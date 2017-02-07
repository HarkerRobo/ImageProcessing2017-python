"""
Constants and methods for constructing and parsing messages that are
sent between the Raspberry Pi and the Roborio.

All messages are encoded as JSON. They have a key 'type', which
designates the type of the message (i.e. what it should do). Below is an
example of a message:

{
    "type": "start",
    "port": "3000",
    "host": "10.10.72.43",
    "iso": 500,
    "shutterspeed": 2000
}
"""

import json

# Message types
TYPE_START_STREAM = 'start'
TYPE_STOP_STREAM = 'stop'
TYPE_ERROR = 'error'
TYPE_RESULTS = 'results'

# Fields
FIELD_TYPE = 'type'
FIELD_PORT = 'port'
FIELD_HOST = 'host'
FIELD_ISO = 'iso'
FIELD_SS = 'shutterspeed'
FIELD_ERROR = 'message'
FIELD_CORNERS = 'corners'

# Message schemas
MESSAGES = {
    TYPE_START_STREAM: {
        FIELD_PORT: int,
        FIELD_HOST: str,
        FIELD_ISO: int,
        FIELD_SS: int
    },
    TYPE_STOP_STREAM: {},
    TYPE_ERROR: {
        FIELD_ERROR: str
    },
    TYPE_RESULTS: {
        FIELD_CORNERS: list
    }
}

def parse_message(message_str):
    """Take in a message as a string, validate it, and output json.

    While this function will raise a ValueError if the message is
    missing required fields, it will not throw any errors if it includes
    extra ones.
    """
    message = json.loads(message_str) # Raises a ValueError if json is invalid
    if 'type' not in message:
        raise ValueError('Message does not have a type field')
    if message['type'] not in MESSAGES:
        raise ValueError('Message type is not understood')

    message_schema = MESSAGES[message['type']]
    for field in message_schema:
        if field not in message:
            raise ValueError(
                'Message does not contain required field {}'.format(field))
        if type(message[field]) is not type(message_schema[field]):
            raise ValueError((
                'Field {} is of type {.__name__} and not of type {.__name__}'
                ).format(field, message_schema[field]))

    return message

def create_message(message_type, fields):
    """Create a message string from a given tyoe and fields."""
    message = dict({FIELD_TYPE: message_type}, **fields)
    return json.dumps(message) + '\n'
