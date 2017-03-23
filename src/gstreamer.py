"""
This file contains utilities for creating gstreamer pipelines for
streaming camera outputs.
"""

from datetime import datetime
import logging
import os
import threading

import gi

SOCKET_PATH = '/tmp/foo'
SINK_NAME = 'pipesink'
SRC_NAME = 'pipesrc'
UDP_NAME = 'udpsink0'
GSTREAMER_LAUNCH_COMMAND = 'gst-launch-1.0 -v -e '

# Set of defaults used for all methods; adjustable via parameters
DEFAULTS = {
    'width': 640,
    'height': 480,
    'bitrate': 1000000, # 1 Mbps (after h.264 encoding)
    'quant_param': 0, # Quantisation parameter - higher is lower quality, 0=off
    'framerate': 15,
    'device': '/dev/video0',
    'host': '127.0.0.1',
    'port': 5001,
    'iso': 100,
    'shutter': 2000,
    'awb': False, # Auto white balance
    'ab': 2.5, # Blue component of white balance
    'ar': 1, # Red component of white balance
    'expmode': 6, # 0 for manual, 1 for auto, 6 for sports
    'sink_name': SINK_NAME,
    'src_name': SRC_NAME,
    'udp_name': UDP_NAME,
    'socket_path': SOCKET_PATH,
    'h264encoder': 'omxh264enc' # Name of GStreamer element to encode h.264
}

logger = logging.getLogger(__name__)

merge_defaults = lambda k: dict(DEFAULTS, **k)

gi.require_version('Gst', '1.0')
from gi.repository import Gst
Gst.init(None)

def delete_socket(socket_path=SOCKET_PATH):
    """Delete the file that is used for communication for the shared
    memory location."""
    try:
        os.remove(socket_path)
    except FileNotFoundError:
        pass

class PipelinePart(str):
    """A class to aid in the construction of GStreamer pipelines.

    It extends str and overides the `__add__` and `__radd__` methods, so
    you can add them together as you would strings. For example:

    >>> PipelinePart('videotestsrc') + PipelinePart('autovideosink')
    'videotestsrc ! autovideosink'
    """

    def __add__(self, part):
        return str(self) + ' ! ' + str(part)

    def __radd__(self, part):
        return str(part) + ' ! ' + str(self)

class Webcam(PipelinePart):
    """
    A GStreamer pipline part that takes in video from a webcam that
    supports v4l2 and outputs raw video.

    The optional keyword arguments taken are as follows: width, height,
    framerate, device
    """
    def __new__(cls, **kwargs):
        return super().__new__(cls, (
            'v4l2src name={src_name} device={device} ! video/x-raw,width={width},'
            'height={height},framerate={framerate}/1'
        ).format(**merge_defaults(kwargs)))

class RaspiCam(PipelinePart):
    """
    A GStreamer pipeline part that takes in video from a Raspberry Pi
    Camera Module and outputs raw video.

    The optional keyword arguments are as follows: iso, shutter, ab, ar,
    width, height, framerate
    """
    def __new__(cls, **kwargs):
        kw = merge_defaults(kwargs)
        if kw['awb']:
            awb_str = ''
        else:
            awb_str = 'awb-mode=off awb-gain-blue={ab} awb-gain-red={ar} '

        if kw['expmode'] == 0:
            exp_str = 'exposure-mode={expmode} iso={iso} shutter-speed={shutter}'
        else:
            exp_str = 'exposure-mode={expmode}'
        return super().__new__(cls, (
            'rpicamsrc name={src_name} preview=false '
            + awb_str
            + exp_str +
            ' ! video/x-raw, format=I420, width={width}, height={height}, '
            'framerate={framerate}/1'
        ).format(**kw))

