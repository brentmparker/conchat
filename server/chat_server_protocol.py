# /networking/nonblocking/async_chat_server.py
from abc import ABC, abstractmethod
import asyncio
import json
from typing import Any, Dict, List
from common import User, ENCODING


class AbstractChatConnection(ABC):
    def __init__(self, user: User | None, conn: Any) -> None:
        self.user = user
        self.conn = conn

    @abstractmethod
    def send(self, message: Dict[str, str]) -> None:
        pass

    @abstractmethod
    def close(self):
        pass


class ChatProtocolConnection(AbstractChatConnection):
    def __init__(self, user: User | None, conn: asyncio.BaseTransport) -> None:
        self.user = user
        self.conn = conn

    def send(self, message: Dict[str, str]) -> None:
        data = json.dumps(message)
        self.conn.write(data.encode(ENCODING))

    def close(self):
        self.conn.close()


class Chatroom:
    connections: List[AbstractChatConnection]
    roomid: str

    async def forward_to_room(self, message: str) -> None:
        for connection in self.connections:
            connection.send(message)

    def join_room(self, conn: AbstractChatConnection) -> None:
        if conn in self.connections:
            return

        self.connections.append(conn)

    def leave_room(self, conn: AbstractChatConnection) -> None:
        self.connections = [c for c in self.connections if c.user != conn.user]


class AbstractChatServerProtocol(ABC):

    connections: List[AbstractChatConnection]
    rooms: List[Chatroom]

    async def handle_message(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        pass

    async def forward_to_room(self, message: Dict[str, str], room: Chatroom) -> None:
        pass

    async def forward_to_user(self, message: Dict[str, str], user: User) -> None:
        pass


# Changes:
# add transports above __init__ for typing
class ChatServerProtocol(asyncio.Protocol):
    _transports: List[asyncio.BaseTransport] | None = None

    def __init__(self, transports: List[asyncio.BaseTransport]):
        super().__init__()
        self._transports = transports
        self._transport: asyncio.BaseTransport = None

    # Called when we accept a new connection
    def connection_made(self, transport: asyncio.BaseTransport):
        peername = transport.get_extra_info("peername")
        print(f"Connection from {peername}")
        self._transport = transport
        self._transports.append(transport)

    # Called when new data is incoming
    def data_received(self, data: bytes) -> None:
        message = data.decode(ENCODING)
        print(f"Data received: {message}")

        self.broadcast_message(message)

    def broadcast_message(self, message: str):
        for transport in self._transports:
            transport.write(message.encode(ENCODING))

    # Called when a connection is closed or there is an error
    def connection_lost(self, exc: Exception):
        self._transports.remove(self._transport)
        peername = self._transport.get_extra_info("peername")
        print(f"Lost connection from {peername}.")
        return super().connection_lost(exc)


def run_server(host: str = "127.0.0.1", port: int = 5001):
    async def _run_server(host: str, port: int):

        loop = asyncio.get_event_loop()

        transports: List[asyncio.BaseTransport] = []
        server = await loop.create_server(
            lambda: ChatServerProtocol(transports), host, port
        )

        async with server:
            try:
                await server.serve_forever()
            except KeyboardInterrupt as e:
                pass
            finally:
                print("Exiting server")

    asyncio.run(_run_server(host=host, port=port))


if __name__ == "__main__":
    run_server()
