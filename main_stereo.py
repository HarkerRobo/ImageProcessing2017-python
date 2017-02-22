"""
This program serves streams from the camera as well as processing them
and sending results back to clients connected to a server.
"""

import threading
import cv2
import networking
import networking.messages as m
from processing.tapecontours import get_corners_from_image
# Gst = gs.Gst

if __name__ == '__main__':

    # cap_right = cv2.VideoCapture(0)



    # Set up server
    # sock, clis = networking.server.create_socket_and_client_list()
    # handler = networking.create_gst_handler(pipeline, gs.SRC_NAME, 'valve',
    #                                         gs.UDP_NAME)

    # acceptThread = threading.Thread(target=networking.server.AcceptClients,
    #                                 args=[sock, clis, handler])
    # acceptThread.daemon = True # Makes the thread quit with the current thread
    # acceptThread.start()
    cap = cv2.VideoCapture(1)
    while True:


        _, img = cap.read()
        cv2.imshow('original', img)

        img = img[::-1]

        corners = get_corners_from_image(img, show_image=True)
        corns = [[(int(a[0]), int(a[1])) for a in b] for b in corners]

        if cv2.waitKey(1) == ord('q') and len(corns) == 2:
            print("Left: " + str(corns))
            break


    cap = cv2.VideoCapture(1)

    while True:
        cv2.imshow('original', img)

        _, img = cap.read()
        img = img[::-1]

        corners = get_corners_from_image(img, show_image=True)
        # Send the coordinates to the roborio
        corns = [[(int(a[0]), int(a[1])) for a in b] for b in corners]

        if cv2.waitKey(1) == ord('q') and len(corns) == 2:
            print("Right: " + str(corns))
            break
