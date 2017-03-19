"""
This program serves streams from the camera as well as processing them
and sending results back to clients connected to a server.
"""

import logging
import logging.config
import threading
import cv2
import numpy as np

from src.processing.stereo import process
# Gst = gs.Gst

if __name__ == '__main__':
    cleft = cv2.VideoCapture(0)
    cright = cv2.VideoCapture(1)


    while True:
        _, ileft = cleft.read()
        _, iright = cright.read()

        ipleft = np.rot90(ileft, 3)
        ipright = np.rot90(iright, 3)

        points = process(ipleft, ipright, True)


        if cv2.waitKey(1) == ord('q'):
            break
