import os
import cv2
import gstreamer as gs
Gst = gs.Gst

try:
    os.remove(gs.SOCKET_PATH)
except FileNotFoundError:
    pass

pipeline = gs.webcam_streaming_pipeline(gs.STREAM_HOST, gs.STREAM_PORT)
pipeline.set_state(Gst.State.PLAYING)

# TODO: Find a better method to wait for playback to start
print(pipeline.get_state(Gst.CLOCK_TIME_NONE)) # Wait for the pipeline to start playing

caps = gs.get_sink_caps(pipeline.get_by_name(gs.SINK_NAME))
cap_string = gs.make_command_line_parsable(caps)

cap = cv2.VideoCapture(gs.webcam_loopback_command(cap_string))

# while True:
#     _, img = cap.read()
#     cv2.imshow('frame', img)
#     if cv2.waitKey(1) == ord('q'):
#         break

import time

while True:
    time.sleep(1)
