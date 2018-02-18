"""
Experiments from off-season
"""

import logging
import time
import threading

import cv2
import numpy as np

from processing.videocapture import VideoCapture
import gstreamer as gs
import networking
from networking import messages as m
Gst = gs.Gst

LOW_GREEN = np.array([60, 100, 10])
UPPER_GREEN = np.array([100, 255, 255])
KERNEL = np.ones((2, 2), np.uint8)
KERNEL2 = np.ones((3, 3), np.uint8)

def get_mask(img):
    """Return a mask were the green parts of the image are white and the
    non-green parts are black.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOW_GREEN, UPPER_GREEN)
    return mask

def valid_cnt(cnt):
    """Return True if the contour is possibly a valid target."""
    area = cv2.contourArea(cnt)
    if not area > 100:
        return False

    hullarea = cv2.contourArea(cv2.convexHull(cnt))
    if not area/hullarea > 0.8:
        return False

    rotrect = cv2.minAreaRect(cnt)
    w, h = rotrect[1]
    if not min(w, h) / max(w, h) > 0.5:
        return False

    rotrectarea = w * h
    if not area/rotrectarea > 0.7:
        return False

    return True

def cnt_score(cnt):
    """Return the score of several properties of the given contours, on a scale of 0 to 1."""
    score = 0
    area = cv2.contourArea(cnt)

    hull = cv2.convexHull(cnt)
    hullarea = cv2.contourArea(hull)
    hullscore = area/hullarea

    rotrect = cv2.minAreaRect(cnt)
    w, h = rotrect[1]
    arscore = np.sqrt(min(w, h) / max(w, h))

    rotrectarea = w * h
    rotrectscore = area / rotrectarea

    perimeter = cv2.arcLength(hull, True)
    squaredness = 1 - abs(16*hullarea / perimeter**2 - 1)**1.5
    squarescore = squaredness

    areascore = 2 / (1 + 1.1**(-area/100)) - 1

    return {
        'hull': hullscore,
        'ar': arscore,
        'rotrect': rotrectscore,
        'square': squarescore,
        'area': areascore
    }

def weighted_score(cnt):
    """Return a total score from 0 to 1 on how likely a contour is to be a target."""
    s = cnt_score(cnt)
    return 0.2*s['hull'] + 0.05*s['ar'] + 0.2*s['rotrect'] + 0.35*s['square'] + 0.2*s['area']

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
logger.addHandler(sh)

gs.delete_socket()

pipeline = gs.pipeline(
    gs.RaspiCam(vflip=True, hFlip=True, expmode=6, framerate=30, ec=10,
                awb=False, ar=1, ab=2.5, width=1280, height=960) +
    gs.PipelinePart('videoconvert') +
    gs.Tee('t',
           gs.Valve('valve') + gs.H264Video() + gs.H264Stream(),
           gs.PipelinePart('videoscale ! video/x-raw, width=640, height=480') + gs.SHMSink())
)

# Start debugging the gstreamer pipeline
debuggingThread = gs.MessagePrinter(pipeline)
debuggingThread.start()

pipeline.set_state(Gst.State.PLAYING)

logger.debug(pipeline.get_state(Gst.CLOCK_TIME_NONE))

caps = gs.get_sink_caps(pipeline.get_by_name(gs.SINK_NAME))
cap_string = gs.make_command_line_parsable(caps)

vc = VideoCapture(gs.SHMSrc(cap_string))
vc.setDaemon(True)
vc.start()

# Now that the capture filters have been (hopefully) successfully
# captured, GStreamer doesn't need to be debugged anymore and the thread
# can be stopped.
debuggingThread.stop()

sock, clis = networking.server.create_socket_and_client_list(port=6000)
handler = networking.create_gst_handler(pipeline, gs.SRC_NAME, 'valve',
                                        gs.UDP_NAME)

acceptThread = threading.Thread(target=networking.server.AcceptClients,
                                args=[sock, clis, handler])
acceptThread.daemon = True # Makes the thread quit with the current thread
acceptThread.start()

frames = 0
start = time.time()

while True:
    status, img = vc.read()
    if status:
        mask = get_mask(img)
        closing = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, KERNEL, iterations=2)
        opening = cv2.morphologyEx(closing, cv2.MORPH_OPEN, KERNEL2, iterations=4)

        _, cnt, _ = cv2.findContours(opening, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # cv2.drawContours(img, cnt, -1, (0, 0, 255), 2)
        valid = list(filter(valid_cnt, cnt))
        # cv2.drawContours(img, valid, -1, (0, 255, 255), 2)

        bestcnt = max(valid, key=weighted_score) if len(valid) > 0 else None
        if bestcnt is not None:
            # cv2.drawContours(img, [bestcnt], -1, (0, 255, 0), 2)
            bbx, bby, bbw, bbh = cv2.boundingRect(bestcnt)
            roi = mask[bby:bby+bbh, bbx:bbx+bbw]

            roi2 = cv2.morphologyEx(roi, cv2.MORPH_OPEN, KERNEL2, iterations=6)
            bbbx, bbby, bbbw, bbbh = cv2.boundingRect(roi2)
            # cv2.rectangle(img, (bbx+bbbx, bby+bbby), (bbx+bbbx+bbbw, bby+bbby+bbbh), (255, 0, 0), 2)
            corns = (bbx+bbbx, bby+bbby, bbw, bbh)

            #XXX: Only sending valid contours to first client won't always work
            smessage = m.create_message(m.TYPE_RESULTS, {m.FIELD_CORNERS: corns})
            networking.server.broadcast(sock, clis[2:], smessage)

            lmessage = m.create_message(m.TYPE_RESULTS, {m.FIELD_CORNERS: corns, 'valid': [x.tolist() for x in valid]})
            networking.server.broadcast(sock, clis[:2], lmessage)

        # for cnt in valid:
        #     M = cv2.moments(cnt)
        #     cx = int(M['m10'] / M['m00'])
        #     cy = int(M['m01'] / M['m00'])
        #     y = 0
        #     for k, v in cnt_score(cnt).items():
        #         text = '{}: {:.2f}'.format(k, v)
        #         cv2.putText(img, text, (cx+60, cy+y-25), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        #         y += 15

        # cv2.imshow('image', img)
        # cv2.imshow('frame', mask)
        frames += 1
        print('FPS: {}'.format(frames / (time.time()-start)))
    else:
        print('No image')
    if cv2.waitKey(1) == ord('q'):
        break
