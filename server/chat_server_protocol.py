from __future__ import annotations
from abc import ABC, abstractmethod
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
    def send(self, message: Dict[str, str]) -> None:
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
    roomid: str

    def __init__(self, roomid: str) -> None:
        if roomid is None:
            raise ValueError("roomid can not be None")
        self.roomid = roomid
        self.connections = []

    async def forward_to_room(self, message: str) -> None:
        for connection in self.connections:
            connection.send(message)

    def join_room(self, conn: AbstractChatConnection) -> None:
        if conn.room.roomid != self.roomid:
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

        # Get lobby for new users
        l = self._db.get_room_by_name("Lobby")
        if l is None:
            raise ValueError("Could not find lobby")

        self.lobby = Chatroom(l["id"])
        self.rooms[l["id"]] = self.lobby

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
