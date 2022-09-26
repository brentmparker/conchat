from __future__ import annotations
import asyncio
import json
import logging
import bcrypt
from typing import Dict, List

from .chat_server_protocol import (
    AbstractChatServer,
    AbstractChatConnection,
    Chatroom,
)
from .database_protocol import AbstractDatabase, ConstraintError, DBConnectionError
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
    FIELDS_JOIN_ROOM_MESSAGE,
    FIELDS_LIST_USERS_MESSAGE,
    FIELDS_LOGOUT_MESSAGE,
    FIELDS_REGISTER_MESSAGE,
    FIELDS_UNBLOCK_MESSAGE,
    # message_factory,
    serialzie_create_room_response_message,
    serialize_register_response_message,
    serialize_blacklist_response_message,
    serialize_chat,
    serialize_chat_messages,
    serialize_error_message,
    serialize_join_room_response_message,
    serialize_list_rooms_message,
    serialize_list_users_message,
    serialize_login_response_message,
    serialize_unblock_response_message,
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

    async def send(self, payload: str) -> None:
        if payload is None:
            return
        if self.closed:
            return

        try:
            logging.debug("Sending payload: \n%s", payload)
            self.conn.write(payload.encode(ENCODING))
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
            case MESSAGE_TYPES.create_room:
                await self.handle_create_room(message, source)
            case MESSAGE_TYPES.chat:
                await self.handle_chat(message, source)
            case MESSAGE_TYPES.join_room:
                await self.handle_join_room(message, source)
            case MESSAGE_TYPES.list_rooms:
                await self.handle_list_rooms(message, source)
            case MESSAGE_TYPES.list_users:
                await self.handle_list_users(message, source)
            case MESSAGE_TYPES.login:
                await self.handle_login(message, source)
            case MESSAGE_TYPES.logout:
                await self.handle_logout(message, source)
            case MESSAGE_TYPES.register:
                await self.handle_register(message, source)
            case MESSAGE_TYPES.unblock:
                await self.handle_unblock(message, source)
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

    async def handle_blacklist(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        userid = message.get(FIELDS_BLACKLIST_MESSAGE.userid, "").strip()
        username = message.get(FIELDS_BLACKLIST_MESSAGE.blocked_username, "").strip()

        if len(userid) == 0 or len(username) == 0:
            return await self.handle_error(
                ERROR_TYPES.invalid_blacklist, ERRORS.invalid_blacklist, source
            )

        # get userid
        blocked_user: Dict[str, str] | None = None

        try:
            blocked_user = self._db.get_user_by_username(username)
        except ValueError as e:
            logging.debug("Error: get_user_by_username: %s\n%s", username, e)

        if blocked_user is None:
            return await self.handle_error(
                ERROR_TYPES.invalid_blacklist, ERRORS.invalid_blacklist, source
            )

        blocked_userid = blocked_user.get("id", None)
        if blocked_userid is None:
            return await self.handle_error(
                ERROR_TYPES.invalid_blacklist, ERRORS.invalid_blacklist, source
            )

        result: Dict[str, str] | None = None
        try:
            result = self._db.insert_blacklist(userid, blocked_userid)
        except ConstraintError as e:
            logging.error(e)
            return await self.handle_error(
                ERROR_TYPES.server_error, ERRORS.server_error, source
            )

        if result is None:
            return

        payload = serialize_blacklist_response_message(userid, username)
        await source.send(payload)

    async def handle_create_room(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        name = message[FIELDS_CREATE_ROOM_MESSAGE.name]

        room: Dict[str, str] | None = None

        # ******************************
        # ******************************
        # ******************************
        # Insert room into database
        # Don't forget about possible ConstraintErrors
        # Use result to create Chatroom object
        new_room = None  # This should not be None, this should be a new Chatroom object
        # Add room to self.rooms (key is room id)
        # Create and send create_room_response message using imported serializer function
        # ******************************
        # ******************************
        # ******************************

        await self._join_room(new_room, source)

    async def handle_chat(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        messages = message.get(FIELDS_CHAT_MESSAGES.messages, [])
        if len(messages) == 0:
            return

        room_messages: List[Dict[str, str]] = []

        rid: str | None = None
        tuid: str | None = None
        # messages come is as a list to simplify API
        # So you need to interate over messages

        # ******************************
        # ******************************
        # ******************************
        # for each message in messages
        #   get authorid, roomid, target_userid, target_username, message
        #   validate inputs
        #   if there is a target_username, it's a DM
        #       get target users's ID from database
        #       Don't forget to handle any ConstraintErrors that may be raised
        #   insert message into database (using target_userid if DM)
        #   Don't forget to handle any ConstraintErrors that may be raised (like blocked users)
        #   If it is a room message, forward message to entire room
        #   If it is a DM, forward message to ORIGNAL SENDER AND TARGET USER
        # ******************************
        # ******************************
        # ******************************

        for message in messages:
            authorid = message.get(FIELDS_CHAT_MESSAGE.authorid, "").strip()
            roomid = message.get(FIELDS_CHAT_MESSAGE.roomid, "").strip()
            target_userid = message.get(FIELDS_CHAT_MESSAGE.target_userid, "").strip()
            target_username = message.get(
                FIELDS_CHAT_MESSAGE.target_username, ""
            ).strip()
            message_content = message.get(FIELDS_CHAT_MESSAGE.message, "").strip()

    async def handle_error(
        self, errortype: str, error: str, source: AbstractChatConnection
    ):
        message = serialize_error_message(errortype, error)
        await source.send(message)

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
            # ******************************
            # ******************************
            # ******************************
            # Get room from databasey by room name
            # Don't forget to handle any constraint errors that may be raised
            # If the room is not already in self.rooms
            #   create a new Chatroom object
            #   Insert into self.rooms (key is room's id)
            # ******************************
            # ******************************
            # ******************************
            pass

        await self._join_room(room, source)

    async def _join_room(self, room: Chatroom, source: AbstractChatConnection):

        room.join_room(source)
        # Send join room message
        payload = serialize_join_room_response_message(
            source.user.userid, room.id, room.name
        )
        await source.send(payload)
        # Weird thing to do, but messages can be sent together if there is not enough time between
        await asyncio.sleep(0.05)

        # Now get recent messages in room and send those
        messages: List[Dict[str, str]] | None = None
        try:
            messages = self._db.get_room_messages(room.id)
        except DBConnectionError as e:
            logging.error("Error selecting recent messages: %s", e)
            return await self.handle_error(
                ERROR_TYPES.server_error, ERRORS.server_error, source
            )
        except ValueError as e:
            logging.error("Error selecting recent messages: %s", e)
            return

        if messages is None:
            return await self.handle_error(
                ERROR_TYPES.server_error, ERRORS.server_error, source
            )

        if len(messages) == 0:
            return

        payload = serialize_chat_messages(messages)
        await source.send(payload)

    async def handle_list_rooms(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:
        rooms: List[str] | None = None
        rooms = self._db.get_room_list()
        room_names: List[str] = ["Lobby"]
        if rooms is not None and len(rooms) > 0:
            room_names = [r.get("name") for r in rooms if r.get("name", None) != None]

        payload = serialize_list_rooms_message(room_names)
        await source.send(payload)

    async def handle_list_users(
        self, message: Dict[str, str], source: AbstractChatConnection
    ):
        roomid = message.get(FIELDS_LIST_USERS_MESSAGE.roomid, None)
        if roomid is None:
            return await self.handle_error(
                ERROR_TYPES.room_not_found, ERRORS.room_not_found, source
            )

        room = self.rooms.get(roomid, None)
        if room is None:
            return await self.handle_error(
                ERROR_TYPES.room_not_found, f"Empty room", source
            )

        usernames = [c.user.username for c in room.connections if c.user is not None]
        payload = serialize_list_users_message(room.id, room.name, usernames)
        await source.send(payload)

    async def handle_login(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:

        username = message.get(FIELDS_REGISTER_MESSAGE.username, "").strip()
        password = message.get(FIELDS_REGISTER_MESSAGE.password, "").strip()

        if len(username) == 0 or len(password) == 0:
            logging.error("Missing field in register message: %s", e)
            return await self.handle_error(
                ERROR_TYPES.invalid_username_password,
                ERRORS.invalid_username_password,
                source,
            )

        user: Dict[str, str] | None = None

        # ******************************
        # ******************************
        # ******************************
        # Get the user from the database using username
        # Don't forget to handle any ConstraintErrors that may be raised
        # ******************************
        # ******************************
        # ******************************

        # User is not found
        if user is None:
            return await self.handle_error(
                ERROR_TYPES.invalid_username_password,
                ERRORS.invalid_username_password,
                source,
            )

        # Validate password
        pwhash = user["password"]
        if not bcrypt.checkpw(password.encode(ENCODING), pwhash):
            return await self.handle_error(
                ERROR_TYPES.invalid_username_password,
                ERRORS.invalid_username_password,
                source,
            )

        # ******************************
        # ******************************
        # ******************************
        # create a login_response using the serializer imported above
        payload = None  # use serializer above for this assignment
        # You may need to read the signature to know what to send
        # The room id and room name are for the lobby
        # Use the self.lobby object to find those
        # ******************************
        # ******************************
        # ******************************

        await source.send(payload)

        # Weird thing to do but messages can be batched together if sent too close in time
        await asyncio.sleep(0.05)

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

    async def handle_register(
        self, message: Dict[str, str], source: AbstractChatConnection
    ) -> None:

        username = message.get(FIELDS_REGISTER_MESSAGE.username, "").strip()
        password = message.get(FIELDS_REGISTER_MESSAGE.password, "").strip()

        if len(username) == 0 or len(password) == 0:
            logging.error("Missing field in register message: %s", e)
            return await self.handle_error(
                ERROR_TYPES.invalid_username_password,
                ERRORS.invalid_username_password,
                source,
            )
        user: Dict[str, str] | None = None
        try:
            pwhash = bcrypt.hashpw(password.encode(ENCODING), bcrypt.gensalt())
            user = self._db.insert_user(username, pwhash)
        except ConstraintError as e:
            logging.error("Error registering user: %s", e)
            return await self.handle_error(
                ERROR_TYPES.username_exists, ERRORS.username_exists, source
            )

        if user is None:
            return await self.handle_error(
                ERROR_TYPES.server_error, ERRORS.server_error, source
            )

        payload = serialize_register_response_message(user["username"], "registered")
        await source.send(payload)

    async def handle_unblock(self, message: Dict[str, str], source):
        if message is None:
            return

        userid = message.get(FIELDS_UNBLOCK_MESSAGE.userid, "").strip()
        username = message.get(FIELDS_UNBLOCK_MESSAGE.blocked_username, "").strip()

        if len(userid) == 0 or len(username) == 0:
            return await self.handle_error(
                ERROR_TYPES.invalid_blacklist, ERRORS.invalid_blacklist, source
            )

        # get userid
        blocked_user: Dict[str, str] | None = None

        try:
            blocked_user = self._db.get_user_by_username(username)
        except ValueError as e:
            logging.debug("Error: get_user_by_username: %s\n%s", username, e)

        if blocked_user is None:
            return await self.handle_error(
                ERROR_TYPES.invalid_blacklist, ERRORS.invalid_blacklist, source
            )

        blocked_userid = blocked_user.get("id", None)
        if blocked_userid is None:
            return await self.handle_error(
                ERROR_TYPES.invalid_blacklist, ERRORS.invalid_blacklist, source
            )

        result: bool = False
        try:
            result = self._db.delete_blacklist(userid, blocked_userid)
        except ConstraintError as e:
            logging.error(e)
            return await self.handle_error(
                ERROR_TYPES.server_error, ERRORS.server_error, source
            )
        if not result:
            return await self.handle_error(
                ERROR_TYPES.server_error, ERRORS.server_error, source
            )

        payload = serialize_unblock_response_message(userid, username)
        await source.send(payload)

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
            id = item[0]
            room = item[1]
            if room.id == self.lobby.id:
                continue
            if len(room.connections) == 0:
                removable.append(id)

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
    db._initialize_database(drop=False)
    server = ChatServer(db=db)
    try:
        server.start(host=host, port=port)
    except KeyboardInterrupt as e:
        logging.debug("ctrl+c: %s", e)


if __name__ == "__main__":
    run_server()
