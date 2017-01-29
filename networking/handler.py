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
        pipeline = gs.raspicam_streaming_pipeline(
            message[m.FIELD_HOST], message[m.FIELD_PORT],
            message[m.FIELD_ISO], message[m.FIELD_SS]
        )
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
