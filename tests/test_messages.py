"""
This file contains tests for networking/messages.py.
"""

import os
import sys
import unittest

from src.networking import messages

class MessagesTest(unittest.TestCase):
    """
    Tests for testing creating and parsing messages
    """

    def test_creation(self):
        """Test that messages can be created."""
        m = messages.create_message(messages.TYPE_START_STREAM, {})
        self.assertIsNotNone(m)

    def test_valid_parse(self):
        """Test that a message can be successfully parsed."""
        m = {
            messages.FIELD_TYPE: messages.TYPE_ERROR,
            messages.FIELD_ERROR: 'something'
        }
        stringified = messages.create_message(messages.TYPE_ERROR, {
            messages.FIELD_ERROR: 'something'
        })
        parsed = messages.parse_message(stringified)
        self.assertDictEqual(m, parsed)

    def test_parse_type(self):
        """Test that parsed messages with bad types throw errors."""
        m = '{"type": "nonexistent"}'
        self.assertRaises(ValueError, messages.parse_message, m)

    def test_parse_fields(self):
        """Test that parsed messages with bad fields throw errors."""
        m = '{"type": "error", "random": "error!"}'
        self.assertRaises(ValueError, messages.parse_message, m)

    def test_parse_field_types(self):
        """Test that parsed messages with bad types throw errors."""
        m = '{"type": "error", "message": 123456}'
        self.assertRaises(ValueError, messages.parse_message, m)

if __name__ == '__main__':
    unittest.main(verbosity=2)
