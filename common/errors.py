from collections import namedtuple

_errors = namedtuple(
    "ERRORS", ["username_exists", "invalid_username_password", "invalid_message_target"]
)

ERRORS = _errors(
    username_exists="username already exists",
    invalid_message_target="room or user does not exist",
    invalid_username_password="invalid username or password",
)
