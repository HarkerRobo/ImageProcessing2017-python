"""
This file contains utilities for creating gstreamer processes for
streaming camera outputs.
"""

import os
import re
import threading
from subprocess import PIPE, Popen

import gi
from gi.repository import Gst

SOCKET_PATH = '/tmp/foo'
SINK_NAME = 'pipesink'
GSTREAMER_LAUNCH_COMMAND = 'gst-launch-1.0 -v -e '

# Defaults; can be overriden by parameters
STREAM_HOST = '192.168.1.123'
STREAM_PORT = 5001
ISO = 100
SHUTTER_SPEED = 2000

gi.require_version('Gst', '1.0')
Gst.init(None)

def delete_socket():
    """Delete the file that is used for communication for the shared
    memory location."""
    try:
        os.remove(SOCKET_PATH)
    except FileNotFoundError:
        pass

def raspicam_command(iso=ISO, shutter=SHUTTER_SPEED):
    """
    Return the command to generate h.264-encoded video from the
    Raspberry Pi camera and output it to stdout.

    However, for some reason, setting a low shutterspeed makes the
    stream very slow. Therefore, this function is deprecated and using a
    pipeline via the gstreamer api with the raspicam_streaming_pipeline
    is prefered.
    """
    return (
        'raspivid --timeout 0 ' # No timeout
        '--bitrate 2000000 ' # 2 Mbps bitrate (after h.264 encoding)
        '--framerate 15 '
        '--width 640 --height 480 '
        '--ev -1 '
        '--exposure off ' # Turn off auto exposure
        '--ISO {iso} ' # 1200 ISO
        '--shutter {shutter} ' # 2 millisecond shutterspeed
        '-n ' # No preview on HDMI output
        '-o - | ' # Stream to pipe
    ).format(shutter=shutter, iso=iso)

def webcam_streaming_command(host=STREAM_HOST, port=STREAM_PORT):
    """
    Return the Gstreamer pipeline that takes in the vision webcam stream
    and outputs both an h.264-encoded stream and a raw stream to a
    shared memory location.
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
    ).format(host=host, port=port,
             socket_path=SOCKET_PATH, sink_name=SINK_NAME)

def webcam_streaming_pipeline(host=STREAM_HOST, port=STREAM_PORT):
    """
    Return the Gstreamer pipeline that takes in the vision webcam stream
    and outputs both an h.264-encoded stream and a raw stream to a
    shared memory location.
    """
    return Gst.parse_launch(webcam_streaming_command(host, port))

def raspicam_streaming_command(host=STREAM_HOST, port=STREAM_PORT,
                               iso=ISO, shutter=SHUTTER_SPEED):
    """
    Create the Gstreamer pipeline that takes in the Raspberry pi camera
    stream and outputs both an h.264-encoded stream and a raw stream to
    a shared memory location.
    """
    return (
        # Take in stream from wraspberry pi camera
        'rpicamsrc preview=false exposure-mode=0 '
        'iso={iso} shutter-speed={shutter} ! '
        'video/x-raw, format=I420, width=640, height=320, framerate=15/1 ! '
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
    ).format(host=host, port=port, socket_path=SOCKET_PATH,
             sink_name=SINK_NAME, iso=iso, shutter=shutter)

def raspicam_streaming_pipeline(host=STREAM_HOST, port=STREAM_PORT,
                                iso=ISO, shutter=SHUTTER_SPEED):
    """
    Create the Gstreamer pipeline that takes in the Raspberry Pi camera
    stream and outputs both an h.264-encoded stream and a raw stream to
    a shared memory location.
    """
    return Gst.parse_launch(
        raspicam_streaming_command(host, port, iso, shutter))

def raspicam_streaming_process(host=STREAM_HOST, port=STREAM_PORT,
                               iso=ISO, shutter=SHUTTER_SPEED):
    """
    Create a subprocess to stream the raspberry pi camera, outputting
    the same streams as the webcam.

    As raspicam_command is deprecated, this function has no other use
    and is also deprecated in favor of raspicam_streaming_pipeline.
    """
    command = (
        raspicam_command(iso, shutter) + GSTREAMER_LAUNCH_COMMAND +
        'rpicamsrc'
        # Get stream from raspivid process
        'fdsrc ! h264parse ! '
        # Copy the stream to two different outputs
        'tee name=t ! queue ! '
        # Convert to rtp packets
        'rtph264pay pt=96 config-interval=5 ! '
        # Stream over udp
        'udpsink host={host} port={port} '
        # Use other output
        't. ! queue ! '
        # Decode h.264
        'omxh264dec ! '
        # Put output in a shared memory location
        'shmsink name={sink_name} socket-path={socket_path} '
        'sync=true wait-for-connection=false shm-size=10000000'
    ).format(host=host, port=port,
             socket_path=SOCKET_PATH, sink_name=SINK_NAME)

    return Popen(command, shell=True, stdout=PIPE)

def get_caps_from_process_and_wait(proc):
    """
    Gets the capture filters from the given process and waits for the
    pipeline to play.

    As raspicam_streaming_process is deprecated in favor of
    raspicam_streaming_pipeline, this function is also deprecated in
    favor of using Gst.Pipeline.get_by_name and get_sink_caps to find
    the caps for the pipeline returned by raspicam_streaming_process.
    """
    caps = None
    while True:
        line = proc.stdout.readline().decode('utf-8').strip()
        # Messages about caps will contain pipeline0 since that is the name of
        # the pipeline. To be less verbose, these messages are not printed.
        if 'pipeline0' not in line:
            print(line)
        if line == '':
            # This happens when the process is done printing out stuff. The
            # program returns here as to not enter an infinite loop
            return
        if line.strip() == 'Setting pipeline to PLAYING ...':
            return caps

        try:
            find_str = SINK_NAME + '.GstPad:sink: caps = '
            raw_caps = (line[line.index(find_str)+len(find_str):]
                        .strip('"') # Remove surrounding quotes if any
                        .replace('\\', '')) # Remove backslashes that occor on
                                            # linux environments
            caps = re.sub(r'=\(.*?\)', '=', raw_caps)
        except ValueError:
            pass

def webcam_loopback_command(caps):
    """
    Return the command used by opencv to parse the raw video from the
    shared memory location, given capture filters.

    These capture filters are needed as opencv needs to know how to
    parse what is at the memory location (e.g. width and height).
    """
    return (
        'shmsrc socket-path={socket_path} ! '
        '{caps} ! videoconvert ! appsink'
    ).format(socket_path=SOCKET_PATH, caps=caps)

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
        print('Error received from element {}: {}'.format(element, err))
        print('Debugging information: {}'.format(debug))

    elif message.type == Gst.MessageType.EOS:
        print('End-Of-Stream reached.')

    elif message.type == Gst.MessageType.STATE_CHANGED:
        if isinstance(message.src, Gst.Pipeline):
            old_state, new_state, _ = message.parse_state_changed()
            old = old_state.value_nick
            new = new_state.value_nick
            print('Pipeline state changed from {} to {}'.format(old, new))

    else:
        m_type = message.type
        print('Unexpected message of type {} received.'.format(m_type))

class MessagePrinter(threading.Thread):
    """Thread that coninously queries the pipeline's bus for messages,
    printing them to stdout.
    """
    MESSAGE_TYPES = (Gst.MessageType.STATE_CHANGED | Gst.MessageType.ERROR |
                     Gst.MessageType.EOS)

    def __init__(self, pipeline):
        threading.Thread.__init__(self)
        self._stop = threading.Event()
        self.pipeline = pipeline

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
