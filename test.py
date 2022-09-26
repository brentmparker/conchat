from datetime import datetime, timezone
from msilib.schema import Error
from multiprocessing.sharedctypes import Value
import sqlite3
from typing import Dict
import uuid
import bcrypt
from common import ENCODING

from server.sqlite_database import (
    CREATE_TABLE_USERS,
    CREATE_TABLE_ROOMS,
    CREATE_TABLE_MESSAGES,
    CREATE_TABLE_BLACKLIST,
    CREATE_TRIGGER_BLACKLIST,
    CREATE_TRIGGER_NONE_MESSAGE,
    DROP_TABLE_BLACKLIST,
    DROP_TABLE_MESSAGES,
    DROP_TABLE_ROOMS,
    DROP_TABLE_USERS,
    DROP_TRIGGER_BLACKLIST,
    DROP_TRIGGER_NONE_MESSAGE,
    INSERT_USER,
    INSERT_ROOM,
    INSERT_MESSAGE,
    INSERT_BLACKLIST,
    SELECT_RECENT_USER,
    SELECT_RECENT_ROOM,
    SELECT_RECENT_MESSAGE,
    SELECT_LATEST_ROOM_MESSAGES,
    SELECT_USER_BY_USERNAME,
    SELECT_ROOM_BY_NAME,
)

DB = "test.db"


