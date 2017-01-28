SOCKET_PATH = '/tmp/foo'
STREAM_HOST = '169.254.84.224'
STREAM_PORT = 5001

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
Gst.init(None)

# Build the pipeline
pipeline = Gst.parse_launch("videotestsrc ! glimagesink")

# Start playing
pipeline.set_state(Gst.State.PLAYING)

# Wait until error or EOS
bus = pipeline.get_bus()
msg = bus.timed_pop_filtered(
    Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)

# Free resources
pipeline.set_state(Gst.State.NULL)
