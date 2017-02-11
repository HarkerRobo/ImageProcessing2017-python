import cv2
import numpy as np
import time
from . import tapecontours
import math
from scipy.spatial import distance as dist
import traceback

MATRIX = np.array([[592.24710402, 0., 309.2252711],
                   [0., 587.04231392, 249.43817009],
                   [0., 0., 1.]]).astype('float32')


def extract_points(img):
    rectangle_pair = tapecontours.get_corners_from_image(img, False)
    points = []
    temp_points = []
    for corner in rectangle_pair[0]:
        for corner_point in corner:
            temp_points.append([corner_point[0], corner_point[1]])

    temp_points = order_points(temp_points)

    temp_points_2 = []
    for corner in rectangle_pair[1]:
        for corner_point in corner:
            temp_points_2.append([corner_point[0], corner_point[1]])

    temp_points_2 = order_points(temp_points_2)

    points = np.array(temp_points + temp_points_2).astype('float32')

    return points


def order_points(pts):
    xSorted = sorted(pts, key=lambda pts: pts[0])
    # print(xSorted)
    leftMost = xSorted[:2]
    rightMost = xSorted[2:]
    leftMost = sorted(leftMost, key=lambda leftMost: leftMost[1])
    top_left = leftMost[1]

    def dist(pt1):
        return math.fabs(math.hypot(top_left[0] - pt1[0], top_left[1] - pt1[1]))

    rightMost = sorted(rightMost, key=dist)
    final = leftMost + rightMost
    return final





# def transform(img):
#     # object = gearcontours.process_image(cv2.imread("sampleImages/img.png"))
#     # vcts = []
#     # corners2 = gearcontours.process_image(cv2.imread("pic.jpg"))
#
#     object = gearcontours.process_image(cv2.imread("sampleImages/img.png"))
#     vcts = []
#     image = gearcontours.process_image(cv2.imread("pic.jpg"))
#
#     # for corner in object:
#
#     object_points = []
#     for subcorner in object[0]:
#         for subsubcorner in subcorner:
#             object_points.append([subsubcorner[0], subsubcorner[1]])
#     for subcorner in object[1]:
#         for subsubcorner in subcorner:
#             object_points.append([subsubcorner[0], subsubcorner[1]])
#
#     image_points = []
#     for subcorner in image[0]:
#         for subsubcorner in subcorner:
#             image_points.append([subsubcorner[0], subsubcorner[1]])
#     for subcorner in image[1]:
#         for subsubcorner in subcorner:
#             image_points.append([subsubcorner[0], subsubcorner[1]])
#     print(object_points)
#     print(image_points)
#
#     camera_matrix = np.zeros((3, 3))
#     # print(object[0][0])
#     # print(np.array_type(object[0]))
#     try:
#         # object_points = np.array(object_points, np.float32)
#         # image_points = np.array(image_points, np.float32)
#         object_points = np.array(object_points).astype('float32')
#         image_points = np.array(image_points).astype('float32')
#
#         object_points = [object_points]
#         image_points = [image_points]
#         print(object_points)
#         print(image_points)
#         # print(cv2.getPerspectiveTransform(np.array(object_points, np.float32), np.array(left_second, np.float32)))
#         h, _ = cv2.findHomography(np.array(object_points, np.float32), np.array(image_points, np.float32))
#         # cameraMatrix = None
#         # distCoeffs = None
#         rms, camera_matrix, dist_coefs, rvecs, tvecs = cv2.calibrateCamera(objectPoints=object_points,
#                                                                            imagePoints=image_points,
#                                                                            imageSize=img.shape[1::-1],
#                                                                            cameraMatrix=None, distCoeffs=None)
#
#         print(h)
#     except:
#         print(traceback.format_exc())
#
#         # print(matrix)
#
#
#
#         # print(object)
#

def process(img2):
    img1 = cv2.imread("sampleImages/img-center.png")
    src_points = extract_points(img1)
    dst_points = extract_points(img2)

    # retval = cv2.estimateRigidTransform(src_points, dst_points, fullAffine=False)
    # matrix = None
    # matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    retval, mask = cv2.findHomography(src_points, dst_points)
    # print(retval)
    # print(MATRIX)
    time.sleep(1)

    number, rotations, translations, normals = cv2.decomposeHomographyMat(retval, MATRIX)
    print(number)
    for possible_rotation in rotations:
        rot_vector = cv2.Rodrigues(possible_rotation)[0]
        print(list(map(math.degrees, rot_vector)))

    # [print(math.degrees(rotation_val)) for sublist in [cv2.Rodrigues(rotation)[0] for rotation in rotations] for rotation_val in sublist]
    # print(translations)z
    # print(normals)
    # print(output)
    # print(output[0])
    # print(output[1])
    # print(output[2])

    new_src = np.int32(src_points)
    new_dst = np.int32(dst_points)
    # print(src_points)
    # print(dst_points)
    essentialMatrix, mask = cv2.findFundamentalMat(new_src, new_dst, cv2.FM_LMEDS)
    # print(essentialMatrix)
    # print("\n"*20)
    # pose = cv2.recoverPose(essentialMatrix, src_points, dst_points, MATRIX)
    R1, R2, t = cv2.decomposeEssentialMat(essentialMatrix)  # for thing in pose:

    vector1 = cv2.Rodrigues(R1)[0]
    vector2 = cv2.Rodrigues(R2)[0]
    pos1 = [math.degrees(item) for sublist in vector1.tolist() for item in sublist]
    pos2 = [math.degrees(item) for sublist in vector2.tolist() for item in sublist]
    # print(vector2.tolist())

    print(pos1)
    print(pos2)
    #
    # print(t)
    # print("Done")


if __name__ == '__main__':
    # transform(cv2.imread("sampleImages/img.png"))
    # img1 = cv2.imread("sampleImages/img.png")
    img2 = cv2.imread("sampleImages/img-top.png")
    cv2.waitKey(0)
    process(img2)