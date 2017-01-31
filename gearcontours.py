"""
This should do the same thing as gearalign.py, but using contours
"""

import cv2
import numpy as np

LOW_GREEN = np.array([60, 100, 20])
UPPER_GREEN = np.array([80, 255, 255])
MIN_PERCENT = 0.9 # After the first rectangle is detected, the second
                  # rectangle's area must be above this percent of the first's
# Tape area is 10-1/4 in by 5 in

TARGET_SCALE = 10
TARGET_WIDTH = 10.25 * TARGET_SCALE
TARGET_HEIGHT = 5 * TARGET_SCALE

def corners_to_tuples(corners):
    """Converts a given array of corners to an array of tuples"""
    return [tuple(c[0]) for c in corners]

def draw_corners(img, corners, color):
    """Draws corners as circles on an image"""
    for corner in corners:
        cv2.circle(img, tuple(corner), 3, color)

def draw_line(img, line, color):
    """Draws a line of (m, b) on an image"""
    m, b = line
    w = img.shape[1]
    cv2.line(img, (0, int(b)), (w, int(m*w + b)), color)

def get_corner_line(corners):
    """Returns the best fit line for an array of corners.

    This function returns an tuple of (m, b), where the best fit line is
    represented by y = mx + b.
    """
    corner_xs = [c[0] for c in corners]
    corner_ys = [c[1] for c in corners]
    return tuple(np.polyfit(x=corner_xs, y=corner_ys, deg=1))

def get_two_corner_line(corners):
    """Returns the line that contains the two given corners.

    This function returns an tuple of (m, b), where the best fit line is
    represented by y = mx + b.
    """
    x1, y1 = corners[0]
    x2, y2 = corners[1]

    m = (y1 - y2) / (x1 - x2)
    # Since y - y1 = m(x - x1)
    #       y = m(x - x1) + y1
    #       y = mx - mx1 + y1
    b = -m * x1 + y1
    return (m, b)

def get_intersection_point(l1, l2):
    """Returns the point of intersection between two lines"""
    m, b = l1
    n, c = l2
    # Find when mx + b = nx + c
    #           mx - nx = c - b
    #           And...
    x = (c-b) / (m-n)
    # Then plug back in
    y = m*x + b
    return (x, y)

def get_target_corners(img):
    """Returns what should be the corners of the target for the given
    image
    """
    h, w, _ = img.shape
    return (
        (w/2 + TARGET_WIDTH/2, h/2 - TARGET_HEIGHT/2),
        (w/2 + TARGET_WIDTH/2, h/2 + TARGET_HEIGHT/2),
        (w/2 - TARGET_WIDTH/2, h/2 + TARGET_HEIGHT/2),
        (w/2 - TARGET_WIDTH/2, h/2 - TARGET_HEIGHT/2)
    )

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

    print(corners)
    transform = cv2.findHomography(get_target_corners(img), corners)
    print(transform)

    cv2.imshow('Processed', debug_img)

if __name__ == '__main__':
    im = cv2.imread('sampleImages/img.png')
    cv2.imshow('Original', im)
    process_image(im)
    cv2.waitKey(0)
