"""
This file contains tests for networking/messages.py.
"""

import os
import sys
import unittest

# Add the parent directory to the path so other modules can be imported
currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import config

class ConfigTest(unittest.TestCase):
    """
    Tests for reading from the config file
    """

    incorrect_yaml = """\
- name: Incorrect
  ip: "I'm not filling out the rest of this"
"""

    paramed_yaml = """\
- name: Paramed
  ip: something
  params:
    test: This
    some: should
    params: work
  ports:
    control: 1234
    stream: 2345
"""

    def test_valid_read(self):
        """Test that valid stream configurations can be read."""
        c = config.configfor('Vision')
        self.assertIsNotNone(c)

    def test_invalid_read(self):
        """Test that invalid stream configurations throw errors."""
        self.assertRaises(ValueError, config.configfor, 'I do not exist!')

    def test_read_string(self):
        """Test that a configuration string can be read."""
        c = config.getconfig(stream=self.incorrect_yaml, file=False)
        self.assertIsNotNone(c)

    def test_find_unfilled(self):
        """Test that finding a section of the config file without the
        needed keys throws an error."""
        self.assertRaises(KeyError, config.configfor, 'Incorrect',
                          stream=self.incorrect_yaml, file=False)

    def test_find_string(self):
        """Test that a config file section can be found in a valid
        string."""
        c = config.configfor('Paramed', stream=self.paramed_yaml, file=False)
        self.assertIsNotNone(c)

    def test_get_params(self):
        """Test that the params of a config file section can
        successfully be found."""
        c = config.configfor('Paramed', stream=self.paramed_yaml, file=False)
        self.assertEqual('{test} {some} {params}'.format(**c.params),
                         'This should work')

if __name__ == '__main__':
    unittest.main(verbosity=2)
