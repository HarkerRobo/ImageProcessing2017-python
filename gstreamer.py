"""
This file contains utilities for creating gstreamer processes for streaming camera outputs.
"""

import re
from subprocess import Popen, PIPE

SOCKET_PATH = '/tmp/foo'
STREAM_HOST = '192.168.1.123'
STREAM_PORT = 5001
SINK_NAME = 'pipesink'
RASPICAM_COMMAND = 'raspivid -t 0 -b 2000000 -fps 15 -w 640 -h 360 -np -o - | '

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
        'shmsink name={sink_name} socket-path={socket_path} '
        'sync=true wait-for-connection=false shm-size=10000000'
    ).format(host=host, port=port, socket_path=SOCKET_PATH, sink_name=SINK_NAME)

def webcam_streaming_pipeline(host, port):
    """
    Creates the Gstreamer pipeline that takes in the vision webcam stream and
    outputs both an h.264-encoded stream and a raw stream to a shared memory
    location.
    """
    return Gst.parse_launch(webcam_streaming_command(host, port))

def raspicam_streaming_process(host, port):
    """
    Creates a subprocess to stream the raspberry pi camera, outputting the same
    streams as the webcam.
    """
    command = RASPICAM_COMMAND + 'gstreamer -v' + webcam_streaming_command(host, port)
    return Popen(command, shell=True, stdout=PIPE)

def get_caps_from_process_and_wait(proc):
    """
    Gets the capture filters from the given process and waits for the pipeline to play
    """
    caps = ''
    while True:
        line = proc.stdout.readline()
        if line == '': return
        if line.strip() == 'Setting pipeline to PLAYING ...': return caps

        try:
            find_str = SINK_NAME + '.GstGhostPad:sink: caps = '
            raw_caps = line[line.index(find_str)+len(find_str):]
            caps = re.sub(r'=\(.*?\)', '=', raw_caps).replace('\\', '')
        except ValueError:
            pass

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
    testPipeline = Gst.parse_launch('autovideosrc ! glimagesink name={0}'.format(SINK_NAME))
    testPipeline.set_state(Gst.State.PLAYING)

    # TODO: Find a better method to wait for playback to start
    testPipeline.get_state(Gst.CLOCK_TIME_NONE) # Wait for the pipeline to start playing

    testCaps = get_sink_caps(testPipeline.get_by_name(SINK_NAME))
    print(make_command_line_parsable(testCaps))
