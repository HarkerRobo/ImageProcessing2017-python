import cv2
from processing import stereo

c1 = cv2.VideoCapture(0)
c2 = cv2.VideoCapture(1)

while True:
	_, i1 = c1.read()
	_, i2 = c2.read()

	stereo.process(i1[::-1], i2[::-1], True)
	print("blerb")
	cv2.waitKey(1)
