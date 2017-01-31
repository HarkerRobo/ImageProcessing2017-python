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

DEBUG = True

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
    """Returns the points of the optimal target position for a given image"""
    h, w, _ = img.shape
    return (
        (w/2 + TARGET_WIDTH/2, h/2 - TARGET_HEIGHT/2),
        (w/2 + TARGET_WIDTH/2, h/2 + TARGET_HEIGHT/2),
        (w/2 - TARGET_WIDTH/2, h/2 + TARGET_HEIGHT/2),
        (w/2 - TARGET_WIDTH/2, h/2 - TARGET_HEIGHT/2)
    )

def get_mask(img):
    """Returns a mask were the green parts of the image are white and
    the non-green parts are black
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOW_GREEN, UPPER_GREEN)
    return mask

def get_tape_contours_and_corners(img):
    """Returns an array of contours for the pieces of tape in a given
    mask as well as the corners for each of those contours"""

    mask = get_mask(img)
    _, cnt, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    sorted_contours = sorted(cnt, key=cv2.contourArea, reverse=True)
    found_contours = []
    found_corners = []

    for c in sorted_contours:
        # If the current contour is too small compared to the found
        # contour to be a piece of tape, discard it
        if len(found_contours) == 1:
            ratio = cv2.contourArea(c) / cv2.contourArea(found_contours[0])
            if ratio <= MIN_PERCENT:
                break
        # Check if the countour has four courners
        perimeter = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * perimeter, True)
        # If it does save it
        if len(approx) == 4:
            found_contours.append(c)
            found_corners.append(corners_to_tuples(approx))
            # If there are already 2 rectangles then break
            if len(found_contours) == 2:
                break

    if DEBUG:
        cv2.drawContours(img, found_contours, -1, (255, 0, 0), 1)

    return found_contours, found_corners

def process_image(img):
    debug_img = img.copy()


    getX = lambda c: c[0]
    getY = lambda c: c[1]

    top_corners = np.concatenate(
        [sorted(rect, key=getY)[:2] for rect in found_corners])
    bottom_corners = np.concatenate(
        [sorted(rect, key=getY, reverse=True)[:2] for rect in found_corners])

    draw_corners(debug_img, top_corners, (0, 0, 255))
    draw_corners(debug_img, bottom_corners, (0, 0, 150))

    top_line = get_corner_line(top_corners)
    bottom_line = get_corner_line(bottom_corners)
    draw_line(debug_img, top_line, (255, 0, 0))
    draw_line(debug_img, bottom_line, (255, 0, 0))

    # Just use the first corner's x coordinate to find the left and
    # right contour as the rectangles won't be intersecting
    sorted_rects = sorted(found_corners, key=lambda r: r[0][0])

    left_corners = sorted(sorted_rects[0], key=getX)[:2]
    right_corners = sorted(sorted_rects[1], key=getX, reverse=True)[:2]

    left_line = get_two_corner_line(left_corners)
    right_line = get_two_corner_line(right_corners)
    draw_line(debug_img, left_line, (255, 0, 0))
    draw_line(debug_img, right_line, (255, 0, 0))

    lines = [top_line, right_line, bottom_line, left_line]
    # Convert [a,b,c,d] to [(a,b), (b,c), (c,d), (d,a)]
    line_pairs = list(zip(lines, lines[1:]+lines[:1]))

    l1, l2 = line_pairs[0]
    x, y = get_intersection_point(*line_pairs[0])

    corners = [get_intersection_point(*p) for p in line_pairs]
    int_corners = np.array(corners, np.int32)

    draw_corners(debug_img, int_corners, (0, 255, 0))

    print(corners)
    h, _ = cv2.findHomography(np.array(get_target_corners(img)), np.array(corners))
    print(h)

    cv2.imshow('Processed', debug_img)

    return corners


if __name__ == '__main__':
    im = cv2.imread('sampleImages/img.png')
    cv2.imshow('Original', im)
    process_image(im)
    cv2.waitKey(0)
