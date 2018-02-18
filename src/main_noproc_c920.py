"""
This program serves a stream of the camera with autofocus turned off.
"""
import logging
import logging.config
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
        gs.PipelinePart('v4l2src device=/dev/video0 name=pipe_src ! video/x-h264,width=1280,height=720,framerate=15/1,profile=baseline') + gs.H264Stream(port=5002) # Default to port 5002
    )

    # Alternative:
    # gst-launch-1.0 -v -e uvch264src device=/dev/video0 name=pipe_src auto_start=true pipe_src.vidsrc ! queue ! video/x-h264,width=1280,height=720,framerate=30/1 ! h264parse ! rtph264pay pt=96 config-interval=5 ! udpsink name=udpsink0 host=192.168.6.168 port=5805 async=false pipe_src.vfsrc ! queue! fakesink

    pipeline.set_state(Gst.State.PLAYING)

    # Start debugging the gstreamer pipeline
    debuggingThread = gs.MessagePrinter(pipeline)
    debuggingThread.start()

    # TODO: Find a better method to wait for playback to start
    logging.debug(pipeline.get_state(Gst.CLOCK_TIME_NONE)) # Wait for pipeline to play

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

    logging.info('Streaming... Press Ctrl-C to quit.')
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()
