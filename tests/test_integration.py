"""
This file tests that when put all together (well almost all together)
everything works fine. It's the closest thing to downloading the code
onto a Rasbperry Pi and saying "it launches!" and is to be used in the
case that you don't have a Rasbperry Pi but still want to say "it
launches!".
"""

import os
import socket
import sys
import threading
import unittest

import cv2
import numpy as np

# Add the parent directory to the path so other modules can be imported
currentdir = os.path.dirname(os.path.abspath(__file__))
srcdir = os.path.join(os.path.dirname(currentdir), 'src')
sys.path.insert(0, srcdir)

import gstreamer as gs
import networking
import networking.messages as m
from processing.tapecontours import get_corners_from_image
Gst = gs.Gst

class IntegrationTest(unittest.TestCase):
    """
    This class tries to perform what the main*.py files do but also
    checks to make sure that stuff works.
    """

    def setUp(self):
        # First stream a pattern of 7 bars of 100% intensity to a v4l2 device
        self.inpipe = gs.pipeline('videotestsrc pattern=smpte100 ! '
                                  'v4l2sink device=/dev/video0')
        debuggingThread = gs.MessagePrinter(self.inpipe)
        debuggingThread.start()
        self.inpipe.set_state(Gst.State.PLAYING)

        print(self.inpipe.get_state(Gst.CLOCK_TIME_NONE))

        # Then read images from that device and stream them over a udp
        # socket to localhost.
        self.streampipe = gs.pipeline(
            gs.Webcam() + gs.Valve('valve') +
            gs.H264Video(h264encoder='x264enc') + gs.H264Stream()
        )
        self.streampipe.set_state(Gst.State.PLAYING)

        # TODO: Find a better method to wait for playback to start
        self.streampipe.get_state(Gst.CLOCK_TIME_NONE)

        debuggingThread.stop()

        res = networking.server.create_socket_and_client_list(host='localhost',
                                                              port=0)
        self.sock, self.clis = res
        handler = networking.create_gst_handler(self.streampipe, None,
                                                'valve', gs.UDP_NAME)

        self.acpter = threading.Thread(target=networking.server.AcceptClients,
                                       args=[self.sock, self.clis, handler])
        self.acpter.daemon = True # Makes the thread quit with the current thread
        self.acpter.start()

        # Now that the server is set up, create a client to connect to it
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(self.sock.getsockname())

        # Initialize some variables that will be populated later
        self.outpipe = None
        self.cap1 = None
        self.cap2 = None

    def test_works(self):
        """Test that the stream can be correctly read."""

        # Test that input stream is working
        self.cap1 = cv2.VideoCapture(0)
        stat, im = self.cap1.read()

        self.assertTrue(stat, 'OpenCV could not read from input stream')
        tlp = im[0][0]
        self.assertTrue(np.array_equal(tlp, [255, 255, 255]),
                        'Top left pixel of image is not white (is {})'.format(tlp))
        trp = im[0][im.shape[1]-1]
        self.assertTrue(np.array_equal(trp, [255, 0, 0]),
                        'Top right pixel of image is not blue (is {})'.format(trp))

        # Start the stream
        self.s.send(m.create_message('start', {
            m.FIELD_HOST: self.sock.getsockname()[0],
            m.FIELD_PORT: self.sock.getsockname()[1],
            m.FIELD_ISO: 0,
            m.FIELD_SS: 0
        }).encode('utf-8'))

        # Then stream it to another v4l2 device
        self.outpipe = gs.pipeline(
            'udpsrc port=5001 ! application/x-rtp, payload=96 ! '
            'rtph264depay ! avdec_h264 ! videoconvert ! '
            'v4l2sink device=/dev/video1'
        )
        self.outpipe.set_state(Gst.State.PLAYING)

        self.cap2 = cv2.VideoCapture(1)
        stat, im = self.cap2.read()

        self.assertTrue(stat, 'OpenCV could not read from input stream')
        # The encoding will make the colors off from what they should
        # be, so white won't be exactly white
        tlp = im[0][0]
        self.assertTrue(np.array_equal(tlp, [235, 235, 235]),
                        'Top left pixel of image is not white (is {})'.format(tlp))
        trp = im[0][im.shape[1]-1]
        self.assertTrue(np.array_equal(trp, [239, 15, 16]),
                        'Top right pixel of image is not blue (is {})'.format(trp))

    def tearDown(self):
        self.inpipe.set_state(Gst.State.NULL)
        self.streampipe.set_state(Gst.State.NULL)
        # TODO: stop self.acpter
        self.s.close()
        self.sock.close()
        self.outpipe.set_state(Gst.State.NULL)
        self.cap1.release()
        self.cap2.release()

if __name__ == '__main__':
    unittest.main()
