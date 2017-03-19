"""
This file contains tests for gstreamer.py.
"""

import unittest

from src import gstreamer as gs
from src.gstreamer import PipelinePart as Part

class GstPipelineTests(unittest.TestCase):
    """
    Tests for testing the various classes that inherit from
    gs.PipelinePart
    """

    def test_adding(self):
        """Test that two elements can be added to each other."""
        p = Part('videotestsrc') + Part('autovideosink')
        self.assertEqual(p, 'videotestsrc ! autovideosink')

    def test_tee(self):
        """Test that a basic tee works fine."""
        p = Part('fakesrc') + gs.Tee('t', Part('fakesink'), Part('fakesink'))
        e = 'fakesrc ! tee name=t ! queue ! fakesink t. ! queue ! fakesink'
        self.assertEqual(p, e)

class GstUtilitiesTest(unittest.TestCase):
    """
    Tests for testing utilities contained within gstreamer.py
    """

    def test_parsable(self):
        """Test that the parsed caps match the given ones."""

        caps = (
            'video/x-raw, format=I420, width=320, height=240, '
            'framerate=30/1, pixel-aspect-ratio=1/1, '
            'interlace-mode=progressive'
        )
        p = gs.pipeline('videotestsrc ! {} ! fakesink name=sink'.format(caps))
        p.set_state(gs.Gst.State.PLAYING)

        p.get_state(gs.Gst.CLOCK_TIME_NONE)

        real_caps_obj = gs.get_sink_caps(p.get_by_name('sink'))
        real_caps = gs.make_command_line_parsable(real_caps_obj)

        p.set_state(gs.Gst.State.NULL)

        self.assertEqual(caps, real_caps)

if __name__ == '__main__':
    unittest.main(verbosity=2)
