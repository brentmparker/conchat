import json
from typing import Callable, Dict, List
from collections import namedtuple

_message_types = namedtuple(
    "MESSAGE_TYPES",
    [
        "chat",
        "blacklist",
        "join_room",
        "list_rooms",
        "login",
        "login_response",
        "logout",
        "register",
        "register_response",
        "error",
    ],
)

MESSAGE_TYPE = "message_type"
MESSAGE_TYPES = _message_types(
    blacklist="blacklist",
    chat="message_chat",
    join_room="join_room",
    list_rooms="list_rooms",
    login="message_login",
    login_response="message_login_response",
    logout="message_logout",
    register="message_register",
    register_response="message_register_response",
    error="message_error",
)

_fields_blacklist_message = namedtuple(
    "FIELDS_BLACKLIST_MESSAGE", ["userid", "blocked_username"]
)

_fields_list_rooms_message = namedtuple("FIELDS_LIST_ROOMS_MESSAGE", ["rooms"])

_fields_join_room_message = namedtuple(
    "FIELDS_JOIN_ROOM_MESSAGE", ["userid", "roomname"]
)

_fields_chat_message = namedtuple(
    "FIELDS_CHAT_MESSAGE",
    [
        "id",
        "authorname",
        "authorid",
        "roomid",
        "target_userid",
        "message",
        "createdate",
    ],
)

_fields_chat_messages = namedtuple("CHAT_MESSAGES", ["messages"])
_fields_login_message = namedtuple("FIELDS_LOGIN_MESSAGE", ["username", "password"])
_fields_login_response_message = namedtuple(
    "FIELDS_LOGIN_RESPONSE_MESSAGE", ["username", "userid"]
)
_fields_register_response_message = namedtuple(
    "FIELDS_REGISTER_RESPONSE_MESSAGE", ["username", "status"]
)
_fields_error_message = namedtuple("FIELDS_ERROR_MESSAGE", ["errortype", "message"])

FIELDS_BLACKLIST_MESSAGE = _fields_blacklist_message(
    userid="userid", blocked_username="blocked_username"
)

FIELDS_LIST_ROOMS_MESSAGE = _fields_list_rooms_message(rooms="rooms")

FIELDS_JOIN_ROOM_MESSAGE = _fields_join_room_message(
    userid="userid", roomname="roomname"
)

FIELDS_CHAT_MESSAGE = _fields_chat_message(
    id="id",
    authorname="authorname",
    roomid="roomid",
    target_userid="target_userid",
    message="message",
    authorid="authorid",
    createdate="createdate",
)
FIELDS_CHAT_MESSAGES = _fields_chat_messages(messages="messages")
FIELDS_LOGIN_MESSAGE = _fields_login_message(username="username", password="password")
# registration requires same fields as login
FIELDS_REGISTER_MESSAGE = _fields_login_message(
    username="username", password="password"
)
FIELDS_LOGIN_RESPONSE_MESSAGE = _fields_login_response_message(
    username="username", userid="userid"
)
# logout message requires same fields as login response
FIELDS_LOGOUT_MESSAGE = _fields_login_response_message(
    username="username", userid="userid"
)
FIELDS_REGISTER_RESPONSE_MESSAGE = _fields_register_response_message(
    username="username", status="status"
)
FIELDS_ERROR_MESSAGE = _fields_error_message(errortype="errortype", message="message")


def message_factory(
    data: Dict[str, str] | List[Dict[str, str]], message_type: str
) -> str:
    """Takes a data dict and a type and produces a JSON string depending on the type

    Args:
        data (Dict): A dictionary containing appropriate data for each event. The data required is defined in any of the FIELDS_* constants imported from this file

    Returns:
        str: a JSON string ready to send to client or server
    """
    serializer = _get_serializer(message_type=message_type)
    return serializer(data)


def _get_serializer(message_type) -> Callable:
    match message_type:
        case MESSAGE_TYPES.blacklist:
            return _serialize_blacklist_message
        case MESSAGE_TYPES.join_room:
            return _serialize_join_room_message
        case MESSAGE_TYPES.list_rooms:
            return _serialize_list_rooms_message
        case MESSAGE_TYPES.chat:
            # return _serialize_chat_message
            return _serialize_chat_messages
        case MESSAGE_TYPES.login:
            return _serialize_login_message
        case MESSAGE_TYPES.login_response:
            return _serialize_login_response_message
        case MESSAGE_TYPES.logout:
            return _serialize_logout_message
        case MESSAGE_TYPES.register:
            return _serialize_register_message
        case MESSAGE_TYPES.register_response:
            return _serialize_register_response_message
        case MESSAGE_TYPES.error:
            return _serialize_error_message


