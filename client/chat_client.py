import asyncio
from datetime import datetime, timezone
import json
from typing import List

import textual.events as events

from .ui.messages import (
    ChatMessage,
    Login,
    Logout,
    Register,
    Error,
    InvalidLogin,
    InvalidUsername,
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
)
from common import (
    User,
    ERRORS,
    MESSAGE_TYPE,
    message_factory,
    MESSAGE_TYPES,
    FIELDS_CHAT_MESSAGE,
    FIELDS_CHAT_MESSAGES,
    FIELDS_LOGIN_MESSAGE,
    FIELDS_LOGIN_RESPONSE_MESSAGE,
    FIELDS_LOGOUT_MESSAGE,
    FIELDS_REGISTER_MESSAGE,
    FIELDS_REGISTER_RESPONSE_MESSAGE,
    FIELDS_ERROR_MESSAGE,
)


class ChatApp(MultiviewApp, AbstractMessageHandler):

    _user: User = None
    _protocol = AbstractChatClientProtocol
    _messages: List[dict] = []

    def __init__(self, protocol: AbstractChatClientProtocol):
        self._protocol = protocol
        self._protocol.message_handler = self
        self._message_serializer = message_factory
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
        message = json.loads(data)
        message_type = message[MESSAGE_TYPE]
        if message_type == MESSAGE_TYPES.chat:
            await self.add_messages(message)
        elif message_type == MESSAGE_TYPES.login_response:
            self._user = User(
                username=message[FIELDS_LOGIN_RESPONSE_MESSAGE.username],
                userid=message[FIELDS_LOGIN_RESPONSE_MESSAGE.userid],
            )
            await self.swap_to_view("chatView")
            await self._chat_view.clear_history()
            await self._chat_view.add_history_messages(self._messages, self._user)
        elif message_type == MESSAGE_TYPES.register_response:
            await self.swap_to_view("signinView")
        elif message_type == MESSAGE_TYPES.error:
            error_type = message[FIELDS_ERROR_MESSAGE.errortype]
            if error_type == ERRORS.invalid_username_password and isinstance(
                self.view, SigninView
            ):
                await self.view.handle_invalid_login(InvalidLogin(self))
            elif error_type == ERRORS.username_exists and isinstance(
                self.view, SignupView
            ):
                await self.view.handle_invalid_username(InvalidUsername(self))

    async def on_connection_lost(self) -> None:
        pass

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

        data = {
            FIELDS_CHAT_MESSAGE.authorname: self._user.username,
            FIELDS_CHAT_MESSAGE.authorid: self._user.userid,
            FIELDS_CHAT_MESSAGE.roomid: "1",
            FIELDS_CHAT_MESSAGE.message: message,
        }
        data = self._message_serializer([data], MESSAGE_TYPES.chat)
        await self.protocol.send(data)

    async def handle_login(self, event: Login):
        username = event.username.strip()
        password = event.password.strip()
        if len(username) == 0 or len(password) == 0:
            return
        data = {
            FIELDS_LOGIN_MESSAGE.username: username,
            FIELDS_LOGIN_MESSAGE.password: password,
        }
        data = self._message_serializer(data, MESSAGE_TYPES.login)
        await self.protocol.send(data)

    async def handle_logout(self, event: Logout):
        if self._user is None:
            return
        data = {
            FIELDS_LOGOUT_MESSAGE.userid: self._user.userid,
            FIELDS_LOGOUT_MESSAGE.username: self._user.username,
        }
        data = self._message_serializer(data, MESSAGE_TYPES.logout)
        await self.protocol.send(data)

    async def handle_register(self, event: Register):
        username = event.username.strip()
        password = event.password.strip()
        if len(username) == 0 or len(password) == 0:
            return

        data = {
            FIELDS_REGISTER_MESSAGE.username: username,
            FIELDS_REGISTER_MESSAGE.password: password,
        }
        data = self._message_serializer(data, MESSAGE_TYPES.register)
        await self.protocol.send(data)

    async def handle_error(self, event: Error):
        pass


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
