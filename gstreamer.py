SOCKET_PATH = '/tmp/foo'
STREAM_HOST = '169.254.84.224'
STREAM_PORT = 5001

import time
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
Gst.init(None)

def webcam_streaming_command(host, port):
    """
    Creates the Gstreamer pipeline that takes in the vision webcam stream and
    outputs both an h.264-encoded stream and a raw stream to a shared memory
    location.
    """
    return (
        # Take in stream from webcam
        'v4l2src ! video/x-raw, width=640,height=480 ! '
        # Copy the stream to two different outputs
        'tee name=t ! queue ! '
        # Encode one output to h.264
        'omxh264enc ! h264parse ! '
        # Convert to rtp packets
        'rtph264pay pt=96 config-interval=5 ! '
        # Stream over udp
        'udpsink host={host} port={port} '
        # Use other output
        't. ! queue ! '
        # Put output in a shared memory location
        'shmsink name=pipesink socket-path={socket_path}'
        'sync=true wait-for-connection=false shm-size=10000000'
    ).format(host=host, port=port, socket_path=SOCKET_PATH)

def webcam_streaming_pipeline(host, port):
    """
    Creates the Gstreamer pipeline that takes in the vision webcam stream and
    outputs both an h.264-encoded stream and a raw stream to a shared memory
    location.
    """
    return Gst.parse_launch(webcam_streaming_command(host, port))

def webcam_loopback_command(caps):
    """
    Creates the command used by opencv to parse the raw video from the shared
    memory location, given capture filters.

    These capture filters are needed as opencv needs to know how to parse what
    is at the memory location (e.g. width and height).
    """
    return (
        'shmsrc socket-path={socket_path} ! '
        '{caps} ! videoconvert ! appsink'
    ).format(socket_path=SOCKET_PATH, caps=caps)

def get_sink_caps(element):
    """
    Returns the negotiated capture filters of a given element's sink connection
    (i.e. what is outputted by the element).

    Because these capture filters will be negotiated, this method must be used
    after the pipeline is playing.
    """
    return element.get_static_pad('sink').get_current_caps()

def get_cap_value_by_name(caps, name):
    """
    For some reason getValue(name) works for every data type except
    fractions, so a bit more work needs to be done to get a capture filter by
    its name.
    """
    try:
        return caps.get_value(name)
    except TypeError:
        fraction = caps.get_fraction(name)
        return '{1}/{2}'.format(*fraction)

def make_command_line_parsable(caps):
    """
    A Cap object's toString method returns something very close to what this
    method returns, but the outputted string also contains types in parenthesis
    (e.g. width=(int)320). This method returns that string, but without the type
    and parenthesis.

    One could just use regex to find all ocurrences of \(.*?\), but that would
    run into problems if the enclosed strings contained parenthesis.
    """

    struct = caps.get_structure(0)
    out = struct.get_name()

    for i in range(struct.n_fields()):
        cap_name = struct.nth_field_name(i)
        cap_value = get_cap_value_by_name(struct, cap_name)

        out += ', {0}={1}'.format(cap_name, cap_value)

    return out

if __name__ == '__main__':
    pipeline = Gst.parse_launch('autovideosrc ! glimagesink name=pipesink')
    pipeline.set_state(Gst.State.PLAYING)

    # TODO: Find a better method to wait for playback to start
    pipeline.get_state(Gst.CLOCK_TIME_NONE) # Wait for the pipeline to start playing

    caps = get_sink_caps(pipeline.get_by_name('pipesink'))
    print(make_command_line_parsable(caps))
