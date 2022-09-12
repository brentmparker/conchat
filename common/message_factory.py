import json
from typing import Callable, Dict, List
from collections import namedtuple

_message_types = namedtuple(
    "MESSAGE_TYPES",
    [
        "chat",
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
    chat="message_chat",
    login="message_login",
    login_response="message_login_response",
    logout="message_logout",
    register="message_register",
    register_response="message_register_response",
    error="message_error",
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
"""_summary_

Returns:
    _type_: _description_
"""
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
    if message_type == MESSAGE_TYPES.chat:
        # return _serialize_chat_message
        return _serialize_chat_messages
    if message_type == MESSAGE_TYPES.login:
        return _serialize_login_message
    if message_type == MESSAGE_TYPES.login_response:
        return _serialize_login_response_message
    if message_type == MESSAGE_TYPES.logout:
        return _serialize_logout_message
    if message_type == MESSAGE_TYPES.register:
        return _serialize_register_message
    if message_type == MESSAGE_TYPES.register_response:
        return _serialize_register_response_message
    if message_type == MESSAGE_TYPES.error:
        return _serialize_error_message


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
