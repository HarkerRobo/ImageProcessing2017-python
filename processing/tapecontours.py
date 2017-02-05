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

MAX_AREA_ERROR = 0.6 # If two contours have to be combined to form the second
                      # rectangle, the percent error in for their area and
                      # that of the first the first's
MAX_HEIGHT_ERROR = 0.4 # If two contours have to be combined to form the second
                      # rectangle, the percent error in for their height and
                      # that of the first the first's

MIN_PAD = 1 # Percent of sqrt of contour area

TAPE_WIDTH = 2
TAPE_HEIGHT = 5
TAPE_WH_RATIO = TAPE_WIDTH / TAPE_HEIGHT
TAPE_ACCEPTABLE_ERROR = 0.4 # The maximum percent error for the ratio of the
                            # target's width to height

# Tape area is 10-1/4 in by 5 in
TARGET_SCALE = 10
TARGET_WIDTH = 10.25
TARGET_HEIGHT = 5
TARGET_WIDTH_SCALED = TARGET_WIDTH * TARGET_SCALE
TARGET_HEIGHT_SCALED = TARGET_HEIGHT * TARGET_SCALE

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

def color_contour(contour, n, img):
    """
    Draws the contour on the given image if it is not None. The
    parameter n defines the color of the contour: with increasing values
    of n the contour will be drawn more green instead of red.
    """
    if img is not None:
        if n < 5:
            green = n * 51
            red = 255
        if n > 5:
            green = 255
            red = 255 - n * 51
        cv2.drawContours(img, [contour], -1, (0, green, red), 1)

def is_tape(contour, debug_img=None):
    """
    Return true if the given contour could represent a piece of tape,
    otherwise return false.

    This function also returns the bounding rect points upon success.
    """
    rect = cv2.boundingRect(contour)
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)

    color_contour(contour, 2, debug_img)

    # Criteria 1: Contour has 4 or 5 contours
    center = get_center(contour)
    moved_center = (int(center[0]-5), int(center[1]+5))
    if debug_img is not None:
        cv2.putText(debug_img, str(len(approx)), moved_center,
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))

        draw_corners(debug_img, corners_to_tuples(approx), (0, 0, 255))

    if not 4 <= len(approx) <= 5:
        return False, None

    color_contour(contour, 3, debug_img)

    # Criteria 2: Contour's area is at least 70% of that of the bounding rect
    x, y, w, h = rect
    if area == 0 or area / w / h < 0.7:
        return False, None

    color_contour(contour, 4, debug_img)

    # Critera 3: % error between actual aspect ratio and expected is <= 70%
    ratio = min(w/h, h/w) # w/h ratio since w will always be less than h

    # Since w will usually be less but h won't, the ratio should be less
    err = (TAPE_WH_RATIO - ratio) / TAPE_WH_RATIO

    if abs(err) < TAPE_ACCEPTABLE_ERROR:
        points = [[(x, y+h)], [(x, y)], [(x+w, y)], [(x+w, y+h)]]
        # One could also return approx instead of points but approx is not
        # always accurate
        return True, points

    return False, None

def large_tape_piece(contours, tape_cnt=None, tape_area=None, debug_img=None):
    """
    Return the contours and corners for the piece of tape in the given
    set of contours. If none of the contours are close enough to a piece
    of tape, return None in place of the contours and None in place of
    the corners.

    This function also returns an array of the rest of the contours that
    are yet unprocessed.
    """
    rest = [c for c in contours]

    for c in contours:
        if tape_cnt is not None and tape_area is not None:
            err1 = abs(cv2.contourArea(c) - tape_area) / tape_area
            err2 = (abs(cv2.boundingRect(c)[3] - cv2.boundingRect(tape_cnt)[3])
                    / tape_area)

            color_contour(c, 0, debug_img)
            if err1 > MAX_AREA_ERROR:
                break
            color_contour(c, 1, debug_img)
            if err2 > MAX_HEIGHT_ERROR:
                break

        rest = rest[1:]

        tape, approx = is_tape(c, debug_img)
        if tape:
            return c, corners_to_tuples(approx), rest

    return None, None, rest

