import numpy as np
import cv2
import glob
import pickle

def calibrate(image_paths, calibration_file):
    # try:
    #     with open(calibration_file, 'rb') as f:
    #         return pickle.load(f)
    # except:
        # termination criteria
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        pointsY = 9
        pointsX = 9
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
            crit = (cv2.CALIB_CB_ADAPTIVE_THRESH+cv2.CALIB_CB_NORMALIZE_IMAGE)
            ret, corners = cv2.findChessboardCorners(img, (pointsY, pointsX), flags=crit)

            # If found, add object points, image points
            print(ret)

            if ret == True:

                objpoints.append(objp)

                cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                imgpoints.append(corners)

                # Draw and display the corners
                # cv2.drawChessboardCorners(img, (7, 6), corners, ret)
                # cv2.drawChessboardCorners(img, (7, 6), corners2, ret)
                # cv2.imshow('img', img)
                # cv2.waitKey(500)
                # print(imgpoints)
                # print(objpoints)

        print(imgpoints)
        print(objpoints)
        reproj_error, camera_matrix, distance_coeffs, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints,
                                                                                        gray.shape[::-1], None, None)
        d = {"reproj_error": reproj_error, "camera_matrix": camera_matrix, "distance_coeffs": distance_coeffs,
                "rvecs": rvecs, "tvecs": tvecs, "obj_points": objpoints, "img_points": imgpoints,
                "img_size": gray.shape[::-1]}

        with open(calibration_file, 'wb') as f:
            pickle.dump(d, f)

        return d


if __name__ == '__main__':
    calibrate(r'C:\Users\Austin\Desktop\roboimage\ImageProcessing2017-python\processing\right_images\*', 'calibration.pickle.right')
