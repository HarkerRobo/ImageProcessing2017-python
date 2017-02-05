import os
import sys
import unittest

import numpy as np
import cv2

# Add the parent directory to the path so other modules can be imported
currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from processing import tapecontours

# Range for fist mask
LOW_RED = np.array([169, 100, 100])
ML_RED = np.array([179, 255, 255])
# Range for second mask
MH_RED = np.array([0, 100, 100])
HIGH_RED = np.array([10, 255, 255])

MAX_DIST = 50 # Maximum error between calculated corner and actual corner
SHOW_IMAGES = False # Whether to show images for failed results

def get_circles(img):
    """Return the positions of the red circles in an imagFe."""
    # First mask
    hue = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hue, LOW_RED, ML_RED)
    mask2 = cv2.inRange(hue, MH_RED, HIGH_RED)
    mask = cv2.bitwise_or(mask1, mask2)
    # Then detect cirlces
    _, cnt, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                 cv2.CHAIN_APPROX_SIMPLE)
    circles = map(cv2.minEnclosingCircle, cnt)
    centers = np.array([c for (c, r) in circles])
    return centers

def compare_corners(c1, c2):
    """Determines if the given corners are close enough."""
    if c1.shape[0] != c2.shape[0]:
        return False
    if c1.shape[0] == 0:
        return True
    diff = np.sum(np.square(np.abs(c2 - c1[0])), axis=1)
    index = np.argmin(diff)
    dist = np.sqrt(diff[index])
    if dist > MAX_DIST:
        return False
    # Python doesn't optimize tail recursion, so this will be less
    # efficient than a while loop. However, I personally think this way
    # is more elegant.
    return compare_corners(np.delete(c1, 0, 0), np.delete(c2, index, 0))

class ImageTests(unittest.TestCase):
    """
    This test currently only has 1 test - checking that corners can be
    correctly identified in images of retroreflective tape.
    """

    CMP_ERR = 'The determined corners are not correct'
    LEAST_PERCENT = 0.5 # Minimum percent of images that must be
                        # identified correctly to pass

    def test_corners(self):
        """
        Test that tapecontours.get_corners_from_image returns the
        correct corners for a set of sample images.
        """
        markeddir = os.path.join(currentdir, 'testImages/marked')
        origdir = os.path.join(currentdir, 'testImages/original')

        correct = 0
        incorrect = 0
        for f in os.listdir(markeddir):
            # Read the two images
            marked = cv2.imread(os.path.join(markeddir, f))
            original = cv2.imread(os.path.join(origdir, f))

            # Find the circles
            expected = get_circles(marked)
            try:
                actual = np.concatenate(tapecontours.get_corners_from_image(
                    original, show_image=False))
            except ValueError:
                actual = np.array([])

            result = compare_corners(expected, actual)
            if not result and SHOW_IMAGES:
                tapecontours.get_corners_from_image(original,
                                                    show_image=True)
                cv2.waitKey(0)
            if result:
                correct += 1
            else:
                incorrect += 1

        percent = correct / (correct + incorrect)
        print('Getting corners: {} correct, {} incorrect ({}% correct)'
              .format(correct, incorrect, percent*100))
        self.assertGreater(percent, self.LEAST_PERCENT)

if __name__ == '__main__':
    unittest.main()
