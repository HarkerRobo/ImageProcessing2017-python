"""
Finds the corners of the gear pieces of tape by using best fit lines

This module is currently not being used by anything as opencv's
findHomography function can take in an arbitrary number of points.

However, if we cannot get this to work, this may come in handy when we
use trig to estimate angles.

Also note that this module assumes that two rectangles will always be in
an image, which is obviously untrue. Therefore, this code will either
need to be modified to work with this case, or the importing script will
need to check for this case.
"""

import cv2
import numpy as np
from .tapecontours import *

getX = lambda c: c[0]
getY = lambda c: c[1]

def get_lines(found_corners, debug_img=None):
    """Return an array of the best fit lines for the sides of the two
    pieces of tape.
    """
    top_corners = np.concatenate(
        [sorted(rect, key=getY)[:2] for rect in found_corners])
    bottom_corners = np.concatenate(
        [sorted(rect, key=getY, reverse=True)[:2] for rect in found_corners])

    if debug_img is not None:
        draw_corners(debug_img, top_corners, (0, 0, 255))
        draw_corners(debug_img, bottom_corners, (0, 0, 150))

    top_line = get_corner_line(top_corners)
    bottom_line = get_corner_line(bottom_corners)
    if debug_img is not None:
        draw_line(debug_img, top_line, (255, 0, 0))
        draw_line(debug_img, bottom_line, (255, 0, 0))

    # Just use the first corner's x coordinate to find the left and
    # right contour as the rectangles won't be intersecting
    sorted_rects = sorted(found_corners, key=lambda r: r[0][0])

    left_corners = sorted(sorted_rects[0], key=getX)[:2]
    right_corners = sorted(sorted_rects[1], key=getX, reverse=True)[:2]

    left_line = get_two_corner_line(left_corners)
    right_line = get_two_corner_line(right_corners)
    if debug_img is not None:
        draw_line(debug_img, left_line, (255, 0, 0))
        draw_line(debug_img, right_line, (255, 0, 0))

    lines = [top_line, right_line, bottom_line, left_line]

    return lines

def get_intersection_points(lines, debug_img=None):
    """Return the four intersection points for the four given lines
    whose enclosed shape is a quadrilateral.
    """

    # Convert [a,b,c,d] to [(a,b), (b,c), (c,d), (d,a)]
    line_pairs = list(zip(lines, lines[1:]+lines[:1]))

    corners = [get_intersection_point(*p) for p in line_pairs]

    if debug_img is not None:
        int_corners = np.array(corners, np.int32)
        draw_corners(debug_img, int_corners, (0, 255, 0))

    return corners

def get_outside_corners(tape_corners, debug_img=None):
    """Return the locations of the four outside corners of two pieces of
    tape. The given corners should be a 3D array of shape (2, 4, 2).
    """
    lines = get_lines(tape_corners, debug_img)
    return get_intersection_points(lines, debug_img)

if __name__ == '__main__':
    im = cv2.imread('sampleImages/img.png')
    cv2.imshow('Original', im)
    mask = get_mask(im)
    cnts, crns = get_tape_contours_and_corners(mask, im)
    get_outside_corners(crns, im)

    cv2.imshow('Processsed', im)

    cv2.waitKey(0)
