"""
This should do the same thing as gearalign.py, but using contours
"""

import cv2
import numpy as np

LOW_GREEN = np.array([60, 100, 20])
UPPER_GREEN = np.array([80, 255, 255])
MIN_PERCENT = 0.9 # After the first rectangle is detected, the second
                  # rectangle's area must be above this percent of the first's

def process_image(img):
    debugImg = img.copy()

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOW_GREEN, UPPER_GREEN)

    _, cnt, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    sortedContours = sorted(cnt, key=cv2.contourArea, reverse=True)
    foundContours = []
    foundCorners = []

    for c in sortedContours:
        # If the current contour is too small compared to the found
        # contour to be a piece of tape, discard it
        if len(foundContours) == 1:
            ratio = cv2.contourArea(c) / cv2.contourArea(foundContours[0])
            if ratio <= MIN_PERCENT:
                break
        # Check if the countour has four courners
        perimeter = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * perimeter, True)
        # If it does save it
        if len(approx) == 4:
            foundContours.append(c)
            foundCorners.append(approx)
            # If there are already 2 rectangles then break
            if len(foundContours) == 2:
                break

    cv2.drawContours(debugImg, foundContours, -1, (255, 0, 0), 1)

    return foundCorners
    for rectangle in foundCorners:
        for corner in rectangle:
            cv2.circle(debugImg, tuple(corner[0]), 3, (0, 0, 255))


    print(foundContours)

    cv2.imshow('Processed', debugImg)

    # cv2.imshow('mask', mask)

if __name__ == '__main__':
    im = cv2.imread('sampleImages/img.png')
    cv2.imshow('Original', im)
    process_image(im)
    cv2.waitKey(0)
