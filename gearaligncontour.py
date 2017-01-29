import cv2
import numpy as np
import time
import gearcontours

def transform(img):
    corners = gearcontours.process_image(cv2.imread("sampleImages/img.png"))
    vcts = []
    corners2 = gearcontours.process_image(cv2.imread("pic.jpg"))
    # for corner in corners:

    left_first = []
    for subcorner in corners[0]:
        for subsubcorner in subcorner:
            left_first.append([subsubcorner[0], subsubcorner[1]])

    left_second = []
    for subcorner in corners2[0]:
        for subsubcorner in subcorner:
            left_second.append([subsubcorner[0], subsubcorner[1]])

    right_first = []
    for subcorner in corners[1]:
        for subsubcorner in subcorner:
            left_first.append([subsubcorner[0], subsubcorner[1]])

    right_second = []
    for subcorner in corners2[1]:
        for subsubcorner in subcorner:
            left_second.append([subsubcorner[0], subsubcorner[1]])


    # print(corners[0][0])
    # print(np.array_type(corners[0]))
    try:
        # print(cv2.getPerspectiveTransform(np.array(left_first, np.float32), np.array(left_second, np.float32)))
        h, _ = cv2.findHomography(np.array(left_first, np.float32), np.array(left_second, np.float32))
        print(h)
    except:
        print("Fail")
    # print(matrix)



    # print(corners)




if __name__ == '__main__':
    transform(cv2.imread("sampleImages/img.png"))
    cv2.waitKey(0)
    # cv2.findC