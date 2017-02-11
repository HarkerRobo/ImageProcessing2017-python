import cv2

cap = cv2.VideoCapture(0)
counter = 0
while True:
    _, img = cap.read()
    img = img[::-1]

    cv2.imshow('original', img)
    if cv2.waitKey(1) == ord('t'):
        cv2.imwrite(r"chess_right"+str(counter)+".jpg", img)
        counter += 1
        print(counter)
    if cv2.waitKey(1) == ord('q'):
        break


cap = cv2.VideoCapture(0)

counter = 0
while True:
    _, img = cap.read()
    img = img[::-1]
    cv2.imshow('original', img)
    if cv2.waitKey(1) == ord('t'):
        cv2.imwrite("chess_right"+str(counter)+".jpg", img)
        counter += 1
        print(counter)
    if cv2.waitKey(1) == ord('q'):
        break