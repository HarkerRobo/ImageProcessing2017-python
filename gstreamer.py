SOCKET_PATH = '/tmp/foo'
STREAM_HOST = '169.254.84.224'
STREAM_PORT = 5001

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

Gst.init()

Gst.Pipeline.new("autovideosrc ! aasink")
