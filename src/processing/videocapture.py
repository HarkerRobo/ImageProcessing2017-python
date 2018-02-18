"""
This module contains the VideoCapture class, which substitutes cv2's VideoCapture but runs in a
separate thread.


If cv2's VideoCapture was a class, I could've used multiple inheritance, but alas it's a function so
I have to make a wrapper class.

Most of the documentation you'll see here comes from
http://docs.opencv.org/3.0-beta/modules/videoio/doc/reading_and_writing_video.html.
"""

import threading
import cv2

class VideoCapture(threading.Thread):
    """
    A drop-in replacement for cv2's VideoCapture that runs the capture on a separate thread,
    speeding up processing.
    """

    def __init__(self, *args):
        threading.Thread.__init__(self)
        self._stop = threading.Event()
        self._vc = cv2.VideoCapture(*args)
        self._image = None
        self._status = False

    def run(self):
        """Continuously read images in a loop."""
        while not self._stop.isSet():
            self._status, self._image = self._read()

    def open(self, fileOrDevice):
        """Open a video file or a capturing device for video capturing.

        The method first calls `release()` to close the already opened file or camera.
        """
        self._vc.open(fileOrDevice)

    def isOpened(self):
        """Return True if video capturing has been initialized already.

        If the previous call to the constructor or `open` succeeded, the method returns True.
        """
        return self._vc.isOpened()

    def _grab(self):
        """Grab the next frame from video file or camera and return True in the case of success.

        (From OpenCV documentation) The primary use of the function is in multi-camera environments,
        especially when the cameras do not have hardware synchronization. That is, you call
        VideoCapture::grab() for each camera and after that call the slower method
        VideoCapture::retrieve() to decode and get frame from each camera. This way the overhead on
        demosaicing or motion jpeg decompression etc. is eliminated and the retrieved frames from
        different cameras will be closer in time.

        Also, when a connected camera is multi-head (for example, a stereo camera or a Kinect
        device), the correct way of retrieving data from it is to call VideoCapture::grab first and
        then call VideoCapture::retrieve() one or more times with different values of the channel
        parameter. See https://github.com/Itseez/opencv/tree/master/samples/cpp/openni_capture.cpp.
        """
        self._vc.grab()

    def _retrieve(self, *args):
        """Decode and return the grabbed video frame.

        If no frames has been grabbed (camera has been disconnected, or there are no more frames in
        video file), return a tuple (False, None).
        """
        return self._vc.retrieve(*args)

    def _read(self, *args):
        """Grab, decode and return the next video frame.

        The method combines `_grab` and `_retrieve` in one call.
        This is the most convenient method for reading video files or capturing data from decode and
        return the just grabbed frame. If no frames has been grabbed (camera has been disconnected,
        or there are no more frames in video file), return a tuple (False, None).
        """
        return self._vc.read(*args)

    def read(self):
        """Return the last status and image obtained from calling cv2's read."""
        return self._status, self._image

    def get(self, propId):
        """Return the specified VideoCapture property.

        See
        http://docs.opencv.org/3.0-beta/modules/videoio/doc/reading_and_writing_video.html#videocapture-get
        for a list of valid property identifiers.

        Note: When querying a property that is not supported by the backend used by the VideoCapture
        class, value 0 is returned.
        """
        return self._vc.get(propId)

    def set(self, propid, value):
        """Set a property in the VideoCapture.

        See
        http://docs.opencv.org/3.0-beta/modules/videoio/doc/reading_and_writing_video.html#videocapture-set
        for a list of valid property identifiers.
        """

    def release(self):
        """Close the video file or capturing device."""
        self._vc.release()

    def stop(self):
        """Stop the thread and close the video file or capturing device."""
        self._stop.set()
        self.release()
