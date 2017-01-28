SOCKET_PATH = '/tmp/foo'
STREAM_HOST = '169.254.84.224'
STREAM_PORT = 5001

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

Gst.init()

pipeline = Gst.Pipeline.new("autovideosrc ! glimagesink")
pipeline.set_state(Gst.STATE_PLAYING)
