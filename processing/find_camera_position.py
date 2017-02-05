import cv2
import numpy as np
import time
from .tapecontours import get_corners_from_image
import traceback

def transform(img):
    # object = gearcontours.process_image(cv2.imread("sampleImages/img.png"))
    # vcts = []
    # corners2 = gearcontours.process_image(cv2.imread("pic.jpg"))

    object = get_corners_from_image(cv2.imread("sampleImages/img.png"),
                                    show_image=False)
    vcts = []
    image = get_corners_from_image(cv2.imread("pic.jpg"), show_image=False)


    # for corner in object:

    object_points = []
    for subcorner in object[0]:
        for subsubcorner in subcorner:
            object_points.append([subsubcorner[0], subsubcorner[1]])

    image_points = []
    for subcorner in image[0]:
        for subsubcorner in subcorner:
            image_points.append([subsubcorner[0], subsubcorner[1]])

    right_first = []
    for subcorner in object[1]:
        for subsubcorner in subcorner:
            object_points.append([subsubcorner[0], subsubcorner[1]])

    right_second = []
    for subcorner in image[1]:
        for subsubcorner in subcorner:
            image_points.append([subsubcorner[0], subsubcorner[1]])
    print(object_points)
    print(image_points)

    camera_matrix = np.zeros((3, 3))
    # print(object[0][0])
    # print(np.array_type(object[0]))
    try:
        # object_points = np.array(object_points, np.float32)
        # image_points = np.array(image_points, np.float32)
        object_points = np.array(object_points).astype('float32')
        image_points = np.array(image_points).astype('float32')

        object_points = [object_points]
        image_points = [image_points]
        print(object_points)
        print(image_points)
        # print(cv2.getPerspectiveTransform(np.array(object_points, np.float32), np.array(left_second, np.float32)))
        h, _ = cv2.findHomography(np.array(object_points, np.float32), np.array(image_points, np.float32))
        # cameraMatrix = None
        # distCoeffs = None
        rms, camera_matrix, dist_coefs, rvecs, tvecs = cv2.calibrateCamera(objectPoints=object_points, imagePoints=image_points, imageSize=img.shape[1::-1], cameraMatrix=None, distCoeffs=None)


        print(h)
    except:
        print(traceback.format_exc())

    # print(matrix)



    # print(object)




if __name__ == '__main__':
    transform(cv2.imread("sampleImages/img.png"))
    cv2.waitKey(0)
    # cv2.findC
