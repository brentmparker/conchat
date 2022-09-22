from abc import ABC, abstractmethod
from multiprocessing.sharedctypes import Value
from typing import Any, Dict, List
import sqlite3
import uuid
import logging
from .database_protocol import AbstractDatabase, DBConnectionError

DBNAME = "conchat.db"

CREATE_TABLE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    createdate TEXT NOT NULL DEFAULT(STRFTIME('%Y-%m-%d %H:%M:%f+00:00', 'NOW'))
)
"""
DROP_TABLE_USERS = """
DROP TABLE IF EXISTS users
"""

CREATE_TABLE_ROOMS = """
CREATE TABLE IF NOT EXISTS rooms (
    id TEXT PRIMARY KEY UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL,
    createdate TEXT NOT NULL DEFAULT(STRFTIME('%Y-%m-%d %H:%M:%f+00:00', 'NOW'))
)
"""
DROP_TABLE_ROOMS = """
DROP TABLE IF EXISTS rooms
"""

CREATE_TABLE_MESSAGES = """
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY UNIQUE NOT NULL,
    authorid TEXT NOT NULL,
    roomid TEXT NOT NULL DEFAULT 'NONE',
    target_userid TEXT NOT NULL DEFAULT 'NONE',
    message TEXT NOT NULL,
    createdate TEXT NOT NULL DEFAULT(STRFTIME('%Y-%m-%d %H:%M:%f+00:00', 'NOW')),
    FOREIGN KEY (authorid)
        REFERENCES users (id)
        ON DELETE CASCADE
        ON UPDATE NO ACTION
    FOREIGN KEY (roomid)
        REFERENCES rooms (id)
        ON DELETE CASCADE
        ON UPDATE NO ACTION
    FOREIGN KEY (target_userid)
        REFERENCES users (id)
        ON DELETE CASCADE
        ON UPDATE NO ACTION
)
"""
DROP_TABLE_MESSAGES = """
DROP TABLE IF EXISTS messages
"""

CREATE_TABLE_BLACKLIST = """
CREATE TABLE IF NOT EXISTS blacklisted_users (
    userid TEXT NOT NULL,
    blocked_userid TEXT NOT NULL,
    createdate TEXT NOT NULL DEFAULT(STRFTIME('%Y-%m-%d %H:%M:%f+00:00', 'NOW')),
    UNIQUE(userid, blocked_userid),
    FOREIGN KEY (userid)
        REFERENCES users (id)
        ON DELETE CASCADE
        ON UPDATE NO ACTION
    FOREIGN KEY (blocked_userid)
        REFERENCES users (id)
        ON DELETE CASCADE
        ON UPDATE NO ACTION
)
"""
DROP_TABLE_BLACKLIST = """
DROP TABLE IF EXISTS blacklisted_users
"""

INSERT_USER = """
INSERT INTO users (
    id,
    username,
    password
) VALUES (
    ?,
    ?,
    ?
)
"""

INSERT_ROOM = """
INSERT INTO rooms (
    id,
    name
) VALUES (
    ?,
    ?
)
"""

INSERT_MESSAGE = """
INSERT INTO messages (
    id,
    authorid,
    roomid,
    target_userid,
    message
) VALUES (
    ?,
    ?,
    ?,
    ?,
    ?
)
"""

INSERT_BLACKLIST = """
INSERT INTO blacklisted_users (
    userid,
    blocked_userid
) VALUES (
    ?,
    ?
)
"""

SELECT_RECENT_USER = """
SELECT * FROM users WHERE rowid = ?
"""

SELECT_RECENT_ROOM = """
SELECT * FROM rooms WHERE rowid = ?
"""

SELECT_RECENT_MESSAGE = """
SELECT 
    m.id,
    u.username AS authorname,
    m.authorid,
    m.roomid,
    m.target_userid,
    m.message,
    m.createdate
FROM messages AS m 
INNER JOIN users AS u 
    ON m.authorid = u.id
WHERE m.rowid = ?
"""

SELECT_RECENT_BLACKLIST = """
SELECT * FROM blacklisted_users WHERE rowid = ?
"""

CREATE_TRIGGER_NONE_MESSAGE = """
CREATE TRIGGER IF NOT EXISTS trigger_block_none_message
    BEFORE INSERT ON messages
BEGIN
    SELECT
        CASE
            WHEN
                NEW.authorid = 'NONE' OR
                (NEW.roomid = 'NONE' AND NEW.target_userid = 'NONE')
            THEN
                RAISE (ABORT, 'authorid can not be NONE or missing one of roomid or target_userid')
    END;
