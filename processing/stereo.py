import cv2
import numpy as np
import time
from . import tapecontours
import math
from . import calibrate_camera

CAMERA_MATRIX = np.array([[592.24710402, 0., 309.2252711],
                          [0., 587.04231392, 249.43817009],
                          [0., 0., 1.]]).astype('float32')


camera_dist = 0

def process(left_img, right_img):
    # image

    # ret, mtx, dist, rvecs, tvecs
    left_dict = calibrate_camera.calibrate(
        r'chess_left*')
    right_dict = calibrate_camera.calibrate(
        r'chess_right*')

    corners_left = np.concatenate(tapecontours.get_corners_from_image(left_img))
    corners_right = np.concatenate(tapecontours.get_corners_from_image(right_img))


    # reproj_error, camera_matrix,  distance_coeffs, rvecs, tvecs, obj_points, img_points, img_size

    # cv2.stereoCalibrate(objectPoints=left_dict["objpoints"], imagePoints1=left_dict["img_points"],
    #                     imagePoints2=right_dict["img_points"],
    #                     cameraMatrix1=left_dict["camera_matrix"], distCoeffs1=left_dict["distance_coeffs"],
    #                     cameraMatrix2=right_dict["camera_matrix"],
    #                     distCoeffs2=right_dict["camera_matrix"], imageSize=left_dict["img_size"])

    reproj_error, camera_matrix_left, dist_coeffs_left, camera_matrix_right, dist_coeffs_right, R, T, E, F = cv2.stereoCalibrate(
        objectPoints=left_dict["objpoints"], imagePoints1=left_dict["img_points"],
        imagePoints2=right_dict["img_points"], cameraMatrix1=None, distCoeffs1=None, cameraMatrix2=None,
        distCoeffs2=None, imageSize=left_dict["img_size"])
    #     R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
    #                         config.camera.left_intrinsics,
    #                         config.camera.left_distortion,
    #                         config.camera.right_intrinsics,
    #                         config.camera.right_distortion,
    # config.camera.size, R, T, alpha=0)
    R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(cameraMatrix1=camera_matrix_left, distCoeffs1=dist_coeffs_right,
                                                      cameraMatrix2=camera_matrix_right, distCoeffs2=dist_coeffs_right,
                                                      imageSize=left_dict["img_size"], R=R, T=T)
    left_maps = cv2.initUndistortRectifyMap(camera_matrix_left, dist_coeffs_left, R1, P1, left_dict["img_size"],
                                            cv2.CV_16SC2)
    right_maps = cv2.initUndistortRectifyMap(camera_matrix_right, dist_coeffs_right, R2, P2, left_dict["img_size"],
                                             cv2.CV_16SC2)
    #
    # left_img_remap = cv2.remap(left_img, left_maps[0], left_maps[1], cv2.INTER_LANCZOS4)
    # right_img_remap = cv2.remap(right_img, right_maps[0], right_maps[1], cv2.INTER_LANCZOS4)

    # corners_left = [[(402, 434), (402, 327), (448, 327), (448, 434)], [(242, 421), (242, 324), (290, 324), (290, 421)]]
    #
    #
    # corners_right = [[(508, 430), (508, 324), (552, 324), (552, 430)], [(342, 427), (342, 326), (384, 326), (384, 427)]]
    # corners_left= np.asarray(corners_left, dtype=np.float32)
    # corners_right= np.asarray(corners_right, dtype=np.float32)


    reconstructed_points = []
    point_pairs = []
    for point_pair in point_pairs:
        disparity = point_pair["left"]["x"] - point_pair["right"]["x"]
        reconstructed_point = (point_pair["left"]["x"], point_pair["left"]["y"], disparity)
        reconstructed_points.append(reconstructed_point)

    mystery = cv2.triangulatePoints(projMatr1=P1, projMatr2=P2, projPoints1=corners_left, projPoints2=corners_right)
    print(mystery)
    # Z = (b * f) / (x1 - x2)
    # b = distance between lens
    # distance = (camera_dist_between_lenses*focal length)/(disparity)


    # z = triangulation_constant / dispartity

if __name__ == '__main__':

    cv2.waitKey(0)
    process(None, None)
