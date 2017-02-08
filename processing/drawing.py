"""
A set of utility methods for drawing on images for debugging purposes
"""

import cv2

def draw_corners(img, corners, color):
    """Draw corners as circles on an image."""
    for corner in corners:
        cv2.circle(img, tuple(corner), 3, color)

def draw_line(img, line, color):
    """Draw a line y = mx + b represented by (m, b) on an image."""
    m, b = line
    w = img.shape[1]
    cv2.line(img, (0, int(b)), (w, int(m*w + b)), color)