class H264RaspiCam(PipelinePart):
    """
    A GStreamer pipeline part that takes in video from a Raspberry Pi
    Camera Module and outputs h264 video.

    The optional keyword arguments are as follows: iso, shutter, ab, ar,
    width, height, framerate

    Note that there are some issues using this with lower exposure
    modes. Proceed with caution. However, this does allow for setting a
    constant bitrate.
    """
    def __new__(cls, **kwargs):
        kw = merge_defaults(kwargs)
        if kw['awb']:
            awb_str = ''
        else:
            awb_str = 'awb-mode=off awb-gain-blue={ab} awb-gain-red={ar} '

        if kw['expmode'] == 0:
            exp_str = 'exposure-mode={expmode} iso={iso} shutter-speed={shutter}'
        else:
            exp_str = 'exposure-mode={expmode}'
        return super().__new__(cls, (
            'rpicamsrc name={src_name} preview=false '
            'bitrate={bitrate} quantisation-parameter={quant_param} '
            + awb_str
            + exp_str +
            ' ! video/x-h264, width={width}, height={height}, profile=high, '
            'framerate={framerate}/1'
        ).format(**kw))


class TestSrc(PipelinePart):
    """
    A Gstreamer pipeline part that generates a sample video via
    GStreamer's videotestsrc and outputs raw video.

    The optional keyword arguments are as follows: width, height,
    framerate
    """
    def __new__(cls, **kwargs):
        return super().__new__(cls, (
            'videotestsrc name={src_name} ! video/x-raw,width={width},'
            'height={height},framerate={framerate}/1'
        ).format(**merge_defaults(kwargs)))

class H264Video(PipelinePart):
    """
    A GStreamer pipeline part that takes in raw video and encodes it to
    h.264.
    """
    def __new__(cls, **kwargs):
        return super().__new__(cls, (
            '{h264encoder}'
        ).format(**merge_defaults(kwargs)))

class H264Stream(PipelinePart):
    """
    A GStreamer pipeline part that takes in h.264 video and streams it
    over RTP over UDP to a given host and port.

    The optional keyword arguments are as follows: host, port
    """
    def __new__(cls, **kwargs):
        return super().__new__(cls, (
            'h264parse ! '
            # Convert to rtp packets
            'rtph264pay pt=96 config-interval=5 ! '
            # Stream over udp
            'udpsink name={udp_name} host={host} port={port} async=false'
        ).format(**merge_defaults(kwargs)))

class SHMSink(PipelinePart):
    """
    A GStreamer pipeline part that takes in raw video and dumps it to a
    shared memory location.
    """
    def __new__(cls, **kwargs):
        return super().__new__(cls, (
            'shmsink name={sink_name} socket-path={socket_path} '
            'sync=true wait-for-connection=false shm-size=10000000'
        ).format(**merge_defaults(kwargs)))

class Tee(PipelinePart):
    """
    A Gstreamer pipeline part that takes in data, splits it into
    multiple pads, and assigns each pad to the given pipeline parts so
    that they can run concurrently.

    The example below will launch two windows for the stream

    >>> (PipelinePart('videotestsrc') + Tee('t',
    ... PipelinePart('autovideosink'), PipelinePart('autovideosink')))
    """
    def __new__(cls, name, *parts):
        return super().__new__(cls, (
            'tee name={} ! queue ! '.format(name) +
            ' {}. ! queue ! '.format(name).join(parts)
        ))

class SHMSrc(PipelinePart):
    """
    A GStreamer pipeline part used by OpenCV to parse the raw video from the
    shared memory location, given capture filters.

    These capture filters are needed as opencv needs to know how to
    parse what is at the memory location (e.g. width and height).
    """
    def __new__(cls, caps, **kwargs):
        return super().__new__(cls, (
            'shmsrc socket-path={socket_path} ! '
            '{caps} ! videoconvert ! appsink'
        ).format(**dict(merge_defaults(kwargs), caps=caps)))

class Valve(PipelinePart):
    """
    Represents a valve element for GStreamer.

    This class takes two parameters: a required name for the valve and
    the initial state of the drop property (whether to drop buffers and
    events), which defaults to False.
    """
    def __new__(cls, name, drop=False):
        return super().__new__(cls, (
            'valve name={} drop={}'
        )).format(name, 'true' if drop else 'false')

