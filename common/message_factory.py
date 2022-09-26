import json
from typing import Dict, List
from collections import namedtuple

# Creating constants for client/server communication
_message_types = namedtuple(
    "MESSAGE_TYPES",
    [
        "chat",
        "blacklist",
        "blacklist_response",
        "create_room",
        "create_room_response",
        "join_room",
        "join_room_response",
        "list_rooms",
        "list_users",
        "login",
        "login_response",
        "logout",
        "register",
        "register_response",
        "error",
        "unblock",
        "unblock_response",
    ],
)

MESSAGE_TYPE = "message_type"
MESSAGE_TYPES = _message_types(
    blacklist="blacklist",
    blacklist_response="blacklist_response",
    chat="message_chat",
    create_room="create_room",
    create_room_response="create_room_response",
    error="message_error",
    join_room="join_room",
    join_room_response="join_room_response",
    list_rooms="list_rooms",
    list_users="list_users",
    login="message_login",
    login_response="message_login_response",
    logout="message_logout",
    register="message_register",
    register_response="message_register_response",
    unblock="unblock",
    unblock_response="unblock_response",
)

_fields_blacklist_message = namedtuple(
    "FIELDS_BLACKLIST_MESSAGE", ["userid", "blocked_username"]
)
_fields_create_room_message = namedtuple("FIELDS_CREATE_ROOM_MESSAGE", ["name"])
_fields_chat_message = namedtuple(
    "FIELDS_CHAT_MESSAGE",
    [
        "id",
        "authorname",
        "authorid",
        "target_username",
        "roomid",
        "target_userid",
        "message",
        "createdate",
    ],
)
_fields_chat_messages = namedtuple("CHAT_MESSAGES", ["messages"])
_fields_error_message = namedtuple("FIELDS_ERROR_MESSAGE", ["errortype", "message"])
_fields_join_room_message = namedtuple(
    "FIELDS_JOIN_ROOM_MESSAGE", ["userid", "roomname", "roomid"]
)
_fields_list_rooms_message = namedtuple("FIELDS_LIST_ROOMS_MESSAGE", ["rooms"])
_fields_list_users_message = namedtuple(
    "FIELDS_LIST_USERS_MESSAGE", ["roomname", "roomid", "users"]
)
_fields_login_message = namedtuple("FIELDS_LOGIN_MESSAGE", ["username", "password"])
_fields_login_response_message = namedtuple(
    "FIELDS_LOGIN_RESPONSE_MESSAGE", ["username", "userid", "roomid", "roomname"]
)
_fields_logout_message = namedtuple("FIELDS_LOGOUT_MESSAGE", ["username", "userid"])
_fields_register_response_message = namedtuple(
    "FIELDS_REGISTER_RESPONSE_MESSAGE", ["username", "status"]
)

FIELDS_BLACKLIST_MESSAGE = _fields_blacklist_message(
    userid="userid", blocked_username="blocked_username"
)
FIELDS_BLACKLIST_RESPONSE_MESSAGE = _fields_blacklist_message(
    userid="userid", blocked_username="blocked_username"
)
FIELDS_CHAT_MESSAGE = _fields_chat_message(
    id="id",
    authorname="authorname",
    roomid="roomid",
    target_userid="target_userid",
    target_username="target_username",
    message="message",
    authorid="authorid",
    createdate="createdate",
)
FIELDS_CHAT_MESSAGES = _fields_chat_messages(messages="messages")
FIELDS_CREATE_ROOM_MESSAGE = _fields_create_room_message(name="name")
FIELDS_CREATE_ROOM_RESPONSE_MESSAGE = _fields_create_room_message(name="name")
FIELDS_ERROR_MESSAGE = _fields_error_message(errortype="errortype", message="message")
FIELDS_JOIN_ROOM_MESSAGE = _fields_join_room_message(
    userid="userid", roomname="roomname", roomid="roomid"
)
FIELDS_JOIN_ROOM_RESPONSE_MESSAGE = _fields_join_room_message(
    userid="userid", roomname="roomname", roomid="roomid"
)
FIELDS_LIST_ROOMS_MESSAGE = _fields_list_rooms_message(rooms="rooms")
FIELDS_LIST_USERS_MESSAGE = _fields_list_users_message(
    roomid="roomid", roomname="roomname", users="users"
)
FIELDS_LOGIN_MESSAGE = _fields_login_message(username="username", password="password")
FIELDS_LOGIN_RESPONSE_MESSAGE = _fields_login_response_message(
    username="username", userid="id", roomid="roomid", roomname="roomname"
)
# logout message requires same fields as login response
FIELDS_LOGOUT_MESSAGE = _fields_logout_message(username="username", userid="id")
# registration requires same fields as login
FIELDS_REGISTER_MESSAGE = _fields_login_message(
    username="username", password="password"
)
FIELDS_REGISTER_RESPONSE_MESSAGE = _fields_register_response_message(
    username="username", status="status"
)
FIELDS_UNBLOCK_MESSAGE = _fields_blacklist_message(
    userid="userid", blocked_username="blocked_username"
)
FIELDS_UNBLOCK_RESPONSE_MESSAGE = _fields_blacklist_message(
    userid="userid", blocked_username="blocked_username"
)


def serialize_blacklist_message(userid: str, blocked_username: str) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.blacklist,
        FIELDS_BLACKLIST_MESSAGE.userid: userid,
        FIELDS_BLACKLIST_MESSAGE.blocked_username: blocked_username,
    }
    return json.dumps(payload)