END;
"""

DROP_TRIGGER_NONE_MESSAGE = """
DROP TRIGGER IF EXISTS trigger_block_none_message
"""

CREATE_TRIGGER_BLACKLIST = """
CREATE TRIGGER IF NOT EXISTS trigger_block_message_insert
    BEFORE INSERT ON messages
BEGIN
    SELECT
        CASE
            WHEN EXISTS(
                SELECT *
                FROM blacklisted_users AS b
                WHERE
                    NEW.authorid = b.blocked_userid AND
                    NEW.target_userid = b.userid
            ) THEN RAISE (ABORT, 'User has been blacklisted')
    END;
END;
"""

DROP_TRIGGER_BLACKLIST = """
DROP TRIGGER IF EXISTS trigger_block_message_insert
"""

SELECT_USER_BY_USERNAME = """
SELECT * FROM users WHERE username = ?
"""

SELECT_ROOM_BY_NAME = """
SELECT * FROM rooms WHERE name = ?
"""

SELECT_ALL_ROOMS = """
SELECT * FROM rooms
WHERE id != 'NONE'
ORDER BY name ASC
"""

SELECT_MESSAGES_BY_ROOMID = """
SELECT 
    m.id,
    u.username AS authorname,
    m.authorid,
    m.roomid,
    m.target_userid,
    m.message,
    m.createdate
FROM messages AS m 
INNER JOIN users AS u 
    ON m.authorid = u.id