class TSFile(PipelinePart):
    """
    A GStreamer pipeline part that dumps received video data into an ts
    container.

    This class takes two parameters: a requried filename to dump the
    video into and an optional boolean of whether to append video to the
    video file, which defaults to True.
    """
    def __new__(cls, location, append=True):
        return super().__new__(cls, (
            'mpegtsmux ! filesink location={} append={}'
        )).format(location, 'true' if append else 'false')

def pipeline(part):
    """Return a GStreamer pipeline given a PipelinePart."""
    logger.debug("Pipeline: {}".format(part))
    return Gst.parse_launch(part)

def ts_filename():
    """Return a filename for a ts file based on the current time."""
    return '{:%Y-%m-%d_%H-%M-%S}.ts'.format(datetime.today())

def get_sink_caps(element):
    """
    Return the negotiated capture filters of a given element's sink
    connection (i.e. what is outputted by the element).

    Because these capture filters will be negotiated, this method must
    be used after the pipeline is playing.
    """
    return element.get_static_pad('sink').get_current_caps()

def get_cap_value_by_name(caps, name):
    """
    Return what caps.get_value(name) does, but also handle fractions.
    """
    try:
        return caps.get_value(name)
    except TypeError:
        fraction = caps.get_fraction(name)
        return '{1}/{2}'.format(*fraction)

def make_command_line_parsable(caps):
    """
    A Cap object's toString method returns something very close to what
    this method returns, but the outputted string also contains types in
    parenthesis (e.g. width=(int)320). This method returns that string,
    but without the type and parenthesis.

    One could just use regex to find all ocurrences of characters
    surrounded in paranthesis, but that would run into problems if the
    enclosed strings contained parenthesis.
    """

    struct = caps.get_structure(0)
    out = struct.get_name()

    for i in range(struct.n_fields()):
        cap_name = struct.nth_field_name(i)
        cap_value = get_cap_value_by_name(struct, cap_name)

        out += ', {0}={1}'.format(cap_name, cap_value)

    return out

def print_message(message):
    """Print a message received from a pipeline bus, formatted to be
    descriptive.

    Adapted from examples at
    https://gist.github.com/willpatera/7984486.
    """
    if message.type == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        element = message.src.get_name()
        logger.error('Error received from element {}: {}'.format(element, err))
        logger.error('Debugging information: {}'.format(debug))

    elif message.type == Gst.MessageType.EOS:
        logger.debug('End-Of-Stream reached.')

    elif message.type == Gst.MessageType.STATE_CHANGED:
        if isinstance(message.src, Gst.Pipeline):
            old_state, new_state, _ = message.parse_state_changed()
            old = old_state.value_nick
            new = new_state.value_nick
            logger.debug('Pipeline state changed from {} to {}'.format(old, new))

    else:
        m_type = message.type
        logger.error('Unexpected message of type {} received.'.format(m_type))

class MessagePrinter(threading.Thread):
    """Thread that coninously queries the pipeline's bus for messages,
    printing them to stdout.
    """
    MESSAGE_TYPES = (Gst.MessageType.STATE_CHANGED | Gst.MessageType.ERROR |
                     Gst.MessageType.EOS)

    def __init__(self, pipe):
        threading.Thread.__init__(self)
        self._stop = threading.Event()
        self.pipeline = pipe

    def run(self):
        """Start the thread."""
        bus = self.pipeline.get_bus()
        while not self._stop.isSet():
             # In nanoseconds, so wait 0.1s = 1e5 nanoseconds
            message = bus.timed_pop_filtered(1e5, self.MESSAGE_TYPES)
            if message is not None:
                print_message(message)

    def stop(self):
        """Stop the thread."""
        self._stop.set()

if __name__ == '__main__':
    testPipeline = Gst.parse_launch(
        'autovideosrc ! glimagesink name={0}'.format(SINK_NAME)
    )
    testPipeline.set_state(Gst.State.PLAYING)

    # TODO: Find a better method to wait for playback to start
    testPipeline.get_state(Gst.CLOCK_TIME_NONE) # Wait for pipeline to play

    testCaps = get_sink_caps(testPipeline.get_by_name(SINK_NAME))
    print(make_command_line_parsable(testCaps))
