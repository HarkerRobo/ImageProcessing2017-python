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

def create_gst_handler(gs, initial_pipeline=None):
    """Create a message handler for the given GStreamer pipeline.

    If a pipeline that has been given is not None, then it will be
    stopped on close messages. However, while this method will set the
    pipeline to None when it is stopped, this change will not be
    reflected outside the function, although the pipeline's state will
    be Gst.State.NULL.

    This function also takes in the gs module as it will be outside this
    module.
    """
    pipeline = initial_pipeline # Rename the argument so code is more readable

    def on_stop(_):
        """Handle a message to stop the GStreamer pipeline."""
        nonlocal pipeline
        if pipeline is not None:
            pipeline.set_state(gs.Gst.State.NULL)
            pipeline = None

    def on_start(message):
        """Handle a message to start the GStreamer pipeline."""
        nonlocal pipeline
        on_stop(message) # First kill the pipeline if it is running
        pipeline = gs.pipeline(
            gs.RaspiCam(iso=message[m.FIELD_ISO], shutter=message[m.FIELD_SS])
            + gs.Tee('t', gs.H264Stream(host=message[m.FIELD_HOST],
                                        port=message[m.FIELD_PORT]),
                     gs.SHMSink()))

        pipeline.set_state(gs.Gst.State.PLAYING)

    handlers = {
        m.TYPE_ERROR: on_error,
        m.TYPE_START_STREAM: on_start,
        m.TYPE_STOP_STREAM: on_stop
    }

    def handle_message(client, message_str):
        """Handle a message sent to the socket.

        This function will be returned by surrounding function.
        """
        try:
            message = m.parse_message(message_str)
            handlers[message[m.FIELD_TYPE]](message)
        except ValueError as e:
            msg = m.create_message(m.TYPE_ERROR, {m.FIELD_ERROR: str(e)})
            client.send(msg.encode('utf-8'))

    return handle_message
