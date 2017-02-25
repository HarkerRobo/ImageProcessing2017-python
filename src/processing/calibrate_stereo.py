import numpy as np
import cv2
import glob
import pickle


def calibrate(image_paths_left, image_paths_right):
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    pointsY = 9
    pointsX = 6
    objp = np.zeros((pointsX * pointsY, 3), np.float32)
    objp[:, :2] = np.mgrid[0:pointsY, 0:pointsX].T.reshape(-1, 2)

    objpoints = []
    imgpoints_left = []
    imgpoints_right = []

    images_left = glob.glob(image_paths_left)
    images_right = glob.glob(image_paths_right)
    img_left = None
    for pair in zip(images_left, images_right):
        # print(pair)
        img_left = cv2.imread(pair[0])
        img_right = cv2.imread(pair[1])

        img_left = cv2.cvtColor(img_left, cv2.COLOR_BGR2GRAY)

        img_right = cv2.cvtColor(img_right, cv2.COLOR_BGR2GRAY)

        ret_left, corners_left = cv2.findChessboardCorners(img_left, (pointsY, pointsX))
        ret_right, corners_right = cv2.findChessboardCorners(img_right, (pointsY, pointsX))
        print(ret_left and ret_right)
        if (ret_left and ret_right):
            objpoints.append(objp)

            corners_left_2 = cv2.cornerSubPix(img_left, corners_left, (11, 11), (-1, -1), criteria)
            corners_right_2 = cv2.cornerSubPix(img_right, corners_right, (11, 11), (-1, -1), criteria)

            imgpoints_left.append(corners_left_2)
            imgpoints_right.append(corners_right_2)



    cameraMatrix1 = None
    cameraMatrix2 = None
    distCoeffs1 = None
    distCoeffs2 = None

    retval, cameraMatrix1, distCoeffs1, cameraMatrix2, distCoeffs2, R, T, E, F = cv2.stereoCalibrate(objpoints,
                                                                                                     imgpoints_left,
                                                                                                     imgpoints_right,
                                                                                                     None, None, None,
                                                                                                     None,
                                                                                                     (640, 480))



    dict = {"left": {"camera_matirx": cameraMatrix1, "dist_coeffs": distCoeffs1},
            "right": {"camera_matirx": cameraMatrix2, "dist_coeffs": distCoeffs2},
            "reproj_error": retval, "rot_matrix":R, "trans_matrix":T, "ess_matrix":E, "fund_matrix":F, "img_size":  (640,480)}


    print(dict)
    with open('calibration.pickle', 'wb') as f:
        pickle.dump(dict, f)
    return dict


if __name__ == '__main__':
    dict = calibrate(r'C:\Users\Austin\Desktop\roboimage\ImageProcessing2017-python\processing\left\*',r'C:\Users\Austin\Desktop\roboimage\ImageProcessing2017-python\processing\right\*' )
    print(dict)