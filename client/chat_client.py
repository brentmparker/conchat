from __future__ import annotations
import asyncio
from datetime import datetime, timezone
import json
from typing import Dict, List

import textual.events as events

from .ui.messages import (
    ChatMessage,
    CommandMessage,
    ListRoomsMessage,
    ListUsersMessage,
    Login,
    Logout,
    Register,
    ErrorMessage,
    InvalidLogin,
    InvalidUsername,
    ServerResponseMessage,
)

from .ui import MultiviewApp
from .ui.views import ChatView, IntroView, SigninView, SignupView

from .chat_client_protocol import (
    AbstractMessageHandler,
    AbstractChatClientProtocol,
    TestProtocol,
    ChatClientProtocol,
    HighLevelProtocol,
    HamletProtocol,
    Chatroom,
)
from common import (
    User,
    COMMAND_TYPES,
    ERRORS,
    ERROR_TYPES,
    FIELDS_BLACKLIST_RESPONSE_MESSAGE,
    FIELDS_CREATE_ROOM_RESPONSE_MESSAGE,
    FIELDS_JOIN_ROOM_RESPONSE_MESSAGE,
    FIELDS_LIST_USERS_MESSAGE,
    FIELDS_CHAT_MESSAGES,
    FIELDS_LIST_ROOMS_MESSAGE,
    FIELDS_LOGIN_RESPONSE_MESSAGE,
    FIELDS_ERROR_MESSAGE,
    FIELDS_UNBLOCK_RESPONSE_MESSAGE,
    MESSAGE_TYPE,
    MESSAGE_TYPES,
    serialize_blacklist_message,
    serialize_chat,
    serialize_chat_messages,
    serialize_create_room_message,
    serialize_join_room_message,
    serialize_list_rooms_message,
    serialize_list_users_message,
    serialize_login_message,
    serialize_logout_message,
    serialize_register_message,
    serialize_unblock_message,
)


