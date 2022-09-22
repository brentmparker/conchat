from collections import namedtuple

_errors = namedtuple(
    "ERRORS",
    [
        "username_exists",
        "invalid_username_password",
        "invalid_message_target",
        "server_error",
        "room_not_found",
    ],
)

ERROR_TYPES = _errors(
    username_exists="username_exists",
    invalid_message_target="invalid_message_target",
    invalid_username_password="invalid_username_password",
    server_error="server_error",
    room_not_found="room_not_found",
)

ERRORS = _errors(
    username_exists="username already exists",
    invalid_message_target="room or user does not exist",
    invalid_username_password="invalid username or password",
    server_error="server error",
    room_not_found="room_not_found",
)
