from typing import Dict, List
from textual.message import Message, MessageTarget
from textual.events import Event


class ChatMessage(Event):
    message: str | None = None

    def __init__(self, sender: MessageTarget, message: str) -> None:
        super().__init__(sender)
        self.bubble = True
        self.message = message

    def __repr__(self) -> str:
        return f"""
ChatMessage:
    name: {self.name}
    message: {self.message}
    bubble: {self.bubble}
    sender: {self.sender}
        """


class ShowView(Event, bubble=True):
    def __init__(self, sender: MessageTarget, view_name: str) -> None:
        super().__init__(sender)
        self.view_name = view_name


class HideView(Event, bubble=True):
    def __init__(self, sender: MessageTarget, view_name: str) -> None:
        super().__init__(sender)
        self.view_name = view_name


class Register(Message):
    def __init__(self, sender: MessageTarget, username: str, password: str) -> None:
        super().__init__(sender)
        self.username = username
        self.password = password


class InvalidUsername(Message):
    def __init__(self, sender: MessageTarget) -> None:
        super().__init__(sender)


class ListRoomsMessage(Message):
    rooms: List[str] | None = None

    def __init__(self, sender: MessageTarget, rooms: List[str]) -> None:
        super().__init__(sender)
        self.rooms = rooms


class ListUsersMessage(Message):
    users: List[str] | None = None

    def __init__(self, sender: MessageTarget, users: List[str]) -> None:
        super().__init__(sender)
        self.users = users


class Login(Message):
    def __init__(self, sender: MessageTarget, username: str, password: str) -> None:
        super().__init__(sender)
        self.username = username
        self.password = password


class InvalidLogin(Message):
    def __init__(self, sender: MessageTarget) -> None:
        super().__init__(sender)


class Logout(Message):
    def __init__(self, sender: MessageTarget, username: str) -> None:
        super().__init__(sender)
        self.username = username


class ServerResponseMessage(Message):
    response: str | None = None

    def __init__(self, sender: MessageTarget, response: str) -> None:
        super().__init__(sender)
        self.response = response


class ErrorMessage(Message):
    def __init__(
        self, sender: MessageTarget, error_type: str, error_message: str
    ) -> None:
        super().__init__(sender)
        self.error_type = error_type
        self.error_message = error_message


class CommandMessage(Message):
    command_type: str
    command_data: str | None = None

    def __init__(
        self,
        sender: MessageTarget,
        command_type: str,
        command_data: str = None,
    ) -> None:
        super().__init__(sender)
        self.command_type = command_type
        self.command_data = command_data
