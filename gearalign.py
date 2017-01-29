import cv2
import numpy as np
import time

def produce_mask(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    low_green = np.array([60,100,80])
    upper_green = np.array([100,255,255])


    mask = cv2.inRange(src=hsv, lowerb=low_green, upperb=upper_green)


if __name__ == '__main__':
    prod(cv2.imread("sampleImages/img.png"))
    cv2.waitKey(0)