def split_tape_piece(contours, tape_cnt=None, tape_area=None, debug_img=None):
    """
    Return the contours and corners for the piece of tape in the given
    set of contours, created by combining the two largest contours. If
    none of the contours are close enough to a piece of tape, return
    None in place of the contours and None in place of the corners.
    """
    if tape_cnt is not None and tape_area is not None:
        distance = partial(get_distance, center=get_center(tape_cnt))
        err = lambda c: abs(cv2.contourArea(c) - tape_area) / tape_area
        cmb = lambda c: distance(c)**0.1 * err(c)**10

        # Find all contours with high enough area and sort them by distance
        # from the previously found piece of tape
        other_cnt = sorted(contours, key=cmb)
    else:
        other_cnt = contours

    if len(other_cnt) >= 2:
        combined_cnt = cv2.convexHull(
            np.concatenate((other_cnt[0], other_cnt[1])))
        cmb_cnt, cmb_corns, _ = large_tape_piece([combined_cnt], tape_cnt,
                                                 tape_area, debug_img)
        return cmb_cnt, cmb_corns
        # if cmb_cnt is not None:
        #     rest = []
        #     for cnt in contours:
        #         if cnt is not other_cnt[0] and cnt is not other_cnt[1]:
        #             rest.append(cnt)
        #     return cmb_cnt, cmb_corns, rest

    return None, None

def get_tape_contours_and_corners(mask, debug_img=None):
    """Return an array of contours for the pieces of tape in a given
    mask as well as the corners for each of those contours."""

    _, cnt, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    sorted_contours = sorted(cnt, key=cv2.contourArea, reverse=True)
    found_contours = []
    found_corners = []

    tape_cnt, tape_crn, rest = large_tape_piece(sorted_contours,
                                                debug_img=debug_img)

    if tape_cnt is not None and cv2.contourArea(tape_cnt) > 0:
        found_contours.append(tape_cnt)
        found_corners.append(tape_crn)

        tcx, tcy = get_center(tape_cnt)

        area = cv2.contourArea(tape_cnt)
        asqrt = np.sqrt(area)
        percent_size = np.sqrt(area / (TAPE_WIDTH*TAPE_HEIGHT))
        exact_range = TARGET_WIDTH * percent_size
        x_range = exact_range * 1.8 / 2
        y_range = TARGET_HEIGHT * percent_size * 1.8 / 2

        if debug_img is not None:
            cv2.rectangle(debug_img, (int(tcx-x_range), int(tcy-y_range)), (int(tcx-asqrt*MIN_PAD), int(tcy+y_range)), (0, 150, 0), 1)
            cv2.rectangle(debug_img, (int(tcx+asqrt*MIN_PAD), int(tcy-y_range)), (int(tcx+x_range), int(tcy+y_range)), (0, 150, 0), 1)

        rest_left = []
        rest_right = []

        for c in sorted_contours:
            cx, cy = get_center(c)
            iny = tcy - y_range < cy < tcy + y_range
            if c is not tape_cnt and iny:
                if tcx - x_range < cx < tcx - asqrt * MIN_PAD:
                    rest_left.append(c)
                if tcx + asqrt * MIN_PAD< cx < tcx + x_range:
                    rest_right.append(c)

        lcnt, lcrn = split_tape_piece(rest_left, tape_cnt, area, debug_img=debug_img)
        rcnt, rcrn = split_tape_piece(rest_right, tape_cnt, area, debug_img=debug_img)

        # I don't know how to compare things so I'm going with the left one
        if lcnt is None:
            lcnt = rcnt
            lcrn = rcrn

        if lcnt is not None:
            found_contours.append(lcnt)
            found_corners.append(lcrn)
        else:
            t2_cnt, t2_crn, _ = large_tape_piece(rest, tape_cnt, area,
                                                 debug_img=debug_img)
            if t2_cnt is not None:
                found_contours.append(t2_cnt)
                found_corners.append(t2_crn)

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
