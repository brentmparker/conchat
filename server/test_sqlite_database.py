from __future__ import annotations
import sqlite3
from typing import Iterable
from .sqlite_database import SqliteDatabase, AbstractID

import pytest


class MockIDGen(AbstractID):
    def __init__(self) -> None:
        super().__init__()
        self.id_cnt: int = 0

    def id(self) -> str:
        self.id_cnt += 1
        return f"{self.id_cnt}"


@pytest.fixture
def id_gen() -> AbstractID:
    return MockIDGen()


@pytest.fixture
def database(id_gen) -> SqliteDatabase:
    print("Initializing database")
    db: SqliteDatabase = SqliteDatabase(db_name="test.db", id_generator=id_gen)
    db._initialize_database(drop=True)
    return db


def test_insert_user(database: SqliteDatabase):
    username = "Test"
    password = "test"
    result = database.insert_user(username, password)
    id = database.id_gen.id_cnt
    assert result is not None
    assert result["id"] == str(id)
    assert result["username"] == username
    assert isinstance(result["createdate"], str) == True


def test_insert_nonunique_username(database: SqliteDatabase):
    with pytest.raises(sqlite3.Error):
        database.insert_user("User1", "Pass1")
        database.insert_user("User1", "Pass1")


def test_insert_room(database: SqliteDatabase):
    name = "Lobby"
    result = database.insert_room(name)
    id = database.id_gen.id_cnt
    assert result is not None
    assert result["id"] == str(id)
    assert result["name"] == name
    assert isinstance(result["createdate"], str) == True


def test_insert_nonunique_room_name(database: SqliteDatabase):
    with pytest.raises(sqlite3.Error):
        database.insert_room("Room")
        database.insert_room("Room")


def test_insert_blacklist(database: SqliteDatabase):
    u1 = database.insert_user("User1", "Pass1")
    u2 = database.insert_user("User2", "Pass2")

    uid1 = u1["id"]
    uid2 = u2["id"]
    result = database.insert_blacklist(uid1, uid2)
    assert result is not None
    assert result["userid"] == uid1
    assert result["blocked_userid"] == uid2


def test_insert_message(database: SqliteDatabase):
    u1 = database.insert_user("User1", "Pass1")
    r1 = database.insert_room("Lobby")

    uid = u1["id"]
    rid = r1["id"]
    tuid = "NONE"
    m = "I'm a message"

    result = database.insert_chat_message(uid, rid, tuid, m)

    id = database.id_gen.id_cnt
    assert result is not None
    assert result["id"] == str(id)
    assert result["authorid"] == uid
    assert result["roomid"] == rid
    assert result["message"] == m
    assert result["target_userid"] == tuid
    assert isinstance(result["createdate"], str) == True


def test_insert_none_message(database: SqliteDatabase):
    r1 = database.insert_room("Lobby")
    uid = "NONE"
    rid = r1["id"]
    tuid = "NONE"
    m = "I'm a message"

    with pytest.raises(sqlite3.Error):
        database.insert_chat_message(uid, rid, tuid, m)


def test_insert_blacklisted_message(database: SqliteDatabase):
    with pytest.raises(sqlite3.Error):
        u1 = database.insert_user("User1", "Pass1")
        u2 = database.insert_user("User2", "Pass2")

        uid1 = u1["id"]
        uid2 = u2["id"]
        database.insert_blacklist(uid1, uid2)

        m = "I'm a message"

        database.insert_chat_message(uid2, "NONE", uid1, m)


def test_get_user_by_username(database: SqliteDatabase):
    username = "User1"
    password = "Pass1"

    database.insert_user(username, password)

    result = database.get_user_by_username(username)
    id = database.id_gen.id_cnt

    assert result["id"] == str(id)
    assert result["username"] == username
    assert result["password"] == password
    assert isinstance(result["createdate"], str) == True


def test_get_room_by_name(database: SqliteDatabase):
    name = "My Room"

    database.insert_room(name)

    result = database.get_room_by_name(name)
    id = database.id_gen.id_cnt

    assert result is not None
    assert result["id"] == str(id)
    assert result["name"] == name
    assert isinstance(result["createdate"], str) == True


def test_get_recent_room_message(database: SqliteDatabase):
    u1 = database.insert_user("User1", "Pass1")
    r1 = database.insert_room("Lobby")

    for i in range(30):
        database.insert_chat_message(u1["id"], r1["id"], "NONE", f"Message {i}")

    limit = 20
    result = database.get_room_messages(r1["id"], limit=limit)
    assert result is not None
    assert isinstance(result, list) == True
    assert len(result) <= limit


def test_get_room_list(database: SqliteDatabase):
    num_rooms = 10
    for i in range(1, 1 + num_rooms):
        database.insert_room(f"Room {i}")
    result = database.get_room_list()

    assert result is not None
    assert isinstance(result, list) == True
    assert len(result) == num_rooms
