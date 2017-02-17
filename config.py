"""
This module contains functions for retrieving data from the config file.
"""

from collections import namedtuple
import os
import ruamel.yaml

DIRNAME = os.path.dirname(os.path.realpath(__file__))
FILE_LOCATION = os.path.join(DIRNAME, "shared", "config.yml")

def getconfig(stream=open(FILE_LOCATION), file=True):
    """Return the parsed contents of the specified yml config file.

    The file parameter determines whether the specified stream is a
    filename or string.
    """
    if file:
        with open(stream) as f:
            return ruamel.yaml.load(f, ruamel.yaml.RoundTripLoader)
    else:
        return ruamel.yaml.load(stream, ruamel.yaml.RoundTripLoader)

Config = namedtuple('Config', ['ip', 'params', 'controlport'])

def fromyaml(yaml):
    """Return a config named tuple from a given piece of yaml."""
    return Config(ip=yaml['ip'], params=dict(yaml['params']),
                  controlport=yaml['ports']['control'])

def configfor(name, stream=FILE_LOCATION, file=True):
    """Return the configuration for the stream with the specified name.

    This function takes in a name, which is a toplevel key in the
    configuration file, and the second and third parameters behaves the
    same as the parameters of `getconfig`.
    """
    try:
        allconf = getconfig(stream, file)
        confyaml = next(c for c in allconf if c['name'] == name)
        return fromyaml(confyaml)
    except StopIteration:
        raise ValueError('Invalid stream name')
