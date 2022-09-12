# /networking/nonblocking/async_chat_client.py
from abc import ABC, abstractmethod
import asyncio
from datetime import datetime, timezone
import json
import os
from random import uniform
from typing import Coroutine
from common import (
    ENCODING,
    FIELDS_CHAT_MESSAGES,
    MESSAGE_TYPE,
    MESSAGE_TYPES,
    FIELDS_CHAT_MESSAGE,
    FIELDS_ERROR_MESSAGE,
    FIELDS_LOGIN_MESSAGE,
    FIELDS_LOGIN_RESPONSE_MESSAGE,
    FIELDS_LOGOUT_MESSAGE,
    FIELDS_REGISTER_MESSAGE,
    FIELDS_REGISTER_RESPONSE_MESSAGE,
)


def _async(coro: Coroutine):
    loop = asyncio.get_event_loop()
    return loop.create_task(coro)


class AbstractMessageHandler:
    @abstractmethod
    async def on_message_received(self, data: str) -> None:
        raise NotImplementedError

    async def on_connection_lost(self) -> None:
        return None

    async def on_close(self) -> None:
        return None


class AbstractChatClientProtocol(ABC):
    _is_connected: bool = False
    _message_handler: AbstractMessageHandler

    def __init__(self, host: str, port: int):
        self._host = host
        self._port = port
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def message_handler(self) -> AbstractMessageHandler:
        return self._message_handler

    @message_handler.setter
    def message_handler(self, message_handler: AbstractMessageHandler) -> None:
        self._message_handler = message_handler

    @abstractmethod
    async def connect(self) -> None:
        raise NotImplementedError("Protocols must implment connect")

    @abstractmethod
    async def send(self, data: str):
        raise NotImplementedError("Protocols must implement send method")

    @abstractmethod
    async def close(self):
        raise NotImplementedError("Protocols must implement close method")


class ChatClientProtocol(AbstractChatClientProtocol, asyncio.Protocol):
    _transport: asyncio.Transport

    async def connect(self):
        loop = asyncio.get_event_loop()
        await loop.create_connection(lambda: self, self._host, self._port)

    async def send(self, data: str):
        if data:
            message = data.encode(ENCODING)
            self._transport.write(message)

    async def close(self):
        self._transport.close()
        # add this
        self._is_connected = False

        if self.message_handler:
            await self.message_handler.on_close()

    def connection_made(self, transport: asyncio.Transport) -> None:
        self._transport = transport
        self._is_connected = True

    def connection_lost(self, exc: Exception | None) -> None:
        self._is_connected = False
        if self.message_handler:
            _async(self.message_handler.on_connection_lost())

    def data_received(self, data: bytes) -> None:
        message = data.decode(ENCODING)
        message_handler = self.message_handler
        if message_handler:
            _async(message_handler.on_message_received(message))


class TestProtocol(AbstractChatClientProtocol):

    delay: float = 0.5

    def __init__(self, *, delay: int = 0.5):
        self.delay = delay

    async def connect(self):
        loop = asyncio.get_event_loop()
        self._on_close = loop.create_future()
        self._is_connected = True

    async def send(self, data: str):
        await asyncio.sleep(self.delay)
        if data and self._is_connected and self.message_handler:
            message = json.loads(data)
            response: str = None
            message_type = message[MESSAGE_TYPE]

            if message_type == MESSAGE_TYPES.chat:
                response = data
            elif message_type == MESSAGE_TYPES.login:
                response = json.dumps(
                    {
                        MESSAGE_TYPE: MESSAGE_TYPES.login_response,
                        FIELDS_LOGIN_RESPONSE_MESSAGE.username: message.username,
                        FIELDS_LOGIN_RESPONSE_MESSAGE.userid: "1",
                    }
                )
            elif message_type == MESSAGE_TYPES.register:
                response = json.dumps(
                    {
                        MESSAGE_TYPE: MESSAGE_TYPES.register_response,
                        FIELDS_REGISTER_RESPONSE_MESSAGE.username: message.username,
                        FIELDS_REGISTER_RESPONSE_MESSAGE.status: "registered",
                    }
                )

            if response is None:
                return
            await self.message_handler.on_message_received(response)

    async def close(self):
        self._is_connected = False

        if self.message_handler:
            await self.message_handler.on_close()


