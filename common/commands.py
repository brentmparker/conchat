from collections import namedtuple

_command_types = namedtuple(
    "COMMAND_TYPES",
    [
        "block",
        "create_room",
        "dm",
        "join_room",
        "list_rooms",
        "list_users",
        "logout",
        "unblock",
    ],
)

COMMAND_TYPES = _command_types(
    block="block",
    create_room="create_room",
    dm="dm",
    join_room="join_room",
    list_rooms="list_rooms",
    list_users="list_users",
    logout="logout",
    unblock="unblock",
)
