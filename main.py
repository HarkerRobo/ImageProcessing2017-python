"""
This program serves streams from the camera as well as processing them
and sending results back to clients connected to a server.
"""

import threading
import cv2
import numpy as np
import gstreamer as gs
import networking
import networking.messages as m
from processing.tapecontours import get_corners_from_image
Gst = gs.Gst

if __name__ == '__main__':
    gs.delete_socket()

    pipeline = gs.pipeline(
        gs.RaspiCam() +
        gs.Tee('t',
               gs.Valve('valve') + gs.H264Stream(),
               gs.SHMSink())
    )

    pipeline.set_state(Gst.State.PLAYING)

    # Start debugging the gstreamer pipeline
    debuggingThread = gs.MessagePrinter(pipeline)
    debuggingThread.start()

    # TODO: Find a better method to wait for playback to start
    print(pipeline.get_state(Gst.CLOCK_TIME_NONE)) # Wait for pipeline to play

    caps = gs.get_sink_caps(pipeline.get_by_name(gs.SINK_NAME))
    cap_string = gs.make_command_line_parsable(caps)

    cap = cv2.VideoCapture(gs.SHMSrc(cap_string))

    # Now that the capture filters have been (hopefully) successfully
    # captured, GStreamer doesn't need to be debugged anymore and the thread
    # can be stopped.
    debuggingThread.stop()

    # Set up server
    sock, clis = networking.server.create_socket_and_client_list()
    handler = networking.create_gst_handler(pipeline, gs.SRC_NAME, 'valve',
                                            gs.UDP_NAME)

<<<<<<< Updated upstream
    acceptThread = threading.Thread(target=networking.server.AcceptClients,
                                    args=[sock, clis, handler])
    acceptThread.daemon = True # Makes the thread quit with the current thread
    acceptThread.start()

    while True:
        _, img = cap.read()
        cv2.imshow('original', img)
        corners = get_corners_from_image(img, show_image=True)
=======
acceptThread = threading.Thread(target=networking.server.AcceptClients,
                                args=[sock, clis, handler])
acceptThread.daemon = True
acceptThread.start()

while True:
    _, img = cap.read()
    cv2.imshow('original', img)
    corners = get_corners_from_image(img, show_image=True)

    # Send the coordinates to the roborio
    corns = np.array(corners).tolist()
    message = m.create_message(m.TYPE_RESULTS, {m.FIELD_CORNERS: corns})
    networking.server.broadcast(sock, clis, message)

    if cv2.waitKey(1) == ord('q'):
        sock.close()
        break
>>>>>>> Stashed changes

        # Send the coordinates to the roborio
        corns = [[(int(a[0]), int(a[1])) for a in b] for b in corners]
        message = m.create_message(m.TYPE_RESULTS, {m.FIELD_CORNERS: corns})
        networking.server.broadcast(sock, clis, message)

        if cv2.waitKey(1) == ord('q'):
            sock.close()
            break
