import cv2
import numpy as np
import time
from . import tapecontours
import math
import pickle
from . import calibrate_camera
import logging

CAMERA_MATRIX = np.array([[592.24710402, 0., 309.2252711],
                          [0., 587.04231392, 249.43817009],
                          [0., 0., 1.]]).astype('float32')


camera_dist = 0

# left_dict = calibrate_camera.calibrate(
#     r'processing/left_images/*', r"processing/calibration.pickle.left")
# right_dict = calibrate_camera.calibrate(
#     r'processing/right_images/*', r"processing/calibration.pickle.right")
#
# reproj_error, camera_matrix_left, dist_coeffs_left, camera_matrix_right, dist_coeffs_right, R, T, E, F = cv2.stereoCalibrate(
#     objectPoints=left_dict["obj_points"], imagePoints1=left_dict["img_points"],
#     imagePoints2=right_dict["img_points"], cameraMatrix1=None, distCoeffs1=None, cameraMatrix2=None,
#     distCoeffs2=None, imageSize=left_dict["img_size"])
#
# dict = {"left": {"camera_matirx": cameraMatrix1, "dist_coeffs": distCoeffs1},
#         "right": {"camera_matirx": cameraMatrix1, "dist_coeffs": distCoeffs2},
#         "reproj_error": retval, "rot_matrix": R, "trans_matrix": T, "ess_matrix": E, "fund_matrix": F}
with open("processing/calibration.pickle", "rb") as p:
    calib_dict = pickle.load(p)


def process(left_img, right_img):
    # image




    # reproj_error, camera_matrix,  distance_coeffs, rvecs, tvecs, obj_points, img_points, img_size

    # cv2.stereoCalibrate(objectPoints=left_dict["objpoints"], imagePoints1=left_dict["img_points"],
    #                     imagePoints2=right_dict["img_points"],
    #                     cameraMatrix1=left_dict["camera_matrix"], distCoeffs1=left_dict["distance_coeffs"],
    #                     cameraMatrix2=right_dict["camera_matrix"],
    #                     distCoeffs2=right_dict["camera_matrix"], imageSize=left_dict["img_size"])

    # reproj_error, camera_matrix_left, dist_coeffs_left, camera_matrix_right, dist_coeffs_right, R, T, E, F = cv2.stereoCalibrate(
    #     objectPoints=left_dict["objpoints"], imagePoints1=left_dict["img_points"],
    #     imagePoints2=right_dict["img_points"], cameraMatrix1=None, distCoeffs1=None, cameraMatrix2=None,
    #     distCoeffs2=None, imageSize=left_dict["img_size"])


    #     R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
    #                         config.camera.left_intrinsics,
    #                         config.camera.left_distortion,
    #                         config.camera.right_intrinsics,
    #                         config.camera.right_distortion,
    # config.camera.size, R, T, alpha=0)
    R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(cameraMatrix1=calib_dict["left"]["camera_matirx"], distCoeffs1=calib_dict["left"]["dist_coeffs"],
                                                     cameraMatrix2=calib_dict["right"]["camera_matirx"], distCoeffs2=calib_dict["right"]["dist_coeffs"],
                                                     imageSize=calib_dict["img_size"], R=calib_dict["rot_matrix"], T=calib_dict["trans_matrix"])

    left_maps = cv2.initUndistortRectifyMap(calib_dict["left"]["camera_matirx"], calib_dict["left"]["dist_coeffs"], R1, P1, (640, 480),
                                            cv2.CV_16SC2)
    right_maps = cv2.initUndistortRectifyMap(calib_dict["right"]["camera_matirx"], calib_dict["right"]["dist_coeffs"], R2, P2, (640, 480),
                                             cv2.CV_16SC2)




    P1 = np.array([[   1.,           0.,          108.48160885,    0.        ],
 [   0.,            1.,          -10.66847563,    0.        ],
 [   0.,            0.,            1.,            0.        ]])
    P2 = np.array([[   1.,            0.,          108.48160885,    8.1559507 ],
 [   0.,            1.,          -10.66847563,    0.        ],
 [   0.,            0.,            1.,            0.        ]])
   # print(P1, P2)


    left_img_remap = cv2.remap(left_img, left_maps[0], left_maps[1], cv2.INTER_LANCZOS4)
    right_img_remap = cv2.remap(right_img, right_maps[0], right_maps[1], cv2.INTER_LANCZOS4)

    cv2.imshow('left', left_img_remap)
    cv2.imshow('right', left_img_remap)



    try:
        corners_left = np.concatenate(tapecontours.get_corners_from_image(left_img, 1))
        corners_right = np.concatenate(tapecontours.get_corners_from_image(right_img, 2))
    except Exception as e:

        print("Corner fail")
        print(e)
        return
    if len(corners_left) != 8 or len(corners_right) != 8:
        #print(corners_left)
        #print(corners_right)
        print("did not werk")
        return

    reconstructed_points = []
    point_pairs = zip(list(corners_left), list(corners_right))
    for point_pair in point_pairs:

        disparity = point_pair[0][0] - point_pair[1][0]
        print("Disparity: {}".format(disparity))
        reconstructed_point = (point_pair[0][0], point_pair[0][1], disparity)
        reconstructed_points.append(reconstructed_point)
        print(reconstructed_point)



        # focal length is in camera matrix (fx)
    # Z = (b * f) / (x1 - x2)
    # b = distance between lens
    # distance = (camera_dist_between_lenses*focal length)/(disparity)


    # z = triangulation_constant / dispartity

if __name__ == '__main__':
    print("Running main from stereo")
    cv2.waitKey(0)
    process(None, None)
