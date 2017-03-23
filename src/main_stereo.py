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
import gstreamer as gs
import networking
import networking.messages as m
from processing.stereo import process
Gst = gs.Gst

if __name__ == '__main__':
    conf = config.configfor('Vision')

    logging.config.dictConfig(conf.logging)
    logger = logging.getLogger(__name__)

    gs.delete_socket('/tmp/foo0')
    gs.delete_socket('/tmp/foo1')

    leftpipeline = gs.pipeline(
        gs.Webcam(device='/dev/video0') +
        gs.Tee(
            't',
            gs.SHMSink(socket_path='/tmp/foo0'),
            gs.H264Video() + gs.TSFile(gs.ts_filename(), False)
        )
    )

    rightpipeline = gs.pipeline(
        gs.Webcam(device='/dev/video1') +
        gs.Tee(
            't',
            gs.SHMSink(socket_path='/tmp/foo1'),
            gs.H264Video() + gs.TSFile(gs.ts_filename(), False)
        )
    )
    leftpipeline.set_state(Gst.State.PLAYING)
    rightpipeline.set_state(Gst.State.PLAYING)

    leftdebuggingThread = gs.MessagePrinter(leftpipeline)
    rightdebuggingThread = gs.MessagePrinter(rightpipeline)
    leftdebuggingThread.start()
    rightdebuggingThread.start()

    # TODO: Find a better method to wait for playback to start
    logger.debug(leftpipeline.get_state(Gst.CLOCK_TIME_NONE))
    logger.debug(rightpipeline.get_state(Gst.CLOCK_TIME_NONE))

    leftcaps = gs.get_sink_caps(leftpipeline.get_by_name(gs.SINK_NAME))
    rightcaps = gs.get_sink_caps(rightpipeline.get_by_name(gs.SINK_NAME))

    cleft = cv2.VideoCapture(gs.SHMSrc(gs.make_command_line_parsable(leftcaps)))
    cright = cv2.VideoCapture(gs.SHMSrc(gs.make_command_line_parsable(rightcaps)))

    leftdebuggingThread.stop()
    rightdebuggingThread.stop()

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
