"""
This program serves a stream of the camera with autofocus turned off.
"""
import logging
import threading
import time
import config
import gstreamer as gs
import networking
Gst = gs.Gst

if __name__ == '__main__':
    conf = config.configfor('Driver')
    logging.config.dictConfig(conf.logging)
    logger = logging.getLogger(__name__)


    pipeline = gs.pipeline(
        gs.H264RaspiCam(**conf.params) + gs.Valve('valve') +
        gs.H264Stream(port=5002) # Default to port 5002
    )
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
    sock, clis = networking.server.create_socket_and_client_list(port=conf.controlport)
    handler = networking.create_gst_handler(pipeline, None, 'valve',
                                            gs.UDP_NAME)

    acceptThread = threading.Thread(target=networking.server.AcceptClients,
                                    args=[sock, clis, handler])
    acceptThread.daemon = True # Makes the thread quit with the current thread
    acceptThread.start()

    print('Streaming... Press Ctrl-C to quit.')
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()
