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


class Error(Message):
    def __init__(
        self, sender: MessageTarget, error_type: str, error_message: str
    ) -> None:
        super().__init__(sender)
        self.error_type = error_type
        self.error_message = error_message
