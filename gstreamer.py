SOCKET_PATH = '/tmp/foo'
STREAM_HOST = '169.254.84.224'
STREAM_PORT = 5001

import time
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
Gst.init(None)

# Build the pipeline
pipeline = Gst.parse_launch("videotestsrc ! glimagesink")

# Start playing
pipeline.set_state(Gst.State.PLAYING)


# Free resources
#pipeline.set_state(Gst.State.NULL)
time.sleep(4)