def create_connection(database) -> sqlite3.Connection | None:
    conn = None
    try:
        conn = sqlite3.connect(
            database,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
    except sqlite3.Error as e:
        print(e)

    return conn


def test_db():
    conn = create_connection(DB)
    if conn is None:
        print("could not connect")
        return

    with conn:
        cursor = conn.cursor()
        cursor.execute(DROP_TABLE_USERS)
        cursor.execute(DROP_TABLE_ROOMS)
        cursor.execute(DROP_TABLE_MESSAGES)
        cursor.execute(DROP_TABLE_BLACKLIST)
        cursor.execute(DROP_TRIGGER_BLACKLIST)
        cursor.execute(DROP_TRIGGER_NONE_MESSAGE)

        cursor.execute(CREATE_TABLE_USERS)
        cursor.execute(CREATE_TABLE_ROOMS)
        cursor.execute(CREATE_TABLE_MESSAGES)
        cursor.execute(CREATE_TABLE_BLACKLIST)
        cursor.execute(CREATE_TRIGGER_BLACKLIST)
        cursor.execute(CREATE_TRIGGER_NONE_MESSAGE)

        cursor.execute(INSERT_USER, ("NONE", "NONE", "NONE"))
        cursor.execute(INSERT_ROOM, ("NONE", "NONE"))

        conn.commit()


def test_insert_user(username: str, pw: str):
    salt = bcrypt.gensalt()
    user = (str(uuid.uuid4()), username, bcrypt.hashpw(pw.encode(ENCODING), salt))

    print(f"Inserting user: {user}")

    conn = create_connection(DB)
    if conn is None:
        print("Could not connect to database")
        return

    with conn:
        cursor = conn.cursor()
        cursor.execute(INSERT_USER, user)
        if cursor.rowcount != 1:
            raise sqlite3.Error("Error insterting user")
        conn.commit()

        row = cursor.execute(SELECT_RECENT_USER, (cursor.lastrowid,)).fetchone()

        if not bcrypt.checkpw(pw.encode(ENCODING), row[2]):
            raise ValueError("Passwords do not match")

        user = {
            "id": row[0],
            "username": row[1],
            "password": row[2],
            "createdate": row[3],
        }
        return user


def test_insert_room(roomname: str) -> Dict[str, str]:
    room = (str(uuid.uuid4()), roomname)

    print(f"Inserting room: {room}")

    conn = create_connection(DB)
    if conn is None:
        print("Could not connect to database")
        return

    with conn:
        cursor = conn.cursor()
        cursor.execute(INSERT_ROOM, room)
        if cursor.rowcount != 1:
            raise sqlite3.Error("Error inserting room")
        conn.commit()
        row = cursor.execute(SELECT_RECENT_ROOM, (cursor.lastrowid,)).fetchone()
        room = {"id": row[0], "name": row[1], "createdate": row[2]}

        return room


def test_insert_message(authorid: str, roomid: str, target_userid: str, message: str):
    message = (str(uuid.uuid4()), authorid, roomid, target_userid, message)

    print(f"Inserting message: {message}")

    conn = create_connection(DB)
    if conn is None:
        print("Could not connect to database")
        return

    with conn:
        cursor = conn.cursor()
        cursor.execute(INSERT_MESSAGE, message)
        if cursor.rowcount != 1:
            raise sqlite3.Error("Error inserting message")
        conn.commit()
        row = cursor.execute(SELECT_RECENT_MESSAGE, (cursor.lastrowid,)).fetchone()

        room = {
            "id": row[0],
            "authorid": row[1],
            "roomid": row[2],
            "target_userid": row[3],
            "message": row[4],
            "createdate": row[5],
        }

        return room


def test_insert_blacklist(userid: str, blocked_userid: str):
    blacklist = (userid, blocked_userid)

    print(f"Inserting blacklist: {blacklist}")

    conn = create_connection(DB)
    if conn is None:
        return

    with conn:
        cursor = conn.cursor()
        cursor.execute(INSERT_BLACKLIST, blacklist)
        if cursor.rowcount != 1:
            raise sqlite3.Error("Error inserting blacklist")

        conn.commit()


def test_get_room_messages(roomid: str, limit: int = 30):
    params = (roomid, limit)

    conn = create_connection(DB)
    if conn is None:
        return

    with conn:
        cursor = conn.cursor()
        cursor.execute(SELECT_LATEST_ROOM_MESSAGES, params)
        rows = cursor.fetchall()
        print(f"Selected {len(rows)} messages")

        messages = []
        for r in rows:
            print(r)


if __name__ == "__main__":
    test_db()
    user = test_insert_user("Brent", "test")
    user2 = test_insert_user("Test", "test")
    user3 = test_insert_user("Test2", "test")
    user4 = test_insert_user("Test3", "test")
    room = test_insert_room("Lobby")

    users = [user, user2, user3, user4]

    message1 = test_insert_message(user["id"], room["id"], "NONE", "I'm message one")
    message2 = test_insert_message(user2["id"], room["id"], "NONE", "I'm message two")
    dm = test_insert_message(user2["id"], "NONE", user["id"], "I'm a dm")

    print("Testing NONE triggers")
    try:
        test_insert_message("NONE", room["id"], "NONE", "userid is NONE")
    except sqlite3.Error as e:
        print(e)
    try:
        test_insert_message(
            user["id"], "NONE", "NONE", "roomid and target_userid is NONE"
        )
    except sqlite3.Error as e:
        print(e)

    test_insert_blacklist(user["id"], user2["id"])

    print("Testing blacklist trigger")

    try:
        dm = test_insert_message(user2["id"], "NONE", user["id"], "I'm another dm")
    except sqlite3.Error as e:
        print(e)

    # for i in range(50):
    #     u = users[i % len(users)]
    #     test_insert_message(u["id"], room["id"], "NONE", f"I'm message {i+1}")

    test_get_room_messages(room["id"])

    newtime = datetime.fromisoformat("2022-09-13 13:50:00.564+00:00")
    # newtime.tzinfo = timezone.utc
    local = newtime.astimezone(datetime.now().tzinfo)
    print(local)


# from datetime import timezone, datetime

# time = datetime.now(timezone.utc)
# timestr = str(time)
# isostr = time.isoformat()
# print(time)
# print(timestr)
# print(isostr)

# newtime = datetime.fromisoformat(isostr)
# local = newtime.astimezone(datetime.now().tzinfo)

# print(newtime)
# print(local)

# import json
# import os
# from typing import Dict, List

# if __name__ == "__main__":
#     base_path = os.path.dirname(os.path.abspath(__file__))
#     in_path = os.path.join(base_path, "networking", "hamlet.json")
#     out_path = os.path.join(base_path, "networking", "hamlet2.json")

#     speaker_id: int = 2
#     speakers: Dict[str, str] = {}
#     hamlet: Dict = None

#     with open(in_path, "r") as in_file:
#         hamlet = json.loads(in_file.read())
#         messages = hamlet.get("hamlet", None)
#         if messages is None or len(messages) == 0:
#             print("Found no messages")

#         for i, message in enumerate(hamlet["hamlet"]):
#             username = message["username"]
#             userid = speakers.get(username, None)
#             if userid is None:
#                 speaker_id = speaker_id + 1
#                 speakers[username] = f"{speaker_id}"
#             hamlet["hamlet"][i]["userid"] = speakers[username]

#     with open(out_path, "w") as out_file:
#         hamlet = json.dumps(hamlet)
#         out_file.write(hamlet)


# from textual.app import App, DockView
# from textual import events
# from textual.widgets import Header, Footer, Button, ButtonPressed
# from textual.geometry import Size


# class Director:
#     def __init__(self, app):
#         self.app = app
#         self.scenes = {}

#     def create_scene(self, name):
#         if name in self.scenes:
#             raise ValueError(f"Scene {name} already exists")
#         self.scenes[name] = DockView(name=name)
#         return self.scenes[name]

#     def delete_scene(self, name):
#         del self.scenes[name]

#     async def set_scene(self, scene_name):
#         view = self.scenes[scene_name]
#         resize = events.Resize(self.app, Size(self.app.console.size))
#         await self.pop_view()
#         await view.on_resize(resize)
#         await self.app.push_view(view)

#     async def pop_view(self) -> None:
#         if len(self.app._view_stack) > 1:
#             view = self.app._view_stack.pop()
#             await self.app.remove(view)
#             self.app.refresh()


# class MultiPageApp(App):
#     async def on_load(self, event: events.Load) -> None:
#         await self.bind("q", "quit", "Quit")
#         await self.bind("escape", "pop_view", "Escape")
#         await self.bind("a", "set_scene('Alpha')", "Alpha")
#         await self.bind("b", "set_scene('Beta')", "Beta")

#     async def on_mount(self, event: events.Mount) -> None:
#         def make_button(text: str, style: str) -> Button:
#             return Button(f"| {text} |", style=style, name=text)

#         async def assemble(view, header, footer, names, styles):
#             await view.dock(header, edge="top")
#             await view.dock(footer, edge="bottom")
#             grid = await view.dock_grid()
#             btns = [make_button(n, s) for n, s in zip(names, styles)]

#             grid.add_column("c1", fraction=1, max_size=30)
#             grid.add_column("c2", fraction=1, max_size=30)
#             grid.add_row("r1", fraction=1, max_size=10)
#             grid.add_row("r2", fraction=1, max_size=10)
#             grid.place(*btns)

#         self.director = Director(self)
#         header, footer = Header(), Footer()
#         h_style, a_style, b_style = "red", "blue", "green"

#         await assemble(self.view, header, footer, ["Alpha", "Beta"], [a_style, b_style])

#         view = self.director.create_scene("Alpha")
#         await assemble(view, header, footer, ["Home", "Beta"], [h_style, b_style])

#         view = self.director.create_scene("Beta")
#         await assemble(view, header, footer, ["Home", "Alpha"], [h_style, a_style])

#     async def action_pop_view(self):
#         await self.director.pop_view()

#     async def action_set_scene(self, scene_name):
#         await self.director.set_scene(scene_name)

#     async def handle_button_pressed(self, message: ButtonPressed) -> None:
#         assert isinstance(message.sender, Button)
#         button_name = message.sender.name
#         if button_name == "Home":
#             await self.director.pop_view()
#         else:
#             await self.director.set_scene(button_name)


# MultiPageApp.run(title="Multi Page App", log="textual.log")
