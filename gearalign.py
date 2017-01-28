import cv2
import numpy as np
from matplotlib import pyplot as plt


img = cv2.imread("pic.jpg", 0)

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
low_green = np.array([150,60,70])
upper_green = np.array([175,80,90])


mask = cv2.inRange(src=hsv, lowerb=low_green, upperb=upper_green)

res = cv2.bitwise_and(src1=img, src2=img, mask=mask)

cv2.imshow("original",img)
cv2.imshow("mask", mask)
cv2.imshow("res",res)