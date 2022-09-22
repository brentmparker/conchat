from __future__ import annotations
import asyncio
import json
import logging
from msilib.schema import Error
from multiprocessing.sharedctypes import Value
from nis import cat
import bcrypt
from typing import Any, Callable, Coroutine, Dict, List
from .chat_server_protocol import (
    AbstractChatServer,
    AbstractChatConnection,
    Chatroom,
)
from .database_protocol import AbstractDatabase, DBConnectionError
from .sqlite_database import SqliteDatabase
from common import (
    ENCODING,
    ERRORS,
    ERROR_TYPES,
    User,
    MESSAGE_TYPE,
    MESSAGE_TYPES,
    FIELDS_BLACKLIST_MESSAGE,
    FIELDS_CREATE_ROOM_MESSAGE,
    FIELDS_CHAT_MESSAGE,
    FIELDS_CHAT_MESSAGES,
    FIELDS_ERROR_MESSAGE,
    FIELDS_JOIN_ROOM_MESSAGE,
    FIELDS_LIST_ROOMS_MESSAGE,
    FIELDS_LOGIN_MESSAGE,
    FIELDS_LOGIN_RESPONSE_MESSAGE,
    FIELDS_LOGOUT_MESSAGE,
    FIELDS_REGISTER_MESSAGE,
    FIELDS_REGISTER_RESPONSE_MESSAGE,
    message_factory,
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
        message = json.loads(data.decode(ENCODING))
        logging.debug(f"Data received: {message}")

        asyncio.create_task(self.parent.handle_message(message, self))

    # Called when a connection is closed or there is an error
    def connection_lost(self, exc: Exception):
        self.parent.remove_connection(self)
        peername = self.conn.get_extra_info("peername")
        logging.info(f"Lost connection from {peername}.")
        return super().connection_lost(exc)

    async def send(self, message: str) -> None:
        if message is None:
            return
        if self.closed:
            return

        try:
            self.conn.write(message.encode(ENCODING))
        except Exception as e:
            logging.error("Error sending message: %s", e)

    def close(self):
        if self.closed:
            return

        try:
            self.conn.close()
        except Exception as e:
            logging.error("Error closing connection: %s", e)
        finally:
            self.parent.remove_connection(self)
            self._is_closed = True


class ChatServer(AbstractChatServer):
    def __init__(self, db: AbstractDatabase) -> None:
        super().__init__(db)

    async def handle_message(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        logging.info("Handling message: %s", message)

        match message[MESSAGE_TYPE]:
            case MESSAGE_TYPES.blacklist:
                await self.handle_blacklist(message, source)
            case MESSAGE_TYPES.list_rooms:
                await self.handle_list_rooms(message, source)
            case MESSAGE_TYPES.join_room:
                await self.handle_join_room(message, source)
            case MESSAGE_TYPES.create_room:
                await self.handle_create_room(message, source)
            case MESSAGE_TYPES.register:
                await self.handle_register(message, source)
            case MESSAGE_TYPES.login:
                await self.handle_login(message, source)
            case MESSAGE_TYPES.logout:
                await self.handle_logout(message, source)
            case MESSAGE_TYPES.chat:
                await self.handle_chat(message, source)
            case _:
                pass

    async def forward_to_room(self, message: Dict[str, str], roomid: str) -> None:
        room = self.rooms.get(roomid, None)
        if room is None:
            return

        await room.forward_to_room(message)

    async def forward_to_user(self, message: Dict[str, str], userid: str) -> None:
        user = self.user_connections.get(userid, None)
        if user is None:
            return

        await user.send(message)

    async def handle_register(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:

        username = message.get(FIELDS_REGISTER_MESSAGE.username, "").strip()
        password = message.get(FIELDS_REGISTER_MESSAGE.password, "").strip()

        if len(username) == 0 or len(password) == 0:
            logging.error("Missing field in register message: %s", e)
            await self.handle_error(
                ERROR_TYPES.invalid_username_password,
                ERRORS.invalid_username_password,
                source,
            )

        # Add user to database
        # Get back user with userid
        user: Dict[str, str] | None = None
        try:
            pwhash = bcrypt.hashpw(password.encode(ENCODING), bcrypt.gensalt())
            user = self._db.insert_user(username, pwhash)
        except DBConnectionError as e:
            await self.handle_error(
                ERROR_TYPES.server_error, ERRORS.server_error, source
            )
        except Exception as e:
            logging.error("Error registering user: %s", e)
            await self.handle_error(
                ERROR_TYPES.username_exists, ERRORS.username_exists, source
            )

        if user is None:
            await self.handle_error(ERROR_TYPES.server_error, ERRORS.server_error)

        data = {
            FIELDS_REGISTER_RESPONSE_MESSAGE.username: user["username"],
            FIELDS_REGISTER_RESPONSE_MESSAGE.status: "registered",
        }
        message = message_factory(data, MESSAGE_TYPES.register_response)
        await source.send(message)

    async def handle_login(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:

        username = message.get(FIELDS_REGISTER_MESSAGE.username, "").strip()
        password = message.get(FIELDS_REGISTER_MESSAGE.password, "").strip()

        if len(username) == 0 or len(password) == 0:
            logging.error("Missing field in register message: %s", e)
            await self.handle_error(
                ERROR_TYPES.invalid_username_password,
                ERRORS.invalid_username_password,
                source,
            )

        # select user from database
        user: Dict[str, str] | None = None
        try:
            user = self._db.get_user_by_username(username)
        except DBConnectionError as e:
            await self.handle_error(
                ERROR_TYPES.server_error, ERRORS.server_error, source
            )
            return

        if user is None:
            await self.handle_error(
                ERROR_TYPES.invalid_username_password, ERRORS.invalid_username_password
            )
            return

        # Validate password
        pwhash = user["password"]
        if not bcrypt.checkpw(password.encode(ENCODING), pwhash.encode(ENCODING)):
            await self.handle_error(
                ERROR_TYPES.invalid_username_password, ERRORS.invalid_username_password
            )

        # Send login response
        source.user = User(user["id"], user["username"])
        payload = message_factory(user, MESSAGE_TYPES.login_response)
        await source.send(payload)

        # put user in lobby
        await self._join_room(self.lobby, source)

    async def handle_logout(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        if message is None:
            return

        userid = message.get(FIELDS_LOGOUT_MESSAGE.userid, "").strip()
        if len(userid) == 0:
            return

        if source.user is not None and userid != source.user.userid:
            return

        source.close()
        self.remove_connection(source)

    async def handle_join_room(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        if message is None:
            return

        name = message.get(FIELDS_JOIN_ROOM_MESSAGE.roomname, "").strip()
        userid = message.get(FIELDS_JOIN_ROOM_MESSAGE.userid, "").strip()
        if len(name) == 0 or len(userid) == 0:
            return

        if source.user is not None and source.user.userid != userid:
            return

        room: Chatroom | None = None

        # If name is lobby, join lobby
        if name == "Lobby":
            room = self.lobby
        # Otherwise check rooms already in memory
        if room is None:
            room = self.rooms.get(name, None)
        # Finally look up room in DB
        if room is None:
            try:
                room_data = self._db.get_room_by_name(name)
                # Wasn't found in the database or connection error
                if room_data is None:
                    await self.handle_error(
                        ERROR_TYPES.room_not_found, f"Room {name} not found"
                    )
                    return
            except DBConnectionError as e:
                await self.handle_error(ERROR_TYPES.server_error, ERRORS.server_error)
            id = room_data["id"]
            name = room_data["name"]
            room = Chatroom(id)
            self.rooms[name] = room
        room.join_room(source)
        await self._join_room(room, source)
        #

    async def _join_room(self, room: Chatroom, source: AbstractChatConnection):
        messages: List[Dict[str, str]] | None = None
        try:
            messages = self._db.get_room_messages(room.roomid)
        except DBConnectionError as e:
            logging.error("Error selecting recent messages: %s", e)
            await self.handle_error(
                ERROR_TYPES.server_error, ERRORS.server_error, source
            )
        except ValueError as e:
            logging.error("Error selecting recent messages: %s", e)
            return

        if messages is None:
            await self.handle_error(
                ERROR_TYPES.server_error, ERRORS.server_error, source
            )

        if len(messages) == 0:
            return

        payload = message_factory(messages, MESSAGE_TYPES.chat)
        await source.send(payload)

    async def handle_list_rooms(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        rooms: List[str] | None = None
        try:
            rooms = self._db.get_room_list()
        except DBConnectionError as e:
            await self.handle_error(
                ERROR_TYPES.server_error, ERRORS.server_error, source
            )

        payload = message_factory(rooms, MESSAGE_TYPES.list_rooms)
        await source.send(payload)

    async def handle_create_room(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        name = message[FIELDS_CREATE_ROOM_MESSAGE.name]

        room: Dict[str, str] | None = None
        try:
            room = self._db.insert_room(name)
        except DBConnectionError as e:
            await self.handle_error(
                ERROR_TYPES.server_error, ERRORS.server_error, source
            )
        except Error as e:
            if "unique" in str(e).lower():
                await self.handle_error(
                    ERROR_TYPES.invalid_room, "Room already exists", source
                )
                return

        r = Chatroom(room["id"])
        self.rooms[room["name"]] = r
        await self._join_room(r, source)

    async def handle_chat(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        messages = message.get(FIELDS_CHAT_MESSAGES.messages, [])
        if len(messages) == 0:
            return

        room_messages: List[Dict[str, str]] = []

        rid: str | None = None
        tuid: str | None = None

        # There should only be one message per user
        # but let's handle multiple messages anyway
        for message in messages:
            authorid = message.get("authorid", "").strip()
            roomid = message.get("roomid", "").strip()
            target_userid = message.get("target_userid", "").strip()
            message_content = message.get("message", "").strip()

            inserted: Dict[str, str] | None = None
            if len(authorid) == 0 or len(message_content) == 0:
                continue
            if len(roomid) == 0 and len(target_userid) == 0:
                continue
            if len(roomid) > 0:
                rid = roomid
            if len(target_userid) > 0:
                tuid = target_userid
            try:
                inserted = self._db.insert_chat_message(
                    authorid, roomid, target_userid, message_content
                )
            except DBConnectionError as e:
                await self.handle_error(
                    ERROR_TYPES.server_error, ERRORS.server_error, source
                )
                return
            if inserted is not None:
                room_messages.append(inserted)

        payload = message_factory(room_messages, MESSAGE_TYPES.chat)

        if rid is not None:
            room = self.rooms.get(rid, None)
            if room is None:
                return
            await room.forward_to_room(payload)
        if tuid is not None:
            conns = [
                c
                for c in self.connections
                if c.user is not None and c.user.userid == tuid
            ]

            if len(conns) != 1:
                return

            await conns[0].send(payload)

    async def handle_blacklist(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        userid = message.get(FIELDS_BLACKLIST_MESSAGE.userid, "").strip()
        username = message.get(FIELDS_BLACKLIST_MESSAGE.blocked_username, "").strip()

        if len(userid) == 0 or len(username) == 0:
            await self.handle_error(
                ERROR_TYPES.invalid_blacklist, ERRORS.invalid_blacklist, source
            )
            return

        # get userid
        blocked_user: Dict[str, str] | None = None
        try:
            blocked_user = self._db.get_user_by_username(username)
        except DBConnectionError as e:
            logging.error("error selecting user: %s", e)
            await self.handle_error(
                ERROR_TYPES.server_error, ERRORS.server_error, source
            )
            return

        if blocked_user is None:
            await self.handle_error(
                ERROR_TYPES.invalid_blacklist, ERRORS.invalid_blacklist, source
            )
            return

        blocked_userid = blocked_user.get("id", None)
        if blocked_userid is None:
            await self.handle_error(
                ERROR_TYPES.invalid_blacklist, ERRORS.invalid_blacklist, source
            )
            return

        result: Dict[str, str] | None = None
        try:
            result = self._db.insert_blacklist(userid, blocked_user)
        except DBConnectionError as e:
            await self.handle_error(
                ERROR_TYPES.server_error, ERRORS.server_error, source
            )
            return
        if result is not None:
            payload = message_factory(MESSAGE_TYPES.blacklist_response, message)
            await source.send(payload)

    async def handle_error(
        self, errortype: str, error: str, source: AbstractChatConnection
    ):
        data = {
            FIELDS_ERROR_MESSAGE.errortype: errortype,
            FIELDS_ERROR_MESSAGE.message: error,
        }

        message = message_factory(data, MESSAGE_TYPES.error)

        await source.send(message)

    def add_connection(self, conn: ChatServerConnection) -> None:
        if conn not in self.connections:
            self.connections.append(conn)

    def remove_connection(self, conn: ChatServerConnection) -> None:
        # Removes from any room they are in and sets it to None
        conn.room = None

        # remove from self.user_connections
        if conn.user is not None and conn.user.userid is not None:
            self.user_connections.pop(conn.user.userid, None)

        # remove from connections
        if conn in self.connections:
            self.connections.remove(conn)

        self._cleanup_rooms()

    def _cleanup_rooms(self) -> None:
        removable: List[str] = []
        for item in self.rooms.items():
            if len(item[1].connections) == 0:
                removable.append(item[0])

        for r in removable:
            self.rooms.pop(r)

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
    db._initialize_database(drop=True)
    server = ChatServer(db=db)
    try:
        server.start(host=host, port=port)
    except KeyboardInterrupt as e:
        logging.debug("ctrl+c: %s", e)


if __name__ == "__main__":
    run_server()
