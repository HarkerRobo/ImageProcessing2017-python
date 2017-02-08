These images are taken from [FIRST's Vision samples](https://usfirst.collab.net/sf/frs/do/viewRelease/projects.wpilib/frs.sample_programs.2017_c_java_vision_sample).
Before putting them in this directory, I hue shifted them by -15 degrees in OpenCV to better match the color of our LED ring.

As a reference here is the Python code used (run inside the directory):
```python
from os import listdir, mkdir, path
import cv2

try:
    mkdir('out')
except FileExistsError:
    pass

for f in listdir('.'):
    if path.isfile(f) and f[-4:] == '.jpg':
        im = cv2.imread(f)
        hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
        hsv[:,:,0] -= 15
        bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        cv2.imwrite('out/' + f, bgr)

```

This folder contains two directories: `original` and `marked`.
The `original` folder contains images suitable for the image processing code to process,
and the `marked` folder contains images where red circles have been superimposed on the corners of the tape.
