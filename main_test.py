"""
This program serves a test stream that can be used for debugging
networking and streaming.
"""

import logging
import time
import random
import threading
import gstreamer as gs
import networking
import networking.messages as m
Gst = gs.Gst

def randomcorners():
    """Return an array of randomized corners"""
    r = lambda x: random.randint(int(x*0.4), int(x*0.6))
    cx = r(gs.DEFAULTS['width'])
    cy = r(gs.DEFAULTS['height'])

    w = int(gs.DEFAULTS['width'] * random.random() * 0.2)
    h = int(gs.DEFAULTS['height'] * random.random() * 0.2)

    crns = [(cx-w, cy-h), (cx+w, cy-h), (cx+w, cy+h), (cx-w, cy+h)]
    random.shuffle(crns)

    return crns

if __name__ == '__main__':
    conf = config.configfor('Vision')

    logging.config.dictConfig(conf.logging)
    logger = logging.getLogger(__name__)

    pipeline = gs.pipeline(
        gs.TestSrc() + gs.H264Video(h264encoder='x264enc') +
        gs.Tee(
            't',
            gs.Valve('valve') + gs.H264Stream(port=5003, host='localhost'),
            gs.TSFile(gs.ts_filename(), False)
        )
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
    sock, clis = networking.server.create_socket_and_client_list()
    handler = networking.create_gst_handler(pipeline, None, 'valve',
                                            gs.UDP_NAME)

    acceptThread = threading.Thread(target=networking.server.AcceptClients,
                                    args=[sock, clis, handler])
    acceptThread.daemon = True # Makes the thread quit with the current thread
    acceptThread.start()

    print('Streaming... Press Ctrl-C to quit.')
    try:
        while True:
            crns = [randomcorners(), randomcorners()]

            message = m.create_message(m.TYPE_RESULTS, {m.FIELD_CORNERS: crns})
            networking.server.broadcast(sock, clis, message)
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()
