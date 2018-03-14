"""
This program serves a stream of the camera with autofocus turned off.
"""
import sys
import logging
import logging.config
import threading
import time
import config
import gstreamer as gs
import networking
Gst = gs.Gst

if __name__ == '__main__':
    camera = 0
    if len(sys.argv) > 1:
        camera = sys.argv[1]

    conf = config.configfor('Gear' if camera == '1' else 'Driver')

    logging.config.dictConfig(conf.logging)
    logger = logging.getLogger(__name__)

    pipeline = gs.pipeline(
        # gs.PipelinePart('v4l2src device=/dev/video0 name=pipe_src ! video/x-h264,width=1280,height=720,framerate=15/1,profile=baseline') + gs.H264Stream(port=5002) # Default to port 5002
        gs.PipelinePart(('uvch264src device=/dev/video{} name=pipe_src auto_start=true initial-bitrate=1500000 '
                        # 'initial-bitrate=3000000 average-bitrate=3000000 peak-bitrate=5000000 '
                        # 'rate-control=vbr iframe-period=1000 '
                        'pipe_src.vfsrc ! queue ! video/x-raw,format=YUY2,width=320,height=240,framerate=10/1 ! fakesink '
                        'pipe_src.vidsrc ! queue ! video/x-h264,width=1280,height=720,framerate=30/1 '
                        ).format(camera)) + gs.Valve('valve') + gs.Tee('tee',
                            gs.H264Stream(port=5002), # Default to port 5002
                            gs.TSFile('/mnt/usb/video/' + gs.ts_filename(), True)
    )

    # Alternative:
    # gst-launch-1.0 -v -e

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
