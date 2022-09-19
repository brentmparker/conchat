from __future__ import annotations
import asyncio
import json
import logging
from typing import Any, Coroutine, Dict, List
from .chat_server_protocol import (
    AbstractChatServer,
    AbstractChatConnection,
    Chatroom,
)
from .database_protocol import AbstractDatabase
from .sqlite_database import SqliteDatabase
from common import (
    ENCODING,
    User,
    MESSAGE_TYPE,
    MESSAGE_TYPES,
    FIELDS_CHAT_MESSAGE,
    FIELDS_CHAT_MESSAGES,
    FIELDS_ERROR_MESSAGE,
    FIELDS_LOGIN_MESSAGE,
    FIELDS_LOGIN_RESPONSE_MESSAGE,
    FIELDS_LOGOUT_MESSAGE,
    FIELDS_REGISTER_MESSAGE,
    FIELDS_REGISTER_RESPONSE_MESSAGE,
)


class ChatServerConnection(AbstractChatConnection, asyncio.Protocol):
    parent: ChatServer | None = None

    def __init__(self, parent: ChatServer):
        super().__init__(None, None)
        self.parent = parent
        self.conn: asyncio.WriteTransport = None

    # Called when we accept a new connection
    def connection_made(self, transport: asyncio.WriteTransport):
        peername = transport.get_extra_info("peername")
        logging.info(f"Connection from {peername}")
        self.conn = transport
        self.parent.add_connection(self)

    # Called when new data is incoming
    def data_received(self, data: bytes) -> None:
        message = data.decode(ENCODING)
        logging.info(f"Data received: {message}")

        asyncio.create_task(self.parent.handle_message(message, self))

    # Called when a connection is closed or there is an error
    def connection_lost(self, exc: Exception):
        self.parent.remove_connection(self)
        peername = self.conn.get_extra_info("peername")
        logging.info(f"Lost connection from {peername}.")
        return super().connection_lost(exc)

    def send(self, message: Dict[str, str]) -> None:
        pass

    def close(self):
        pass


class ChatServer(AbstractChatServer):
    def __init__(self, db: AbstractDatabase) -> None:
        super().__init__(db)

    async def handle_message(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        logging.info("Handling message: %s", message)

        match message[MESSAGE_TYPE]:
            case MESSAGE_TYPES.register:
                pass
            case MESSAGE_TYPES.login:
                pass
            case MESSAGE_TYPES.chat:
                pass
            case _:
                pass

    async def forward_to_room(self, message: Dict[str, str], roomid: str) -> None:
        pass

    async def forward_to_user(self, message: Dict[str, str], userid: str) -> None:
        pass

    def add_connection(self, conn: ChatServerConnection) -> None:
        pass

    def remove_connection(self, conn: ChatServerConnection) -> None:
        pass

    def _cleanup_rooms(self) -> None:
        pass

    def _create_proto(self) -> asyncio.BaseProtocol:
        proto = ChatServerConnection(parent=self)
        return proto

    def start(self, host: str, port: int):
        async def _run_server():
            loop = asyncio.get_event_loop()

            server = await loop.create_server(lambda: self._create_proto(), host, port)
            logging.info("Starting server at %s:%s", host, port)

            async with server:
                try:
                    await server.serve_forever()
                except Exception as e:
                    logging.debug("Error: %s", e)
                finally:
                    logging.info("Exiting server")

        asyncio.run(_run_server())


def run_server(host: str = "127.0.0.1", port: int = 5001):
    # Setup logger
    logging.basicConfig(filename="server.log", level=logging.DEBUG, filemode="w")

    db = SqliteDatabase()
    db._initialize_database()
    server = ChatServer(db=db)
    try:
        server.start(host=host, port=port)
    except KeyboardInterrupt as e:
        logging.debug("ctrl+c: %s", e)


if __name__ == "__main__":
    run_server()