class ChatApp(MultiviewApp, AbstractMessageHandler):

    _user: User = None
    _protocol = AbstractChatClientProtocol
    _messages: List[dict] = []
    _room: Chatroom | None = None

    def __init__(self, protocol: AbstractChatClientProtocol):
        self._protocol = protocol
        self._protocol.message_handler = self
        super().__init__(title="Chat App", log="log.log")

    @property
    def protocol(self):
        return self._protocol

    @protocol.setter
    def protocol(self, protocol: ChatClientProtocol):
        self._protocol = protocol

    async def on_load(self, event: events.Load) -> None:
        await self._protocol.connect()
        await self.bind("escape", "quit", "Quit")

    async def on_mount(self, event: events.Mount) -> None:

        self.app.title = "Conchat"
        self._intro_view = IntroView(name="introView")
        self._signin_view = SigninView(name="signinView")
        self._signup_view = SignupView(name="signupView")
        self._chat_view = ChatView(name="chatView")

        await self._intro_view.init()
        await self._signin_view.init()
        await self._signup_view.init()
        await self._chat_view.init()

        self.add_view(self._intro_view)
        self.add_view(self._signin_view)
        self.add_view(self._signup_view)
        self.add_view(self._chat_view)
        # await self.swap_to_view("chatView")
        await self.swap_to_view("introView")

    async def add_messages(self, message: dict):
        self._messages.append(message[FIELDS_CHAT_MESSAGES.messages])

        if not isinstance(self.view, ChatView):
            return

        await self.view.add_history_messages(
            message[FIELDS_CHAT_MESSAGES.messages], self._user
        )

    async def on_message_received(self, data: str):
        self.log("Received data:\n", data)
        message = json.loads(data)
        match message[MESSAGE_TYPE]:
            case MESSAGE_TYPES.blacklist_response:
                await self.handle_blacklist_response_message(message)
            case MESSAGE_TYPES.chat:
                await self.handle_chat_message(message)
            case MESSAGE_TYPES.create_room_response:
                await self.handle_create_room_response_message(message)
            case MESSAGE_TYPES.error:
                await self.handle_error_message(message)
            case MESSAGE_TYPES.join_room_response:
                await self.handle_join_room_response_message(message)
            case MESSAGE_TYPES.list_rooms:
                await self.handle_list_rooms(message)
            case MESSAGE_TYPES.list_users:
                await self.handle_list_users(message)
            case MESSAGE_TYPES.login_response:
                await self.handle_login_response(message)
            case MESSAGE_TYPES.register_response:
                await self.handle_register_response(message)
            case MESSAGE_TYPES.unblock_response:
                await self.handle_unblock_response(message)

    async def handle_blacklist_response_message(self, message: Dict[str, str]) -> None:
        if self.view != self._chat_view:
            return

        blocked_username = message.get(
            FIELDS_BLACKLIST_RESPONSE_MESSAGE.blocked_username
        ).strip()
        if len(blocked_username) == 0:
            return

        server_response_message = ServerResponseMessage(
            self, f"You blocked {blocked_username}"
        )
        await self._chat_view.handle_server_response(server_response_message)

    async def handle_chat_message(self, message: Dict[str, str]) -> None:
        await self.add_messages(message)

    async def handle_create_room_response_message(
        self, message: Dict[str, str]
    ) -> None:
        if self.view != self._chat_view:
            return
        name = message.get(FIELDS_CREATE_ROOM_RESPONSE_MESSAGE.name, "").strip()
        if len(name) == 0:
            return
        server_response_message = ServerResponseMessage(self, f"Room {name} created.")
        await self._chat_view.handle_server_response(server_response_message)

    async def handle_join_room_response_message(self, message: Dict[str, str]) -> None:
        userid = message.get(FIELDS_JOIN_ROOM_RESPONSE_MESSAGE.userid, "").strip()
        roomid = message.get(FIELDS_JOIN_ROOM_RESPONSE_MESSAGE.roomid, "").strip()
        roomname = message.get(FIELDS_JOIN_ROOM_RESPONSE_MESSAGE.roomname, "").strip()
        if len(userid) == 0 or userid != self._user.userid:
            return
        if len(roomid) == 0 or self._room.id == roomid:
            return
        if len(roomname) == 0:
            return

        self._messages.clear()
        await self._chat_view.clear_history()

        self._room.id = roomid
        self._room.name = roomname

        self.app.title = roomname

        if self.view != self._chat_view:
            await self.swap_to_view("chatView")

    async def handle_list_rooms(self, message: Dict[str, str]) -> None:
        rooms = message.get(FIELDS_LIST_ROOMS_MESSAGE.rooms, None)
        if rooms is None:
            return

        if self.view != self._chat_view:
            return

        list_message: ListRoomsMessage = ListRoomsMessage(self, rooms)
        await self._chat_view.handle_list_rooms(list_message)

    async def handle_list_users(self, message: Dict[str, str]) -> None:
        users: List[str] = message.get(FIELDS_LIST_USERS_MESSAGE.users, None)
        if users is None:
            return

        if self.view != self._chat_view:
            return

        users.sort()

        list_users: ListUsersMessage = ListUsersMessage(self, users)
        await self._chat_view.handle_list_users(list_users)

    async def handle_login_response(self, message: Dict[str, str]) -> None:
        self._messages.clear()
        await self._chat_view.clear_history()
        username = message.get(FIELDS_LOGIN_RESPONSE_MESSAGE.username, "").strip()
        userid = message.get(FIELDS_LOGIN_RESPONSE_MESSAGE.userid, "").strip()
        roomid = message.get(FIELDS_LOGIN_RESPONSE_MESSAGE.roomid, "").strip()
        roomname = message.get(FIELDS_LOGIN_RESPONSE_MESSAGE.roomname, "").strip()

        if len(userid) == 0 or len(roomid) == 0:
            return

        self._user = User(
            username=username,
            userid=userid,
        )
        self._room = Chatroom(
            id=roomid,
            name=roomname,
        )

        self.app.sub_title = username

        await self.swap_to_view("chatView")
        await self._chat_view.clear_history()
        # await self._chat_view.add_history_messages(self._messages, self._user)

    async def handle_register_response(self, message: Dict[str, str]) -> None:
        await self.swap_to_view("signinView")

    async def handle_unblock_response(self, message: Dict[str, str]) -> None:
        if self.view != self._chat_view:
            return

        blocked_username = message.get(
            FIELDS_UNBLOCK_RESPONSE_MESSAGE.blocked_username
        ).strip()
        if len(blocked_username) == 0:
            return

        server_response_message = ServerResponseMessage(
            self, f"You unblocked {blocked_username}"
        )
        await self._chat_view.handle_server_response(server_response_message)

    async def handle_error_message(self, message: Dict[str, str]) -> None:
        error_type = message[FIELDS_ERROR_MESSAGE.errortype]
        if error_type == ERRORS.invalid_username_password and isinstance(
            self.view, SigninView
        ):
            await self.view.handle_invalid_login(InvalidLogin(self))
        elif error_type == ERRORS.username_exists and isinstance(self.view, SignupView):
            await self.view.handle_invalid_username(InvalidUsername(self))
        else:
            error = ErrorMessage(
                self,
                message[FIELDS_ERROR_MESSAGE.errortype],
                message[FIELDS_ERROR_MESSAGE.message],
            )
            await self.view.handle_error(error)

    async def handle_command(self, command: CommandMessage):
        match command.command_type:
            case COMMAND_TYPES.block:
                await self.handle_command_block(command.command_data)
            case COMMAND_TYPES.create_room:
                await self.handle_command_create_room(command.command_data)
            case COMMAND_TYPES.dm:
                await self.handle_command_dm(command.command_data)
            case COMMAND_TYPES.join_room:
                await self.handle_command_join_room(command.command_data)
            case COMMAND_TYPES.list_rooms:
                await self.handle_command_list_rooms()
            case COMMAND_TYPES.list_users:
                await self.handle_command_list_users()
            case COMMAND_TYPES.logout:
                await self.handle_command_logout()
            case COMMAND_TYPES.unblock:
                await self.handle_command_unblock(command.command_data)

    async def handle_command_block(self, command_data: str) -> None:
        userid = self._user.userid
        blocked_username = command_data.strip()
        if len(blocked_username) == 0:
            return
        payload = serialize_blacklist_message(userid, blocked_username)
        await self.protocol.send(payload)

    async def handle_command_dm(self, command_data: str) -> None:
        m = command_data.split(maxsplit=1)
        if len(m) < 2:
            error_msg = ErrorMessage(
                self,
                ERROR_TYPES.invalid_message_target,
                "Must type a valid username and a message",
            )
            return await self._chat_view.handle_error(error_msg)
        target_username = m[0].strip()
        content = m[1].strip()
        if len(target_username) == 0 or len(content) == 0:
            error_msg = ErrorMessage(
                self,
                ERROR_TYPES.invalid_message_target,
                "Must type a valid username and a message",
            )
            return await self._chat_view.handle_error(error_msg)
        chat_message = serialize_chat(
            message=content,
            authorid=self._user.userid,
            authorname=self._user.username,
            roomid="",
            target_userid="",
            target_username=target_username,
        )

        payload = serialize_chat_messages([chat_message])
        await self.protocol.send(payload)

    async def handle_command_create_room(self, command_data: str) -> None:
        if command_data is None or len(command_data) == 0:
            error_msg = ErrorMessage(
                self, ERROR_TYPES.invalid_room, "Must type a room name"
            )
            return await self._chat_view.handle_error(error_msg)

        payload = serialize_create_room_message(command_data)
        await self.protocol.send(payload)

    async def handle_command_join_room(self, command_data: str) -> None:
        payload = serialize_join_room_message(self._user.userid, command_data)
        await self.protocol.send(payload)

    async def handle_command_list_rooms(self) -> None:
        payload = serialize_list_rooms_message()
        await self.protocol.send(payload)

    async def handle_command_list_users(self) -> None:
        payload = serialize_list_users_message(self._room.id, self._room.name)
        await self.protocol.send(payload)

    async def handle_command_logout(self) -> None:
        payload = serialize_logout_message(self._user.userid, self._user.username)
        await self.protocol.send(payload)
        self._user = None
        await self.swap_to_view("introView")

    async def handle_command_unblock(self, command_data: str) -> None:
        userid = self._user.userid
        blocked_username = command_data.strip()
        if len(blocked_username) == 0:
            return
        payload = serialize_unblock_message(userid, blocked_username)
        await self.protocol.send(payload)

    async def on_connection_lost(self) -> None:
        error = ErrorMessage(self, ERROR_TYPES.server_error, "Connection lost")
        await self.view.handle_error(error)
        await asyncio.sleep(2)
        shutdown = events.ShutdownRequest(self)
        await self.on_shutdown_request(shutdown)

    async def on_close(self) -> None:
        pass

    async def on_shutdown_request(self, event: events.ShutdownRequest) -> None:
        await self.protocol.close()
        return await super().on_shutdown_request(event)

    async def on_chat(self, event: ChatMessage) -> None:
        event.prevent_default().stop()
        if self._user is None:
            return
        message = event.message.strip()
        if len(message) == 0:
            return

        if self._room is None:
            return

        chat_message = serialize_chat(
            message=message,
            authorid=self._user.userid,
            authorname=self._user.username,
            roomid=self._room.id,
        )

        payload = serialize_chat_messages([chat_message])
        await self.protocol.send(payload)

    async def handle_login(self, event: Login):
        username = event.username.strip()
        password = event.password.strip()
        if len(username) == 0 or len(password) == 0:
            return

        payload = serialize_login_message(username, password)
        await self.protocol.send(payload)

    async def handle_logout(self, event: Logout):
        if self._user is not None:
            payload = serialize_logout_message(self._user.userid, self._user.username)
            await self.protocol.send(payload)
            self._user = None
        self.app.sub_title = None
        await self._chat_view.clear_history()
        await self.swap_to_view("introView")

    async def handle_register(self, event: Register):
        username = event.username.strip()
        password = event.password.strip()
        if len(username) == 0 or len(password) == 0:
            return

        payload = serialize_register_message(username, password)
        await self.protocol.send(payload)


def run_client(
    host: str = "127.0.0.1",
    port: int = 5001,
    *,
    test: bool = False,
    protocol_type: str = "basic",
):
    async def _run_client(host, port):
        protocol: ChatClientProtocol = None
        if test:
            if protocol_type == "hamlet":
                print("Starting with hamlet protocol")
                protocol = HamletProtocol(delay=0.5)
            else:
                print("Starting with test protocol")
                protocol = TestProtocol(delay=0.25)
        else:
            if protocol_type == "high":
                print("Starting with high-level protocol")
                protocol = HighLevelProtocol(host=host, port=port)
            else:
                print("Starting with ChatClientProtocol")
                protocol = ChatClientProtocol(host=host, port=port)
        app = ChatApp(protocol=protocol)
        await app.process_messages()

    asyncio.run(_run_client(host, port))


if __name__ == "__main__":
    run_client()
