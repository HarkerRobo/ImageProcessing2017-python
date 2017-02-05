"""
This program serves a stream of the camera with autofocus turned off.
"""

import threading
import gstreamer as gs
import networking
Gst = gs.Gst

def create_pipeline(**kwargs):
    """Create the pipeline that will be instantiated over messages from
    the driver station.

    The keyword arguments will be iso, shutter, host, and port.
    For more information, see networking.create_gst_handler.
    """
    return gs.pipeline(
        gs.RaspiCam(awb=True, expmode=1) +
        gs.H264Stream(**dict({'port': 5002}, **kwargs)) # Default to port 5002
    )

pipeline = create_pipeline()
pipeline.set_state(Gst.State.PLAYING)

# Start debugging the gstreamer pipeline
debuggingThread = gs.MessagePrinter(pipeline)
debuggingThread.start()

# TODO: Find a better method to wait for playback to start
print(pipeline.get_state(Gst.CLOCK_TIME_NONE)) # Wait for pipeline to play

# Now that the pipeline has been (hopefully) successfully started,
# GStreamer doesn't need to be debugged anymore and the thread can be
# stopped.
debuggingThread.stop()

# Set up server
sock, clis = networking.server.create_socket_and_client_list()
handler = networking.create_gst_handler(gs, create_pipeline, pipeline)

acceptThread = threading.Thread(target=networking.server.AcceptClients,
                                args=[sock, clis, handler])
acceptThread.daemon = True # Makes the thread quit with the current thread
acceptThread.start()

input('Streaming... Press enter to quit.')
sock.close()
