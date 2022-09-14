from typing import Any, Dict, List
import sqlite3
import uuid
from database_protocol import AbstractDatabase

DBNAME = "conchat.db"

CREATE_TABLE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    createdate TEXT NOT NULL DEFAULT(STRFTIME('%Y-%m-%d %H:%M:%f+00:00', 'NOW'))
);
"""
DROP_TABLE_USERS = """
DROP TABLE IF EXISTS users;
"""

CREATE_TABLE_ROOMS = """
CREATE TABLE IF NOT EXISTS rooms (
    id TEXT PRIMARY KEY UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL,
    createdate TEXT NOT NULL DEFAULT(STRFTIME('%Y-%m-%d %H:%M:%f+00:00', 'NOW'))
);
"""
DROP_TABLE_ROOMS = """
DROP TABLE IF EXISTS rooms;
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
);
"""
DROP_TABLE_MESSAGES = """
DROP TABLE IF EXISTS messages;
"""

CREATE_TABLE_BLACKLIST = """
CREATE TABLE IF NOT EXISTS blacklisted_users (
    userid TEXT NOT NULL,
    blocked_userid TEXT NOT NULL,
    createdate TEXT NOT NULL DEFAULT(STRFTIME('%Y-%m-%d %H:%M:%f+00:00', 'NOW')),
    FOREIGN KEY (userid)
        REFERENCES users (id)
        ON DELETE CASCADE
        ON UPDATE NO ACTION
    FOREIGN KEY (blocked_userid)
        REFERENCES users (id)
        ON DELETE CASCADE
        ON UPDATE NO ACTION
);
"""
DROP_TABLE_BLACKLIST = """
DROP TABLE IF EXISTS blacklisted_users;
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
);
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
);
"""

INSERT_BLACKLIST = """
INSERT INTO blacklisted_users (
    userid,
    blocked_userid
) VALUES (
    ?,
    ?
);
"""

SELECT_RECENT_USER = """
SELECT * FROM users WHERE rowid = ?;
"""

SELECT_RECENT_ROOM = """
SELECT * FROM rooms WHERE rowid = ?;
"""

SELECT_RECENT_MESSAGE = """
SELECT * FROM messages WHERE rowid = ?;
"""


class SqliteDatabase(AbstractDatabase):
    def __init__(self) -> None:
        super().__init__()

    def _initialize_database(self, drop: bool = False) -> None:
        conn: sqlite3.Connection = self.open_connection()
        if conn is None:
            return

        with conn:
            cursor = conn.cursor()
            if drop:
                cursor.execute(DROP_TABLE_BLACKLIST)
                cursor.execute(DROP_TABLE_MESSAGES)
                cursor.execute(DROP_TABLE_USERS)
                cursor.execute(DROP_TABLE_ROOMS)

            cursor.execute(CREATE_TABLE_USERS)
            cursor.execute(CREATE_TABLE_ROOMS)
            cursor.execute(CREATE_TABLE_MESSAGES)
            cursor.execute(CREATE_TABLE_BLACKLIST)

            # Create NONE user (reference for messages.target_userid)
            data = ("NONE", "NONE", "NONE")
            cursor.execute(INSERT_USER, data)

            data = ("NONE", "NONE")
            cursor.execute(INSERT_ROOM, data)

            conn.commit()

    def open_connection(self) -> sqlite3.Connection | None:
        conn: sqlite3.Connection = None
        try:
            conn = sqlite3.connect(
                DBNAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
        except sqlite3.Error as e:
            print(e)

        return conn

    def insert_chat_message(
        self,
        authorid: str,
        roomid: str | None,
        target_userid: str | None,
        message: str,
    ) -> Dict[str, str]:
        pass

    def insert_user(self, username: str, password: str) -> Dict[str, str]:
        conn = self.open_connection()
        if conn is None:
            return

        result: Dict[str, str] = None

        with conn:
            user = (str(uuid.uuid4()), username, password)
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

    def insert_room(self, name: str) -> Dict[str, str]:
        conn = self.open_connection()
        if conn is None:
            return

        result: Dict[str, str] = None
        with conn:
            room = (str(uuid.uuid4()), name)
            cursor = conn.cursor()
            cursor.execute(INSERT_ROOM, room)
            if cursor.rowcount != 1:
                raise sqlite3.Error(f"Error inserting room: {room}")

            conn.commit()

            row = cursor.execute(SELECT_RECENT_ROOM, (cursor.lastrowid,)).fetchone()
            result = {"id": row[0], "name": row[1], "createdate": row[2]}

        return result

    def insert_blacklist(self, userid: str, blocked_userid: str):
        pass

    def get_room_messages(self, roomid: str, limit: int = 30) -> List[Dict[str, str]]:
        pass

    def get_user_by_username(self, username: str) -> Dict[str, str]:
        pass


def test(db: SqliteDatabase):
    user1 = db.insert_user("Test", "test")
    room1 = db.insert_room("Lobby")
    message1 = db.insert_chat_message(
        user1["username"], user1["id"], room1["id"], "NONE", "I'm a message!"
    )


if __name__ == "__main__":
    db = SqliteDatabase()
    db._initialize_database(drop=True)
    test(db)
