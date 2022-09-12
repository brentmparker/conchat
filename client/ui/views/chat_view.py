from typing import Dict, List

import textual.events as events
from textual import log, messages
from textual.scrollbar import ScrollTo
from textual.views._grid_view import GridView
from textual.widgets import ScrollView
from textual.layout import Layout

from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.style import Style

from textual_inputs import TextInput
from ..messages import ChatMessage, HideView, ShowView
from ..tabview import TabView
from common import MESSAGE_TYPE, MESSAGE_TYPES, FIELDS_CHAT_MESSAGE, User

# from ....common import MESSAGE_TYPE, MESSAGE_TYPES, FIELDS_CHAT_MESSAGE


class ChatView(TabView):
    """
    Chat window to display chat history and send new messages
    """

    _message_panels: List[Panel] = []

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)

    async def init(self):
        grid = await self.dock_grid()
        grid.add_column(name="center", fraction=1)
        grid.add_row(name="top", fraction=1)
        grid.add_row(name="bottom", size=3)

        grid.add_areas(chat="center,top", message_input="center,bottom")

        self._chat_scrollview = ChatHistoryView("", name="chat_view")
        self._message_input = TextInput(
            name="message_input", title="Message", placeholder="Type message here"
        )

        self.add_taborder(self._message_input, self._chat_scrollview)

        grid.place(chat=self._chat_scrollview, message_input=self._message_input)

    async def on_key(self, event: events.Key) -> None:
        await super().on_key(event)
        if event.key == "enter":
            event.prevent_default().stop()
            message = self._message_input.value
            self._message_input.value = ""

            message = message.strip()
            if len(message) == 0:
                return

            e = ChatMessage(self, message)
            log(e)
            await self.emit(e)

    async def on_hide_view(self, event: HideView):
        if event.view_name != self.name:
            return
        event.prevent_default().stop()

    async def on_show_view(self, event: ShowView):
        if event.view_name != self.name:
            return
        event.prevent_default().stop()
        if hasattr(self, "_message_input"):
            await self._message_input.focus()

    async def add_history_message(self, message: dict, active_user: User) -> None:
        """Adds a single message to the chat history window

        Args:
            message (dict): Message to be added
            active_user (str): username of current user, used for styling
        """
        if message is None:
            return
        p = message_to_panel(message, active_user)
        self._message_panels.append(p)
        group = Group(*self._message_panels) if len(self._message_panels) > 0 else ""
        await self._chat_scrollview.update(group, home=False)

    async def add_history_messages(
        self, messages: List[Dict[str, str]], active_user: User
    ) -> None:
        """Adds all messages in a list to current chat history panel

        Args:
            messages (List[dict]): A list of chat messages
            active_user (str): The current logged in user, used to apply styles
        """
        for message in messages:
            p = message_to_panel(message, active_user)
            self._message_panels.append(p)
        group = Group(*self._message_panels) if len(self._message_panels) > 0 else ""
        await self._chat_scrollview.update(group, home=False)

    async def clear_history(self):
        """
        Clears all message panels from chat history window
        """
        self._message_panels.clear()
        await self._chat_scrollview.update("")


other_style = Style(color="rgb(150, 200, 255)")
other_border_style = Style(color="rgb(150, 150, 255)")
my_style = Style(color="rgb(200, 255, 200)")
my_border_style = Style(color="rgb(150, 255, 150)")


def message_to_panel(message: dict, active_user: User) -> Panel:
    id = message.get(FIELDS_CHAT_MESSAGE.authorid)
    un = message.get(FIELDS_CHAT_MESSAGE.authorname)
    m = message.get(FIELDS_CHAT_MESSAGE.message)
    # eventuall parse date here
    mine = id == active_user.userid
    p = Panel(
        m or "",
        box=box.ROUNDED,
        title=f"[italic]{un}[/italic]" if mine else f"[bold]{un}[/bold]",
        title_align="right" if mine else "left",
        padding=(1, 1, 1, 6),
        style=my_style if mine else other_style,
        border_style=my_border_style if mine else other_border_style,
    )
    return p


class ChatHistoryView(ScrollView):
    async def handle_window_change(self, message: messages.Message) -> None:
        should_scroll = self.max_scroll_y - self.y < 25
        await super().handle_window_change(message)
        if not should_scroll:
            return
        bottom = self.max_scroll_y
        scrollTo = ScrollTo(self, 0, bottom)
        await self.handle_scroll_to(scrollTo)
        # await self.dispatch_message(scrollTo)
