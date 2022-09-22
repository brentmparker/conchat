from __future__ import annotations
import asyncio
import json
import logging
from multiprocessing.sharedctypes import Value
import bcrypt
from typing import Any, Coroutine, Dict, List
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
        try:
            username = message[FIELDS_REGISTER_MESSAGE.username]
            password = message[FIELDS_REGISTER_MESSAGE.password]
        except KeyError as e:
            logging.error("Missing field in register message: %s", e)
            await self.handle_error(
                ERROR_TYPES.invalid_username_password,
                ERRORS.invalid_username_password,
                source,
            )
        # Check inputs
        errors: List[str] = []
        if username is None:
            errors.append("Username can not be None")
        if password is None:
            errors.append("Password can not be None")
        username = username.strip()
        password = password.strip()
        if len(username) == 0:
            errors.append("Username can not be empty")
        if len(password) == 0:
            errors.append("Password can not be empty")

        if len(errors) > 0:
            error = "\n".join(errors)
            await self.handle_error(
                ERROR_TYPES.invalid_username_password, error, source
            )
            return

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
        try:
            username = message[FIELDS_REGISTER_MESSAGE.username]
            password = message[FIELDS_REGISTER_MESSAGE.password]
        except KeyError as e:
            logging.error("Missing field in register message: %s", e)
            await self.handle_error(
                ERROR_TYPES.invalid_username_password,
                ERRORS.invalid_username_password,
                source,
            )
        # Check inputs
        errors: List[str] = []
        if username is None:
            errors.append("Username can not be None")
        if password is None:
            errors.append("Password can not be None")
        username = username.strip()
        password = password.strip()
        if len(username) == 0:
            errors.append("Username can not be empty")
        if len(password) == 0:
            errors.append("Password can not be empty")

        if len(errors) > 0:
            error = "\n".join(errors)
            await self.handle_error(
                ERROR_TYPES.invalid_username_password, error, source
            )
            return
        # Select user
        # validate password
        # send login_response

    async def handle_logout(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        if message is None:
            return
        try:
            userid = message[FIELDS_LOGOUT_MESSAGE.userid]
        except Exception as e:
            return

        userid = userid.strip()
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

        try:
            name = message[FIELDS_JOIN_ROOM_MESSAGE.roomname]
            userid = message[FIELDS_JOIN_ROOM_MESSAGE.userid]
        except Exception as e:
            return

        name = name.strip()
        userid = userid.strip()
        if len(name) == 0:
            return

        if len(userid) == 0:
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
        #

    async def handle_list_rooms(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        pass

    async def handle_create_room(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        pass

    async def handle_chat(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        pass

    async def handle_blacklist(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        pass

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
