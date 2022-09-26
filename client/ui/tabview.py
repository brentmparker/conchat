from abc import ABC, abstractmethod
from typing import List
from textual.views._dock_view import DockView
from textual.widget import Widget
import textual.events as events
from textual_inputs.text_input import InputOnFocus

from .messages import ErrorMessage


class TabView(DockView, ABC):

    _tab_idx: int = 0
    _tabs: List[Widget] = []
    _focused: Widget = None

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)
        self._tab_idx = 0
        self._tabs = []

    @abstractmethod
    async def init(self):
        pass

    async def on_key(self, event: events.Key) -> None:
        if event.key == "ctrl+i" or event.key == "tab":
            event.prevent_default().stop()
            self._tab_idx = (self._tab_idx + 1) % len(self._tabs)
            await self._tabs[self._tab_idx].focus()
        elif event.key == "shift+tab":
            event.prevent_default().stop()
            self._tab_idx = (self._tab_idx - 1) % len(self._tabs)
            await self._tabs[self._tab_idx].focus()

    def reset_tabs(self):
        self._tabs.clear()
        self._tab_idx = 0
        self._focused = None

    def add_taborder(self, *widgets) -> None:
        for widget in widgets:
            if widget in self._tabs:
                continue
            self._tabs.append(widget)

    def remove_taborder(self, *widgets) -> None:
        for widget in widgets:
            if widget not in self._tabs:
                continue
            self._tabs.remove(widget)

    async def on_focus(self, event: events.Focus) -> None:
        if event.sender in self._tabs:
            self._tab_idx = self._tabs.index(event.sender)
            self._focused = event.sender

    async def handle_input_on_focus(self, event: InputOnFocus) -> None:
        if event.sender in self._tabs:
            self._tab_idx = self._tabs.index(event.sender)
            self._focused = event.sender

    @abstractmethod
    async def handle_error(self, message: ErrorMessage):
        pass
