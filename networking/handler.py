"""
This module exports a single useful function, create_gst_handler. Its
purpose is to separate the message-handling code from main.py to make it
more readable and to break things up.

create_gst_handler handles 3 types of messages by doing the following:

Error messages: Prints out the error to stdout (because in reality this
code, which happens to not have any tests, is absolutely perfect and the
only code that would not be functioning is the client code, so any error
generated will be absolutely unhelpful)

Start streaming messages: Stops the running GStreamer pipeline if any
and then re-creates it with the specified ISO and shutterspeed options
and streams to the specified host and port

Stop streaming messages: Stops the running GStreamer pipeline if any
"""

from . import messages as m

# Generic handlers
def on_error(message):
    """Handle an error message sent to the socket."""
    print('Got error from socket: {}'.format(message[m.FIELD_ERROR]))

def create_gst_handler(pipeline, src_name=None, valve_name=None,
                       udp_name=None):
    """Create a message handler for the given GStreamer pipeline.

    Besides the required pipeline, which should already be started, this
    function also takes in the names of three elements in the pipeline:

     * A camera source that supports iso and shutter-speed properties
       (the only source the code supports for now is the rpicamsrc),
     * A valve to control the streaming of the video
     * A udpsink (or any sink that has a host and port property) that
       streams the video to a client

    If any one of these names is set to None, or simply not provided,
    then the code will not handle messages that are meant to change
    elements with the name. For example, if you are using a camera that
    does not support settings iso and shutter speed, then not providing
    a src_name will make the code not handle setting the iso and
    shutterspeed of the camera, but will not break anything else.
    """

    def on_stop(_):
        """Handle a message to stop the GStreamer pipeline."""
        if valve_name is not None:
            pipeline.get_by_name(valve_name).set_property('drop', True)

    def on_start(message):
        """Handle a message to start the GStreamer pipeline."""
        if src_name is not None:
            src = pipeline.get_by_name(src_name)
            src.set_property('iso', message[m.FIELD_ISO])
            src.set_property('shutter-speed', message[m.FIELD_SS])

        if udp_name is not None:
            udp = pipeline.get_by_name(udp_name)
            udp.set_property('host', message[m.FIELD_HOST])
            udp.set_property('port', message[m.FIELD_PORT])

        if valve_name is not None:
            pipeline.get_by_name(valve_name).set_property('drop', False)

    handlers = {
        m.TYPE_ERROR: on_error,
        m.TYPE_START_STREAM: on_start,
        m.TYPE_STOP_STREAM: on_stop
    }

    def handle_message(client, message_str):
        """Handle a message sent to the socket.

        This function will be returned by surrounding function.
        """
        print(message_str)
        try:
            message = m.parse_message(message_str)
            handlers[message[m.FIELD_TYPE]](message)
        except ValueError as e:
            msg = m.create_message(m.TYPE_ERROR, {m.FIELD_ERROR: str(e)})
            client.send(msg.encode('utf-8'))

    return handle_message
