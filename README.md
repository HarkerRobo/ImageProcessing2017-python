# ![2017 Image processing code](https://rawgit.com/HarkerRobo/ImageProcessing2017-python/master/images/logo.svg)

[<img src="http://forthebadge.com/images/badges/made-with-python.svg" height="20" alt="Made with Python" />](https://xkcd.com/353/)
[![Travis](https://img.shields.io/travis/HarkerRobo/ImageProcessing2017-python.svg?style=flat-square)](https://travis-ci.org/HarkerRobo/ImageProcessing2017-python)

This is the vision code we will use for 2017.

So you can understand it better, below is a flow chart of the general process:

    +-----------------------+                                Arena network
    |     Video device      |                               (terrible router
    | (Raspi cam or webcam) |                                picture below)
    +-----------+-----------+      +----------------------+                 +-------------------+
                |                  | h.264 encoded stream |     )  |  (     | Program running   |
                v             +----> over rtp over udp    +---> ####### +---> on driver station |
     +----------+---------+   |    | streamed to some ip  |     #######     | displaying stream |
     | Gstreamer pipeline +---+    +----------------------+                 +-------------------+
     |  Note: output is   |                                        ^
     |     duplicated     +---+                                    |
     +--------------------+   |    +------------------------+      | Sends results to driver
                              +----> Shared memory location |      | station to display them
                                   +-----------+------------+      +-------------+
                                               |                                 |
                                               v                                 |
                                  +------------+-------------+     +-------------+------------+
                                  | OpenCV VideoSource using |     | OpenCV script finding    |
                                  |   GStreamer to capture   +-----> position of tape as well |
                                  |    images from stream    |     | as calculating angles    |
                                  +--------------------------+     +--------------------------+
