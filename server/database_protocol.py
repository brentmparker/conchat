# server/database_protocol.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class AbstractDatabase(ABC):
    @abstractmethod
    def _initialize_database(self, drop: bool = False) -> None:
        pass

    @abstractmethod
    def open_connection(self) -> Any:
        pass

    @abstractmethod
    def insert_chat_message(
        self,
        authorid: str,
        roomid: str | None,
        target_userid: str | None,
        message: str,
    ) -> Dict[str, str]:
        pass

    @abstractmethod
    def insert_user(self, username: str, password: str) -> Dict[str, str]:
        pass

    @abstractmethod
    def insert_room(self, name: str) -> Dict[str, str]:
        pass

    @abstractmethod
    def insert_blacklist(self, userid: str, blocked_userid: str):
        pass

    @abstractmethod
    def get_room_messages(self, roomid: str, limit: int = 30) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    def get_user_by_username(self, username: str) -> Dict[str, str]:
        pass