class HighLevelProtocol(AbstractChatClientProtocol):
    _reader: asyncio.StreamReader | None = None
    _writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        loop = asyncio.get_event_loop()
        reader, writer = await asyncio.open_connection(host=self._host, port=self._port)
        self._reader = reader
        self._writer = writer
        self._is_connected = True
        loop.create_task(self.receive())

    async def send(self, data: str) -> None:
        if not self.is_connected or not self._writer:
            raise ConnectionError("Not connected to server")
        data = data.encode(ENCODING)
        self._writer.write(data)
        await self._writer.drain()

    async def close(self):
        if self._writer:
            self._writer.close()
            self._is_connected = False
            await self._writer.wait_closed()
            if self._message_handler:
                await self._message_handler.on_close()

    async def receive(self) -> str:
        if not self._reader:
            raise ConnectionError("Not connected to server")
        while self.is_connected:
            data = await self._reader.read(1024)
            if len(data) == 0:
                # disconnected?
                continue
            message = data.decode(ENCODING)
            if self._message_handler:
                await self._message_handler.on_message_received(message)


class HamletProtocol(AbstractChatClientProtocol):

    delay: float = 0.5
    hamlet: dict = None
    hamlet_started: bool = False

    def __init__(self, *, delay: int = 0.0):
        self.delay = delay
        base_path = os.path.dirname(os.path.abspath(__file__))
        in_path = os.path.join(base_path, "hamlet.json")

        with open(in_path, "r") as in_file:
            self.hamlet = json.loads(in_file.read())

    async def start_hamlet(self):
        messages = self.hamlet.get("hamlet", None)
        if messages is None or len(messages) == 0:
            return
        idx = 0
        while self._is_connected:
            delay = self.delay if self.delay > 0 else uniform(0.1, 5.0)
            await asyncio.sleep(delay)

            message = json.dumps(
                {
                    MESSAGE_TYPE: MESSAGE_TYPES.chat,
                    FIELDS_CHAT_MESSAGES.messages: [
                        {
                            FIELDS_CHAT_MESSAGE.username: messages[idx]["username"],
                            FIELDS_CHAT_MESSAGE.authorid: messages[idx]["userid"],
                            FIELDS_CHAT_MESSAGE.roomid: "1",
                            FIELDS_CHAT_MESSAGE.target_userid: None,
                            FIELDS_CHAT_MESSAGE.message: messages[idx]["message"],
                            FIELDS_CHAT_MESSAGE.createdate: datetime.now(
                                timezone.utc
                            ).isoformat(),
                        }
                    ],
                }
            )
            await self.message_handler.on_message_received(message)
            idx = (idx + 1) % len(messages)

    async def connect(self):
        self._is_connected = True

    async def send(self, data: str):
        await asyncio.sleep(self.delay)
        if data and self._is_connected and self.message_handler:
            message = json.loads(data)
            response: str = None
            message_type = message[MESSAGE_TYPE]

            if message_type == MESSAGE_TYPES.chat:
                response = data
                if not self.hamlet_started:
                    loop = asyncio.get_event_loop()
                    loop.create_task(self.start_hamlet())
                    self.hamlet_started = True
            elif message_type == MESSAGE_TYPES.login:
                response = json.dumps(
                    {
                        MESSAGE_TYPE: MESSAGE_TYPES.login_response,
                        FIELDS_LOGIN_RESPONSE_MESSAGE.username: message[
                            FIELDS_LOGIN_RESPONSE_MESSAGE.username
                        ],
                        FIELDS_LOGIN_RESPONSE_MESSAGE.userid: "1",
                    }
                )
            elif message_type == MESSAGE_TYPES.register:
                response = json.dumps(
                    {
                        MESSAGE_TYPE: MESSAGE_TYPES.register_response,
                        FIELDS_REGISTER_RESPONSE_MESSAGE.username: message[
                            FIELDS_REGISTER_RESPONSE_MESSAGE.username
                        ],
                        FIELDS_REGISTER_RESPONSE_MESSAGE.status: "registered",
                    }
                )

            if response is None:
                return
            await self.message_handler.on_message_received(response)

    async def close(self):
        self._is_connected = False

        if self.message_handler:
            await self.message_handler.on_close()
