# 2017 Image processing code
[![forthebadge](http://forthebadge.com/images/badges/made-with-python.svg)](http://forthebadge.com)

This will probably end up being the vision code we use for 2017.

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
