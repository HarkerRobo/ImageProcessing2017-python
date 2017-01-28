import cv2
import numpy as np
import time
from matplotlib import pyplot as plt


img = cv2.imread("pic.jpg")

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

low_green = np.array([60,100,80])
upper_green = np.array([100,255,255])


mask = cv2.inRange(src=hsv, lowerb=low_green, upperb=upper_green)

res = cv2.bitwise_and(src1=img, src2=img, mask=mask)

cv2.imshow("original",img)
cv2.imshow("mask", mask)
cv2.imshow("res",res)

se1 = cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(5,5))
se2 = cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(2,2))
mask = cv2.morphologyEx(src=mask, op=cv2.MORPH_CLOSE, kernel=se1)
mask = cv2.morphologyEx(src=mask, op=cv2.MORPH_OPEN, kernel=se2)

mask = np.dstack([mask, mask, mask]) / 255
out = img * mask

cv2.imshow("out", out)



cv2.waitKey(0)