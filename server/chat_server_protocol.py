from __future__ import annotations
from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, List
from common import User, ENCODING
from .database_protocol import AbstractDatabase


class AbstractChatConnection(ABC):
    _is_closed: bool = False
    _room: Chatroom | None
    user: User | None
    conn: Any | None

    def __init__(self, user: User | None, conn: Any) -> None:
        self.user = user
        self.conn = conn
        self._room = None

    @property
    def closed(self) -> bool:
        return self._is_closed

    @abstractmethod
    async def send(self, message: str) -> None:
        pass

    @abstractmethod
    def close(self):
        pass

    @property
    def room(self) -> Chatroom:
        return self._room

    @room.setter
    def room(self, room: Chatroom | None):
        if self._room is not None:
            self._room.leave_room(self)
        self._room = room


class Chatroom:
    connections: List[AbstractChatConnection]
    id: str
    name: str

    def __init__(self, roomid: str, roomname: str) -> None:
        if roomid is None:
            raise ValueError("roomid can not be None")
        self.id = roomid
        self.name = roomname
        self.connections = []

    async def forward_to_room(self, message: str) -> None:
        for connection in self.connections:
            await connection.send(message)

    def join_room(self, conn: AbstractChatConnection) -> None:
        if conn.room is None or conn.room.id != self.id:
            conn.room = self

        if conn in self.connections:
            return

        self.connections.append(conn)

    def leave_room(self, conn: AbstractChatConnection) -> None:
        if conn not in self.connections:
            return
        self.connections.remove(conn)
        conn.room = None


class AbstractChatServer(ABC):

    connections: List[AbstractChatConnection] | None = None
    user_connections: Dict[str, AbstractChatConnection] | None = None
    rooms: Dict[str, Chatroom] | None = None
    lobby: Chatroom | None = None
    _db: AbstractDatabase | None = None

    def __init__(self, db: AbstractDatabase) -> None:
        if db is None:
            raise ValueError("Database can not be None")
        self._db = db
        self.rooms = {}
        self.user_connections = {}
        self.connections = []

        lobby_data: Dict[str, str] | None = None

        # Get lobby for new users
        try:
            lobby_data = self._db.get_room_by_name("Lobby")
        except Exception as e:
            logging.error("Could not find lobby. No default room. Exiting chat server.")
            raise Exception(e)
        if lobby_data is None:
            raise ValueError("Could not find lobby")

        self.lobby = Chatroom(lobby_data["id"], lobby_data["name"])
        self.rooms[lobby_data["id"]] = self.lobby

        super().__init__()

    @abstractmethod
    async def handle_message(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        pass

    @abstractmethod
    async def forward_to_room(self, message: Dict[str, str], roomid: str) -> None:
        pass

    @abstractmethod
    async def forward_to_user(self, message: Dict[str, str], userid: str) -> None:
        pass

    def remove_connection(self, conn: AbstractChatConnection) -> None:
        pass
