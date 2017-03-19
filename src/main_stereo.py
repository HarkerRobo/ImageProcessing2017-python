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
from processing.stereo import process
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

        points = process(ipleft, ipright, False)
        message = m.create_message(m.TYPE_RESULTS, {m.FIELD_CORNERS: points})
        networking.server.broadcast(sock, clis, message)

        if cv2.waitKey(1) == ord('q'):
            sock.close()
            break
