import numpy as np
import cv2
import glob
import pickle


def calibrate(image_paths):
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    pointsY = 6
    pointsX = 5
    objp = np.zeros((pointsX * pointsY, 3), np.float32)
    objp[:, :2] = np.mgrid[0:pointsY, 0:pointsX].T.reshape(-1, 2)

    objpoints = []
    imgpoints = []

    # images = glob.glob(r'C:\Users\Austin\Desktop\roboimage\ImageProcessing2017-python\sampleImages\chess*')
    images = glob.glob(image_paths)
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
            imgpoints.append(corners2)
    reproj_error, camera_matrix, distance_coeffs, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints,
                                                                                     gray.shape[::-1], None, None)
    dict = {"reproj_error": reproj_error, "camera_matrix": camera_matrix, "distance_coeffs": distance_coeffs,
            "rvecs": rvecs, "tvecs": tvecs, "obj_points": objpoints, "img_points": imgpoints,
            "img_size": gray.shape[::-1]}

    return dict


if __name__ == '__main__':
    calibrate(r'C:\Users\Austin\Desktop\roboimage\ImageProcessing2017-python\sampleImages\chess*')