WHERE m.roomid = ?
ORDER BY m.createdate DESC
LIMIT ?
"""


class AbstractID(ABC):
    @abstractmethod
    def id() -> str:
        pass


class UUID(AbstractID):
    def id(self) -> str:
        return str(uuid.uuid4())


class SqliteDatabase(AbstractDatabase):
    def __init__(
        self, db_name: str = DBNAME, id_generator: AbstractID = UUID()
    ) -> None:
        self.db_name = db_name
        self.id_gen = id_generator
        super().__init__()

    def _initialize_database(self, drop: bool = False) -> None:
        conn: sqlite3.Connection = self.open_connection()
        logging.info("Initializing database %s", self.db_name)
        with conn:
            cursor = conn.cursor()
            if drop:
                cursor.execute(DROP_TRIGGER_NONE_MESSAGE)
                cursor.execute(DROP_TRIGGER_BLACKLIST)
                cursor.execute(DROP_TABLE_BLACKLIST)
                cursor.execute(DROP_TABLE_MESSAGES)
                cursor.execute(DROP_TABLE_USERS)
                cursor.execute(DROP_TABLE_ROOMS)

            cursor.execute(CREATE_TABLE_USERS)
            cursor.execute(CREATE_TABLE_ROOMS)
            cursor.execute(CREATE_TABLE_MESSAGES)
            cursor.execute(CREATE_TABLE_BLACKLIST)
            cursor.execute(CREATE_TRIGGER_BLACKLIST)
            cursor.execute(CREATE_TRIGGER_NONE_MESSAGE)

            try:
                cursor.execute(INSERT_USER, ("NONE", "NONE", "NONE"))
            except sqlite3.Error as e:
                logging.debug("Error inserting 'NONE' user: %s", e)

            try:
                cursor.execute(INSERT_ROOM, ("NONE", "NONE"))
            except sqlite3.Error as e:
                logging.debug("Error inserting 'NONE' room: %s", e)

            try:
                id = self.id_gen.id()
                cursor.execute(INSERT_ROOM, (id, "Lobby"))
            except sqlite3.Error as e:
                logging.debug("Error inserting 'Lobby' room: %s", e)

            conn.commit()

    def open_connection(self) -> sqlite3.Connection | None:
        conn: sqlite3.Connection = None
        try:
            conn = sqlite3.connect(
                self.db_name,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
        except sqlite3.Error as e:
            logging.error(e)
            raise DBConnectionError(e)

        conn.set_trace_callback(logging.info)

        return conn

    def insert_chat_message(
        self,
        authorid: str,
        roomid: str | None,
        target_userid: str | None,
        message: str,
    ) -> Dict[str, str] | None:
        conn = self.open_connection()
        if conn is None:
            return

        result: Dict[str, str] = None

        with conn:
            message = (self.id_gen.id(), authorid, roomid, target_userid, message)
            cursor = conn.cursor()
            cursor.execute(INSERT_MESSAGE, message)
            if cursor.rowcount != 1:
                raise sqlite3.Error(f"Error inserting message: {message}")
            conn.commit()
            row = cursor.execute(SELECT_RECENT_MESSAGE, (cursor.lastrowid,)).fetchone()
            result = {
                "id": row[0],
                "authorname": row[1],
                "authorid": row[2],
                "roomid": row[3],
                "target_userid": row[4],
                "message": row[5],
                "createdate": row[6],
            }
        return result

    def insert_user(self, username: str, password: str) -> Dict[str, str] | None:
        conn = self.open_connection()
        if conn is None:
            return

        result: Dict[str, str] = None

        with conn:
            user = (self.id_gen.id(), username, password)
            cursor = conn.cursor()
            cursor.execute(INSERT_USER, user)
            if cursor.rowcount != 1:
                raise sqlite3.Error(f"Error inserting user: {user}")

            conn.commit()
            # Select inserted user
            cursor.execute(SELECT_RECENT_USER, (cursor.lastrowid,))
            row = cursor.fetchone()
            result = {"id": row[0], "username": row[1], "createdate": row[3]}
        return result

    def insert_room(self, name: str) -> Dict[str, str] | None:
        conn = self.open_connection()
        if conn is None:
            return

        result: Dict[str, str] | None = None
        with conn:
            room = (self.id_gen.id(), name)
            cursor = conn.cursor()
            cursor.execute(INSERT_ROOM, room)
            if cursor.rowcount != 1:
                raise sqlite3.Error(f"Error inserting room: {room}")

            conn.commit()

            row = cursor.execute(SELECT_RECENT_ROOM, (cursor.lastrowid,)).fetchone()
            result = {"id": row[0], "name": row[1], "createdate": row[2]}

        return result

    def insert_blacklist(
        self, userid: str, blocked_userid: str
    ) -> Dict[str, str] | None:
        conn = self.open_connection()
        if conn is None:
            return

        result: Dict[str, str] = None

        with conn:
            blacklist = (userid, blocked_userid)
            cursor = conn.cursor()
            cursor.execute(INSERT_BLACKLIST, blacklist)
            if cursor.rowcount != 1:
                raise sqlite3.Error(f"Error inserting blacklisted user: {blacklist}")

            conn.commit()

            row = cursor.execute(
                SELECT_RECENT_BLACKLIST, (cursor.lastrowid,)
            ).fetchone()
            result = {"userid": row[0], "blocked_userid": row[1]}
        return result

    def get_room_messages(
        self, roomid: str, limit: int = 30
    ) -> List[Dict[str, str]] | None:
        if roomid is None:
            raise ValueError("roomid can not be None")
        roomid = roomid.strip()
        if len(roomid) == 0:
            raise ValueError("roomid can not be empty")
        if limit <= 0:
            raise ValueError("limit must be a postive integer > 0")

        conn = self.open_connection()
        if conn is None:
            return None

        result: List[Dict[str, str]] = []

        with conn:
            cursor = conn.cursor()
            cursor.execute(SELECT_MESSAGES_BY_ROOMID, (roomid, limit))

            rows = cursor.fetchall()
            for row in rows:
                result.append(
                    {
                        "id": row[0],
                        "authorname": row[1],
                        "authorid": row[2],
                        "roomid": row[3],
                        "target_userid": row[4],
                        "message": row[5],
                        "createdate": row[6],
                    }
                )
        return result

    def get_user_by_username(self, username: str) -> Dict[str, str]:
        if username is None:
            raise ValueError("username can not be none")
        username = username.strip()
        if len(username) == 0:
            raise ValueError("username can not be empty")
        conn = self.open_connection()
        if conn is None:
            return None

        result: Dict[str, str] | None = None

        with conn:
            cursor = conn.cursor()
            cursor.execute(SELECT_USER_BY_USERNAME, (username,))

            row = cursor.fetchone()
            result = {
                "id": row[0],
                "username": row[1],
                "password": row[2],
                "createdate": row[3],
            }

        return result

    def get_room_by_name(self, name: str) -> Dict[str, str] | None:
        if name is None:
            raise ValueError("name can not be None")
        name = name.strip()
        if len(name) == 0:
            raise ValueError("name can not be empty")

        conn = self.open_connection()
        if conn is None:
            return None

        result: Dict[str, str] | None = None

        with conn:
            cursor = conn.cursor()
            cursor.execute(SELECT_ROOM_BY_NAME, (name,))

            row = cursor.fetchone()
            result = {"id": row[0], "name": row[1], "createdate": row[2]}
        return result

    def get_room_list(self) -> List[Dict[str, str]] | None:
        conn = self.open_connection()
        if conn is None:
            return None

        result: List[Dict[str, str]] = []
        with conn:
            cursor = conn.cursor()
            cursor.execute(SELECT_ALL_ROOMS)

            rows = cursor.fetchall()

            for row in rows:
                result.append({"id": row[0], "name": row[1], "createdate": row[2]})

        return result


if __name__ == "__main__":
    db = SqliteDatabase()
    db._initialize_database(drop=True)
