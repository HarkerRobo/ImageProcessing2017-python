"""
This program serves streams from the camera as well as processing them
and sending results back to clients connected to a server.
"""

import logging
import logging.config
import threading
import cv2
import numpy as np
import config
import networking
import networking.messages as m
from processing.tapecontours import get_corners_from_image
# Gst = gs.Gst

if __name__ == '__main__':
    conf = config.configfor('Vision')
    cleft = cv2.VideoCapture(0)
    cright = cv2.VideoCapture(1)

    logging.config.dictConfig(conf.logging)
    logger = logging.getLogger(__name__)



    # Set up server
    sock, clis = networking.server.create_socket_and_client_list(port=conf.controlport)
    handler = networking.create_gst_handler(None, None, None, None)

    acceptThread = threading.Thread(target=networking.server.AcceptClients,
                                    args=[sock, clis, handler])
    acceptThread.daemon = True # Makes the thread quit with the current thread
    acceptThread.start()

    while True:
        _, ileft = cleft.read()
        _, iright = cright.read()

        ipleft = np.rot90(ileft, 3)
        ipright = np.rot90(iright, 3)

        corners_left = np.concatenate(get_corners_from_image(ipleft, 1))
        corners_right = np.concatenate(get_corners_from_image(ipright, 2))

        if corners_left.shape[9] == 2 and corners_right.shape[0] == 2:
            left_center = np.sum(corners_left, axis=0) / 8
            right_center = np.sum(corners_right, axis=0) / 8

            center = (left_center + right_center) / 2
            xdisp = int(round(center - 240))

            message = m.create_message(m.TYPE_SIMPLERESULTS, {m.FIELD_XDISP: xdisp})
            networking.server.broadcast(sock, clis, message)

        if cv2.waitKey(1) == ord('q'):
            sock.close()
            break
