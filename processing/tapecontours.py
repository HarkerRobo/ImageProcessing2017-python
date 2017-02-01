"""
This module uses contours to detect the pieces of tape in an image.
These pieces of tape are assumed to be quadrilaterals, and should not
intersect each other.
"""

import cv2
import numpy as np
from .drawing import draw_corners

LOW_GREEN = np.array([60, 100, 20])
UPPER_GREEN = np.array([80, 255, 255])
MIN_PERCENT = 0.8 # After the first rectangle is detected, the second
                  # rectangle's area must be above this percent of the first's

TAPE_WIDTH = 2
TAPE_HEIGHT = 5
TAPE_WH_RATIO = TAPE_WIDTH / TAPE_HEIGHT
TAPE_ACCEPTABLE_ERROR = 0.2 # The maximum percent error for the ratio of the
                              # target's width to height

# Tape area is 10-1/4 in by 5 in
TARGET_SCALE = 10
TARGET_WIDTH = 10.25 * TARGET_SCALE
TARGET_HEIGHT = 5 * TARGET_SCALE

DEBUG = True # Makes applicable functions show debugging images by default

def corners_to_tuples(corners):
    """Convert a given array of corners to an array of tuples."""
    return [tuple(c[0]) for c in corners]

def get_target_corners(img):
    """Return the points of the optimal target position for a given
    image.
    """
    h, w, _ = img.shape
    return (
        (w/2 + TARGET_WIDTH/2, h/2 - TARGET_HEIGHT/2),
        (w/2 + TARGET_WIDTH/2, h/2 + TARGET_HEIGHT/2),
        (w/2 - TARGET_WIDTH/2, h/2 + TARGET_HEIGHT/2),
        (w/2 - TARGET_WIDTH/2, h/2 - TARGET_HEIGHT/2)
    )

def get_width_height_ratio(points):
    """Returns the ratio of the width of the rectangle approximating the
    four given points to the height."""
    rect = cv2.minAreaRect(points)
    dims = rect[1]
    if dims[1] == 0:
        return 0
    return dims[0] / dims[1]

def get_mask(img):
    """Return a mask were the green parts of the image are white and the
    non-green parts are black.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOW_GREEN, UPPER_GREEN)
    return mask

def get_tape_contours_and_corners(mask, debug_img=None):
    """Return an array of contours for the pieces of tape in a given
    mask as well as the corners for each of those contours."""

    _, cnt, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    sorted_contours = sorted(cnt, key=cv2.contourArea, reverse=True)
    found_contours = []
    found_corners = []

    for c in sorted_contours:
        # If the current contour is too small compared to the found
        # contour to be a piece of tape, discard it
        if len(found_contours) == 1:
            area = cv2.contourArea(found_contours[0])
            if area == 0:
                break # So there isn't a ZeroDivisionError
            ratio = cv2.contourArea(c) / area
            if ratio <= MIN_PERCENT:
                break
        # Check if the countour has four courners
        perimeter = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * perimeter, True)

        # If it does save it
        if len(approx) == 4:
            cv2.drawContours(debug_img, [c], -1, (0, 0, 255), 1)
            # Check that the shape of the object matches that of the
            # target Since the width and height could be reversed,
            # 1/ratio must also be checked.
            ratio = get_width_height_ratio(approx)
            err1 = abs(ratio - TAPE_WH_RATIO) / TAPE_WH_RATIO
            err2 = abs(1/ratio - TAPE_WH_RATIO) / TAPE_WH_RATIO
            if err1 > TAPE_ACCEPTABLE_ERROR and err2 > TAPE_ACCEPTABLE_ERROR:
                continue # Skip the object if it does not

            found_contours.append(c)
            found_corners.append(corners_to_tuples(approx))
            # If there are already 2 rectangles then break
            if len(found_contours) == 2:
                break

    if debug_img is not None:
        cv2.drawContours(debug_img, found_contours, -1, (255, 0, 0), 1)
        for corner_set in found_corners:
            draw_corners(debug_img, corner_set, (255, 0, 0))

    return found_contours, found_corners

def get_corners_from_image(img, show_image=DEBUG):
    """Return an array of the corners of the tape in a given image."""
    debug_img = img.copy() if show_image else None

    mask = get_mask(img)
    if show_image:
        cv2.imshow('mask', mask)
    _, crns = get_tape_contours_and_corners(mask, debug_img)

    if show_image:
        cv2.imshow('corners', debug_img)

    return crns