def _serialize_blacklist_message(data: Dict) -> str:
    payload = {
        FIELDS_BLACKLIST_MESSAGE.userid: data[FIELDS_BLACKLIST_MESSAGE.userid],
        FIELDS_BLACKLIST_MESSAGE.blocked_username: data[
            FIELDS_BLACKLIST_MESSAGE.blocked_username
        ],
    }

    return json.dumps(payload)


def _serialize_list_rooms_message(data: Dict) -> str:
    payload = {
        FIELDS_LIST_ROOMS_MESSAGE.rooms: data.get(FIELDS_LIST_ROOMS_MESSAGE.rooms, None)
    }

    return json.dumps(payload)


def _serialize_join_room_message(data: Dict) -> str:
    payload = {
        FIELDS_JOIN_ROOM_MESSAGE.userid: data[FIELDS_JOIN_ROOM_MESSAGE.userid],
        FIELDS_JOIN_ROOM_MESSAGE.roomname: data.get(
            FIELDS_JOIN_ROOM_MESSAGE.roomname, "Lobby"
        ),
    }

    return json.dumps(payload)


def _serialize_chat_message(data: Dict) -> str:
    payload = {
        # MESSAGE_TYPE: MESSAGE_TYPES.chat,
        FIELDS_CHAT_MESSAGE.authorname: data[FIELDS_CHAT_MESSAGE.authorname],
        FIELDS_CHAT_MESSAGE.authorid: data[FIELDS_CHAT_MESSAGE.authorid],
        FIELDS_CHAT_MESSAGE.roomid: data[FIELDS_CHAT_MESSAGE.roomid],
        FIELDS_CHAT_MESSAGE.target_userid: data[FIELDS_CHAT_MESSAGE.target_userid],
        FIELDS_CHAT_MESSAGE.message: data[FIELDS_CHAT_MESSAGE.message],
    }

    return json.dumps(payload)


def _serialize_chat_messages(messages: List[Dict[str, str]]) -> str:
    if isinstance(messages, dict):
        messages = [messages]

    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.chat,
        FIELDS_CHAT_MESSAGES.messages: messages,
    }

    return json.dumps(payload)


def _serialize_login_message(data: Dict) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.login,
        FIELDS_LOGIN_MESSAGE.username: data[FIELDS_LOGIN_MESSAGE.username],
        FIELDS_LOGIN_MESSAGE.password: data[FIELDS_LOGIN_MESSAGE.password],
    }

    return json.dumps(payload)


def _serialize_login_response_message(data: Dict) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.login_response,
        FIELDS_LOGIN_RESPONSE_MESSAGE.username: data[
            FIELDS_LOGIN_RESPONSE_MESSAGE.username
        ],
        FIELDS_LOGIN_RESPONSE_MESSAGE.userid: data[
            FIELDS_LOGIN_RESPONSE_MESSAGE.userid
        ],
    }

    return json.dumps(payload)


def _serialize_logout_message(data: Dict) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.logout,
        FIELDS_LOGOUT_MESSAGE.username: data[FIELDS_LOGOUT_MESSAGE.username],
        FIELDS_LOGOUT_MESSAGE.userid: data[FIELDS_LOGOUT_MESSAGE.userid],
    }

    return json.dumps(payload)


def _serialize_register_message(data: Dict) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.register,
        FIELDS_REGISTER_MESSAGE.username: data[FIELDS_REGISTER_MESSAGE.username],
        FIELDS_REGISTER_MESSAGE.password: data[FIELDS_REGISTER_MESSAGE.password],
    }

    return json.dumps(payload)


def _serialize_register_response_message(data: Dict) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.register_response,
        FIELDS_REGISTER_RESPONSE_MESSAGE.username: data[
            FIELDS_REGISTER_RESPONSE_MESSAGE.username
        ],
        FIELDS_REGISTER_RESPONSE_MESSAGE.status: data[
            FIELDS_REGISTER_RESPONSE_MESSAGE.status
        ],
    }

    return json.dumps(payload)


def _serialize_error_message(data: Dict) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.error,
        FIELDS_ERROR_MESSAGE.errortype: data[FIELDS_ERROR_MESSAGE.errortype],
        FIELDS_ERROR_MESSAGE.message: data[FIELDS_ERROR_MESSAGE.message],
    }

    return json.dumps(payload)
