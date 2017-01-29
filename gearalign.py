import cv2
import numpy as np
import time

def process_image(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    low_green = np.array([60,100,80])
    upper_green = np.array([100,255,255])


    mask = cv2.inRange(src=hsv, lowerb=low_green, upperb=upper_green)

    res = cv2.bitwise_and(src1=img, src2=img, mask=mask)

    # cv2.imshow("original",img)
    # cv2.imshow("mask", mask)
    # cv2.imshow("res",res)

    # cv2.imshow("res", res)



    se1 = cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(5,5))
    se2 = cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(2,2))
    mask = cv2.morphologyEx(src=mask, op=cv2.MORPH_CLOSE, kernel=se1)
    # cv2.imshow("mask1", mask)
    mask = cv2.morphologyEx(src=mask, op=cv2.MORPH_OPEN, kernel=se2)
    # cv2.imshow("mask2", mask)


    # mask = np.dstack([mask, mask, mask]) / 255

    out = cv2.bitwise_and(src1=res, src2=res, mask=mask)

    cv2.imshow("out", out)

    # out = cv2.bilateralFilter(src=out, d=2, sigmaColor=5, sigmaSpace=5)
    out = cv2.blur(src=out, ksize=(5,5))
    cv2.imshow("blurred", out)
    # gray = cv2.cvtColor(src=out, code=cv2.COLOR)
    gray = cv2.cvtColor(src=out, code=cv2.COLOR_BGR2GRAY)

    gray = np.float32(gray)

    dst = cv2.cornerHarris(src=gray, blockSize=2, ksize=3, k=0.04)
    dst = cv2.dilate(dst, None)


    out[dst>0.01*dst.max()] = [0,0,255]
    cv2.imshow("CURRENTFIN", out)

if __name__ == '__main__':
    process_image(cv2.imread("pic.jpg"))
    cv2.waitKey(0)