def serialize_blacklist_response_message(
    userid: str, blocked_username: str
) -> str | None:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.blacklist_response,
        FIELDS_BLACKLIST_RESPONSE_MESSAGE.userid: userid,
        FIELDS_BLACKLIST_RESPONSE_MESSAGE.blocked_username: blocked_username,
    }
    return json.dumps(payload)


def serialize_chat(
    message: str,
    authorid: str,
    authorname: str,
    roomid: str = "",
    target_userid: str = "",
    target_username: str = "",
    createdate: str = "",
) -> Dict[str, str]:
    payload = {
        # MESSAGE_TYPE: MESSAGE_TYPES.chat,
        FIELDS_CHAT_MESSAGE.message: message,
        FIELDS_CHAT_MESSAGE.authorname: authorname,
        FIELDS_CHAT_MESSAGE.authorid: authorid,
        FIELDS_CHAT_MESSAGE.roomid: roomid,
        FIELDS_CHAT_MESSAGE.target_userid: target_userid,
        FIELDS_CHAT_MESSAGE.target_username: target_username,
        FIELDS_CHAT_MESSAGE.createdate: createdate,
    }

    return payload


def serialize_chat_messages(messages: List[Dict[str, str]] | None) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.chat,
        FIELDS_CHAT_MESSAGES.messages: messages,
    }

    return json.dumps(payload)


def serialize_create_room_message(name: str) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.create_room,
        FIELDS_CREATE_ROOM_MESSAGE.name: name,
    }

    return json.dumps(payload)


def serialzie_create_room_response_message(name: str) -> str:

    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.create_room_response,
        FIELDS_CREATE_ROOM_RESPONSE_MESSAGE.name: name,
    }

    return json.dumps(payload)


def serialize_error_message(errortype: str, message: str) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.error,
        FIELDS_ERROR_MESSAGE.errortype: errortype,
        FIELDS_ERROR_MESSAGE.message: message,
    }

    return json.dumps(payload)


def serialize_join_room_message(userid: str, roomname: str = "Lobby") -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.join_room,
        FIELDS_JOIN_ROOM_MESSAGE.userid: userid,
        FIELDS_JOIN_ROOM_MESSAGE.roomname: roomname,
    }

    return json.dumps(payload)


def serialize_join_room_response_message(
    userid: str, roomid: str, roomname: str = "Lobby"
) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.join_room_response,
        FIELDS_JOIN_ROOM_RESPONSE_MESSAGE.userid: userid,
        FIELDS_JOIN_ROOM_RESPONSE_MESSAGE.roomname: roomname,
        FIELDS_JOIN_ROOM_RESPONSE_MESSAGE.roomid: roomid,
    }

    return json.dumps(payload)


def serialize_list_rooms_message(room_names: List[str] | None = []) -> str:

    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.list_rooms,
        FIELDS_LIST_ROOMS_MESSAGE.rooms: room_names,
    }

    return json.dumps(payload)


def serialize_list_users_message(
    roomid: str, roomname: str, users: List[str] = []
) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.list_users,
        FIELDS_LIST_USERS_MESSAGE.roomid: roomid,
        FIELDS_LIST_USERS_MESSAGE.roomname: roomname,
        FIELDS_LIST_USERS_MESSAGE.users: users,
    }

    return json.dumps(payload)


def serialize_login_message(username: str, password: str) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.login,
        FIELDS_LOGIN_MESSAGE.username: username,
        FIELDS_LOGIN_MESSAGE.password: password,
    }

    return json.dumps(payload)


def serialize_login_response_message(
    userid: str, username: str, roomid: str, roomname: str
) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.login_response,
        FIELDS_LOGIN_RESPONSE_MESSAGE.username: username,
        FIELDS_LOGIN_RESPONSE_MESSAGE.userid: userid,
        FIELDS_LOGIN_RESPONSE_MESSAGE.roomid: roomid,
        FIELDS_LOGIN_RESPONSE_MESSAGE.roomname: roomname,
    }

    return json.dumps(payload)


def serialize_logout_message(userid: str, username: str) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.logout,
        FIELDS_LOGOUT_MESSAGE.username: username,
        FIELDS_LOGOUT_MESSAGE.userid: userid,
    }

    return json.dumps(payload)


def serialize_register_message(username: str, password: str) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.register,
        FIELDS_REGISTER_MESSAGE.username: username,
        FIELDS_REGISTER_MESSAGE.password: password,
    }

    return json.dumps(payload)


def serialize_register_response_message(username: str, status: str) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.register_response,
        FIELDS_REGISTER_RESPONSE_MESSAGE.username: username,
        FIELDS_REGISTER_RESPONSE_MESSAGE.status: status,
    }

    return json.dumps(payload)


def serialize_unblock_message(userid: str, blocked_username: str) -> str:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.unblock,
        FIELDS_BLACKLIST_MESSAGE.userid: userid,
        FIELDS_BLACKLIST_MESSAGE.blocked_username: blocked_username,
    }
    return json.dumps(payload)


def serialize_unblock_response_message(
    userid: str, blocked_username: str
) -> str | None:
    payload = {
        MESSAGE_TYPE: MESSAGE_TYPES.unblock_response,
        FIELDS_BLACKLIST_RESPONSE_MESSAGE.userid: userid,
        FIELDS_BLACKLIST_RESPONSE_MESSAGE.blocked_username: blocked_username,
    }
    return json.dumps(payload)
