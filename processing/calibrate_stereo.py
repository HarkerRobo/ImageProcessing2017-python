import numpy as np
import cv2
import glob
import pickle


def calibrate(image_paths_left, image_paths_right):
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    pointsY = 6
    pointsX = 5
    objp = np.zeros((pointsX * pointsY, 3), np.float32)
    objp[:, :2] = np.mgrid[0:pointsY, 0:pointsX].T.reshape(-1, 2)

    objpoints = []
    imgpoints_left = []
    imgpoints_right = []

    # images = glob.glob(r'C:\Users\Austin\Desktop\roboimage\ImageProcessing2017-python\sampleImages\chess*')
    images = glob.glob(image_paths_left)
    gray = None
    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, (pointsY, pointsX), None)

        # If found, add object points, image points
        if ret == True:
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints_left.append(corners2)

    images = glob.glob(image_paths_right)
    gray = None
    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, (pointsY, pointsX), None)

        # If found, add object points, image points
        if ret == True:
            # objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints_right.append(corners2)

    retval, cameraMatrix1, distCoeffs1, cameraMatrix2, distCoeffs2, R, T, E, F = cv2.stereoCalibrate(objpoints,
                                                                                                     imgpoints_left,
                                                                                                     imgpoints_right,
                                                                                                     None, None, None,
                                                                                                     None,
                                                                                                     gray.shape[::-1])

    # reproj_error, camera_matrix, distance_coeffs, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints,
    #                                                                                  gray.shape[::-1], None, None)
    # dict = {"reproj_error": reproj_error, "camera_matrix": camera_matrix, "distance_coeffs": distance_coeffs,
    #         "rvecs": rvecs, "tvecs": tvecs, "obj_points": objpoints, "img_points": imgpoints_left,
    #         "img_size": gray.shape[::-1]}
    dict = {"left": {"camera_matirx": cameraMatrix1, "dist_coeffs": distCoeffs1},
            "right": {"camera_matirx": cameraMatrix1, "dist_coeffs": distCoeffs2},
            "reproj_error": retval, "rot_matrix":R, "trans_matrix":T, "ess_matrix":E, "fund_matrix":F}

    return dict


if __name__ == '__main__':
    calibrate(r'C:\Users\Austin\Desktop\roboimage\ImageProcessing2017-python\sampleImages\chess*')
