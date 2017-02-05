"""
For now this serves as a test program to perfect the vision pipeline and
display results. Later we will have a server that communicates this
information.
"""

import threading
import cv2
import gstreamer as gs
import networking
import networking.messages as m
from processing.tapecontours import get_corners_from_image
Gst = gs.Gst

gs.delete_socket()

# Code for using raspivid command below
# process = gs.raspicam_streaming_process()
# cap_string = gs.get_caps_from_process_and_wait(process)
# print(cap_string)

# Code for using gstreamer api is below
pipeline = gs.raspicam_streaming_pipeline()
pipeline.set_state(Gst.State.PLAYING)

# Start debugging the gstreamer pipeline
debuggingThread = gs.MessagePrinter(pipeline)
debuggingThread.start()

# TODO: Find a better method to wait for playback to start
print(pipeline.get_state(Gst.CLOCK_TIME_NONE)) # Wait for pipeline to play

caps = gs.get_sink_caps(pipeline.get_by_name(gs.SINK_NAME))
cap_string = gs.make_command_line_parsable(caps)

cap = cv2.VideoCapture(gs.webcam_loopback_command(cap_string))

# Now that the capture filters have been (hopefully) successfully
# captured, GStreamer doesn't need to be debugged anymore and the thread
# can be stopped.
debuggingThread.stop()

# Set up server
sock, clis = networking.server.create_socket_and_client_list()
handler = networking.create_gst_handler(gs, pipeline)

acceptThread = threading.Thread(target=networking.server.AcceptClients,
                                args=[sock, clis, handler])
acceptThread.daemon = True # Makes the thread quit with the current thread
acceptThread.start()

while True:
    _, img = cap.read()
    cv2.imshow('original', img)
    corners = get_corners_from_image(img, show_image=True)

    # Send the coordinates to the roborio
    corns = [[(int(a[0]), int(a[1])) for a in b] for b in corners]
    message = m.create_message(m.TYPE_RESULTS, {m.FIELD_CORNERS: corns})
    networking.server.broadcast(sock, clis, message)

    if cv2.waitKey(1) == ord('q'):
        sock.close()
        break

# If you are using the raspivid command for streaming video from the
# Rasberry Pi camera, you will need to kill gstreamer manually. I could
# think of any way to kill GStreamer through the process given by
# raspicam_streaming_process, however, so ideally it would be nice to
# use something nicer.
# os.system('killall gst-launch-1.0')
