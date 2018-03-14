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

STREAM = ('uvch264src device=/dev/video{0} name=pipe_src{0} auto_start=true initial-bitrate=1500000 '
           # 'initial-bitrate=3000000 average-bitrate=3000000 peak-bitrate=5000000 '
           # 'rate-control=vbr iframe-period=1000 '
           'pipe_src{0}.vfsrc ! queue ! video/x-raw,format=YUY2,width=320,height=240,framerate=10/1 ! fakesink '
           'pipe_src{0}.vidsrc ! queue ! video/x-h264,width=1280,height=720,framerate=15/1 '
        )

OUT = 'rtpmp2tpay pt=96 ! udpsink name={udp_name} host={host} port={port} async=false'.format(**gs.DEFAULTS)

if __name__ == '__main__':
    conf0 = config.configfor('Driver')
    conf1 = config.configfor('Gear')

    logging.config.dictConfig(conf0.logging)
    logger = logging.getLogger(__name__)

    pipeline = gs.pipeline(
        # str(gs.PipelinePart('mpegtsmux name=mux') + gs.Valve('valve') + gs.PipelinePart(OUT))
        # + ' ' + STREAM.format(0) + '! mux.sink_0 ' + STREAM.format(1) + '! mux.sink_1'
        # gs.PipelinePart('v4l2src device=/dev/video0 name=pipe_src ! video/x-h264,width=1280,height=720,framerate=15/1,profile=baseline') + gs.H264Stream(port=5002) # Default to port 5002
        str(gs.PipelinePart(STREAM.format(0)) + gs.Valve('valve0') + gs.H264Stream(port=5030, udp_name='udpsink0')) + ' ' +
        str(gs.PipelinePart(STREAM.format(1)) + gs.Valve('valve1') + gs.H264Stream(port=5031, udp_name='udpsink1'))
    )

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

    def setup_server(i, conf):
        # Set up server
        sock, clis = networking.server.create_socket_and_client_list(port=conf.controlport)
        handler = networking.create_gst_handler(pipeline, None, 'valve'+i, 'udpsink'+i)

        acceptThread = threading.Thread(target=networking.server.AcceptClients,
                                        args=[sock, clis, handler])
        acceptThread.daemon = True # Makes the thread quit with the current thread
        acceptThread.start()
        return sock

    sock0 = setup_server('0', conf0)
    sock1 = setup_server('1', conf1)

    logging.info('Streaming... Press Ctrl-C to quit.')
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        sock0.close()
        sock1.close()
