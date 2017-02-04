"""
This module uses contours to detect the pieces of tape in an image.
These pieces of tape are assumed to be quadrilaterals, and should not
intersect each other.
"""

from functools import partial
import cv2
import numpy as np
from .drawing import draw_corners

LOW_GREEN = np.array([60, 100, 20])
UPPER_GREEN = np.array([80, 255, 255])
MIN_PERCENT1 = 0.6 # After the first rectangle is detected, the second
                   # rectangle's area must be above this percent of the first's

MAX_WIDTH_ERROR = 0.5 # If two contours have to be combined to form the second
                      # rectangle, the percent error in for their width and
                      # that of the first the first's

TAPE_WIDTH = 2
TAPE_HEIGHT = 5
TAPE_WH_RATIO = TAPE_WIDTH / TAPE_HEIGHT
TAPE_ACCEPTABLE_ERROR = 0.7 # The maximum percent error for the ratio of the
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
    """Return the ratio of the width of the rectangle approximating the
    four given points to the height."""
    rect = cv2.minAreaRect(points)
    dims = rect[1]
    if dims[1] == 0:
        return 0
    return dims[0] / dims[1]

def getX(point):
    """Return the x value of a point."""
    return point[0]

def getY(point):
    """Return the y value of a point."""
    return point[1]

def get_center(cnt):
    """Return the center of a given contour."""
    try:
        M = cv2.moments(cnt)
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        return (cX, cY)
    except ZeroDivisionError:
        return (-1e4, -1e4)

def get_distance(cnt, center):
    """Return the distance between a point and the center of a
    contour."""
    cnt_center = get_center(cnt)
    xdiff = center[0] - cnt_center[0]
    ydiff = center[1] - cnt_center[1]
    return np.sqrt(xdiff**2 + ydiff**2)

def get_mask(img):
    """Return a mask were the green parts of the image are white and the
    non-green parts are black.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOW_GREEN, UPPER_GREEN)
    return mask

def large_tape_piece(contours, min_area=1e-4, debug_img=None):
    """
    Return the contours and corners for the piece of tape in the given
    set of contours. If none of the contours are close enough to a piece
    of tape, return None in place of the contours and None in place of
    the corners.

    This function also returns an array of the rest of the contours that
    are yet unprocessed.
    """
    rest = [c.copy() for c in contours]

    for c in contours:
        ratio = cv2.contourArea(c) / min_area
        if ratio <= MIN_PERCENT1:
            break

        rest = rest[1:]

        # Check if the countour has four courners (or 5 in some cases)
        perimeter = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * perimeter, True)

        center = get_center(c)
        moved_center = (center[0]-5, center[1]+5)
        if debug_img is not None:
            cv2.putText(debug_img, str(len(approx)), moved_center,
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))

            draw_corners(debug_img, corners_to_tuples(approx), (0, 0, 255))

        # If it does it could be a piece of tape!
        if 4 <= len(approx) <= 5:
            if debug_img is not None:
                cv2.drawContours(debug_img, [c], -1, (0, 0, 255), 1)
            # Check that the shape of the object matches that of the
            # target Since the width and height could be reversed,
            # 1/ratio must also be checked.
            ratio = get_width_height_ratio(approx)
            err1 = abs(ratio - TAPE_WH_RATIO) / TAPE_WH_RATIO
            err2 = abs(1/ratio - TAPE_WH_RATIO) / TAPE_WH_RATIO
            if err1 > TAPE_ACCEPTABLE_ERROR and err2 > TAPE_ACCEPTABLE_ERROR:
                continue # Skip the object if it does not

            return c, corners_to_tuples(approx), rest

    return None, None, rest

def get_tape_contours_and_corners(mask, debug_img=None):
    """Return an array of contours for the pieces of tape in a given
    mask as well as the corners for each of those contours."""

    _, cnt, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnt_hulls = map(cv2.convexHull, cnt)

    sorted_contours = sorted(cnt_hulls, key=cv2.contourArea, reverse=True)
    found_contours = []
    found_corners = []

    tape_cnt, tape_crn, rest_cnt = large_tape_piece(sorted_contours,
                                                    debug_img=debug_img)

    if tape_cnt is not None and cv2.contourArea(tape_cnt) > 0:
        found_contours.append(tape_cnt)
        found_corners.append(tape_crn)

        # Check if there are two pieces of unblocked tape
        tape_area = cv2.contourArea(tape_cnt)
        tape_width = cv2.boundingRect(tape_cnt)[2]
        sec_cnt, sec_crn, _ = large_tape_piece(rest_cnt, tape_area, debug_img)
        if sec_cnt is not None:
            found_contours.append(sec_cnt)
            found_corners.append(sec_crn)
        else:
            # Otherwise, the peg may be splitting a piece of tape into two.
            # Therefore, try combining the two closest
            distance = partial(get_distance, center=get_center(tape_cnt))
            diff = lambda c: abs(cv2.boundingRect(c)[2] - tape_width)
            good_width = lambda c: diff(c) / tape_width <= MAX_WIDTH_ERROR

            # Find all contours with high enough area and sort them by distance
            # from the previously found piece of tape
            other_cnt = sorted(filter(good_width, rest_cnt), key=distance)
            if len(other_cnt) >= 2:
                combined_cnt = cv2.convexHull(
                    np.concatenate((other_cnt[0], other_cnt[1])))
                cmb_cnt, cmb_corns, _ = large_tape_piece([combined_cnt],
                                                         tape_area, debug_img)
                if cmb_cnt is not None:
                    found_contours.append(cmb_cnt)
                    found_corners.append(cmb_corns)

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
