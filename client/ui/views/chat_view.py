from typing import Dict, List, Tuple
from collections import namedtuple

import textual.events as events
from textual import log, messages
from textual.scrollbar import ScrollTo
from textual.widgets import ScrollView

from rich import box
from rich.box import Box
from rich.console import Group
from rich.panel import Panel
from rich.columns import Columns
from rich.style import Style

from ..header import Header

from textual_inputs import TextInput
from ...chat_client_protocol import Chatroom
from ..messages import (
    ChatMessage,
    CommandMessage,
    ErrorMessage,
    HideView,
    ListRoomsMessage,
    ListUsersMessage,
    ServerResponseMessage,
    ShowView,
)
from ..tabview import TabView
from common import FIELDS_CHAT_MESSAGE, User, COMMAND_TYPES

other_style = Style(color="rgb(175, 225, 255)")
other_border_style = Style(color="rgb(175, 175, 255)")

my_style = Style(color="rgb(200, 255, 200)")
my_border_style = Style(color="rgb(150, 255, 150)")

error_style = Style(color="rgb(255, 200, 200)")
error_border_style = Style(color="rgb(255, 150, 150)")

server_response_style = Style(color="rgb(200, 200, 50)")
server_response_border_style = Style(color="rgb(100, 100, 0)")
server_box_style = box.SIMPLE

dm_style = Style(color="rgb(225, 225, 255)", bgcolor="rgb(50, 50, 50)")
dm_border_style = Style(color="rgb(255, 255, 255)", bgcolor="rgb(50, 50, 50)")

header_style = Style(color="rgb(25, 25, 100)", bgcolor="rgb(200, 200, 200)")

# from ....common import MESSAGE_TYPE, MESSAGE_TYPES, FIELDS_CHAT_MESSAGE
_commands = namedtuple(
    "COMMANDS",
    [
        "blacklist",
        "clear",
        "create_room",
        "dm",
        "join_room",
        "list",
        "logout",
        "unblock",
    ],
)

COMMANDS = _commands(
    blacklist="\\block",
    clear="\\clear",
    create_room="\\create",
    dm="\\dm",
    join_room="\\join",
    list="\\list",
    logout="\\logout",
    unblock="\\unblock",
)


class ChatView(TabView):
    """
    Chat window to display chat history and send new messages
    """

    _message_panels: List[Panel] = []
    _user: User | None = None
    _room: Chatroom | None = None

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)

    async def init(self):
        grid = await self.dock_grid()
        grid.add_column(name="center", fraction=1)
        grid.add_row(name="room_name", size=3)
        grid.add_row(name="top", fraction=1)
        grid.add_row(name="bottom", size=3)

        grid.add_areas(
            header="center,room_name",
            chat="center,top",
            message_input="center,bottom",
        )

        self._header = Header(tall=True, style=header_style)
        self._chat_scrollview = ChatHistoryView("", name="chat_view")
        self._message_input = TextInput(
            name="message_input", title="Message", placeholder="Type message here"
        )

        self.add_taborder(self._message_input, self._chat_scrollview)

        grid.place(
            header=self._header,
            chat=self._chat_scrollview,
            message_input=self._message_input,
        )

    async def on_key(self, event: events.Key) -> None:
        await super().on_key(event)
        if event.key == "enter":
            event.prevent_default().stop()
            message = self._message_input.value
            self._message_input.value = ""

            message = message.strip()
            if len(message) == 0:
                return

            if message.startswith("\\"):
                return await self.parse_command(message)

            e = ChatMessage(self, message)
            log(e)
            await self.emit(e)

    async def parse_command(self, command: str):
        command_parts = command.split(" ", maxsplit=1)
        cmd = command_parts[0].strip()
        message: CommandMessage | None = None
        match cmd:
            case COMMANDS.blacklist:
                if len(command_parts) < 2:
                    error_message = ErrorMessage(
                        self, "", "Must type a username to blacklist them"
                    )
                    return await self.handle_error(error_message)
                blocked_username = command_parts[1].strip()

                message = CommandMessage(self, COMMAND_TYPES.block, blocked_username)
            case COMMANDS.create_room:
                if len(command_parts) < 2:
                    error_message = ErrorMessage(
                        self, "", "Can not create room: Missing room name"
                    )
                    return await self.handle_error(error_message)
                roomname = command_parts[1].strip()
                if len(roomname) == 0:
                    return
                message = CommandMessage(self, COMMAND_TYPES.create_room, roomname)
            case COMMANDS.clear:
                await self.clear_history()
            case COMMANDS.dm:
                if len(command_parts) < 2:
                    error_message = ErrorMessage(
                        self, "", "Can not send DM. Missing user or message."
                    )
                    return await self.handle_error(error_message)

                content = command_parts[1].strip()
                if len(content) == 0:
                    return
                message = CommandMessage(self, COMMAND_TYPES.dm, content)
            case COMMANDS.join_room:
                if len(command_parts) < 2:
                    error_message = ErrorMessage(
                        self, "", "Can not join room: Missing room name"
                    )
                    return await self.handle_error(error_message)
                roomname = command_parts[1].strip()
                if len(roomname) == 0:
                    return
                message = CommandMessage(self, COMMAND_TYPES.join_room, roomname)
            case COMMANDS.list:
                if len(command_parts) < 2:
                    error_message = ErrorMessage(
                        self,
                        "",
                        "Must specify [bold]\\list rooms,[/bold] or [bold]\\list users[/bold]",
                    )
                    return await self.handle_error(error_message)
                list_type = command_parts[1].strip()
                if not (list_type == "rooms" or list_type == "users"):
                    error_message = ErrorMessage(
                        self,
                        "",
                        "Must specify [bold]\\list rooms,[/bold] or [bold]\\list users[/bold]",
                    )
                    return await self.handle_error(error_message)

                if command_parts[1] == "rooms":
                    message = CommandMessage(self, COMMAND_TYPES.list_rooms)
                else:
                    message = CommandMessage(self, COMMAND_TYPES.list_users)
            case COMMANDS.logout:
                message = CommandMessage(self, COMMAND_TYPES.logout)
            case COMMANDS.unblock:
                if len(command_parts) < 2:
                    error_message = ErrorMessage(
                        self, "", "Must type a username to blacklist them"
                    )
                    return await self.handle_error(error_message)
                blocked_username = command_parts[1].strip()

                message = CommandMessage(self, COMMAND_TYPES.unblock, blocked_username)

        if message is None:
            return

        await self.emit(message)

    async def on_hide_view(self, event: HideView):
        if event.view_name != self.name:
            return
        for widget in self.widgets:
            widget.visible = False
        event.prevent_default().stop()

    async def on_show_view(self, event: ShowView):
        if event.view_name != self.name:
            return
        for widget in self.widgets:
            widget.visible = True
        event.prevent_default().stop()
        if hasattr(self, "_message_input"):
            await self._message_input.focus()

    async def handle_error(self, event: ErrorMessage):
        if event is None:
            return
        event.prevent_default().stop()
        message = {
            FIELDS_CHAT_MESSAGE.authorname: "SERVER",
            FIELDS_CHAT_MESSAGE.message: event.error_message,
        }

        p = message_to_panel(
            message=message,
            style=error_style,
            border_style=error_border_style,
            box_style=server_box_style,
            title_align="center",
        )

        self._message_panels.append(p)
        group = Group(*self._message_panels) if len(self._message_panels) > 0 else ""
        await self._chat_scrollview.update(group, home=False)

    async def handle_list_rooms(self, message: ListRoomsMessage):
        if message is None:
            return
        message.prevent_default().stop()
        rooms = message.rooms
        msg: Dict[str, str] | None = None
        if len(rooms) == 0:
            msg = {
                FIELDS_CHAT_MESSAGE.authorname: "SERVER",
                FIELDS_CHAT_MESSAGE.message: "Lobby",
            }
        else:
            msg = {
                FIELDS_CHAT_MESSAGE.authorname: "SERVER",
                FIELDS_CHAT_MESSAGE.message: Columns(
                    rooms, equal=True, column_first=True, expand=True, title="Rooms"
                ),
            }

        if msg is None:
            return

        p = message_to_panel(
            message=msg,
            style=server_response_style,
            border_style=server_response_border_style,
            box_style=server_box_style,
            title_align="center",
        )

        self._message_panels.append(p)
        group = Group(*self._message_panels) if len(self._message_panels) > 0 else ""
        await self._chat_scrollview.update(group, home=False)

    async def handle_list_users(self, message: ListUsersMessage):
        if message is None:
            return

        message.prevent_default().stop()
        users = message.users
        msg: Dict[str, str] | None = None
        if len(users) == 0:
            msg = {
                FIELDS_CHAT_MESSAGE.authorname: "SERVER",
                FIELDS_CHAT_MESSAGE.message: "Empty room",
            }
        else:
            msg = {
                FIELDS_CHAT_MESSAGE.authorname: "SERVER",
                FIELDS_CHAT_MESSAGE.message: Columns(
                    users, equal=True, column_first=True, expand=True, title="Users"
                ),
            }

        if msg is None:
            return

        p = message_to_panel(
            message=msg,
            style=server_response_style,
            border_style=server_response_border_style,
            box_style=server_box_style,
            title_align="center",
        )

        self._message_panels.append(p)
        group = Group(*self._message_panels) if len(self._message_panels) > 0 else ""
        await self._chat_scrollview.update(group, home=False)

    async def handle_server_response(self, message: ServerResponseMessage) -> None:
        if message is None or message.response is None:
            return

        response = message.response.strip()
        if len(response) == 0:
            return

        msg = {
            FIELDS_CHAT_MESSAGE.authorname: "SERVER",
            FIELDS_CHAT_MESSAGE.message: response,
        }

        p = message_to_panel(
            message=msg,
            style=server_response_style,
            border_style=server_response_border_style,
            box_style=server_box_style,
            title_align="center",
        )

        self._message_panels.append(p)
        group = Group(*self._message_panels) if len(self._message_panels) > 0 else ""
        await self._chat_scrollview.update(group, home=False)

    async def add_history_message(self, message: dict, active_user: User) -> None:
        """Adds a single message to the chat history window

        Args:
            message (dict): Message to be added
            active_user (str): username of current user, used for styling
        """
        if message is None:
            return

        mine = message.get(FIELDS_CHAT_MESSAGE.authorid, "") == active_user.userid

        style, border_style = get_styles(message, mine)

        # mine = message[FIELDS_CHAT_MESSAGE.authorid] == active_user.userid
        # style = my_style if mine else other_style
        # border_style = my_border_style if mine else other_border_style
        title_style = "italic" if mine else "bold"
        title_align = "right" if mine else "left"
        p = message_to_panel(
            message=message,
            style=style,
            border_style=border_style,
            title_style=title_style,
            title_align=title_align,
        )
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
            mine = message.get(FIELDS_CHAT_MESSAGE.authorid, "") == active_user.userid
            style, border_style = get_styles(message, mine)
            title_style = "italic" if mine else "bold"
            title_align = "right" if mine else "left"
            p = message_to_panel(
                message=message,
                style=style,
                border_style=border_style,
                title_style=title_style,
                title_align=title_align,
            )
            self._message_panels.append(p)
        group = Group(*self._message_panels) if len(self._message_panels) > 0 else ""
        await self._chat_scrollview.update(group, home=False)

    async def clear_history(self):
        """
        Clears all message panels from chat history window
        """
        self._message_panels.clear()
        await self._chat_scrollview.update("")


def get_styles(message: Dict[str, str], mine: bool) -> Tuple[Style, Style]:

    target_userid = message.get(FIELDS_CHAT_MESSAGE.target_userid, "")
    if len(target_userid) > 0:
        return dm_style, dm_border_style

    if mine:
        return my_style, my_border_style

    return other_style, other_border_style


def message_to_panel(
    message: dict,
    style: Style,
    border_style: Style,
    box_style: Box = box.ROUNDED,
    title_style: str = "bold",
    title_align: str = "left",
) -> Panel:
    un = message.get(FIELDS_CHAT_MESSAGE.authorname)
    m = message.get(FIELDS_CHAT_MESSAGE.message)
    match title_style:
        case "bold":
            title = f"[bold]{un}[/bold]"
        case "italic":
            title = f"[italic]{un}[/italic]"
        case _:
            title = un

    p = Panel(
        m or "",
        box=box_style,
        title=title,
        title_align=title_align,
        padding=(1, 1, 1, 6),
        style=style,
        border_style=border_style,
    )
    return p


class ChatHistoryView(ScrollView):
    async def handle_window_change(self, message: messages.Message) -> None:
        # should_scroll = self.max_scroll_y - self.y < 25
        await super().handle_window_change(message)
        # if not should_scroll:
        #     return

        if self.app.focused == self:
            return

        bottom = self.max_scroll_y
        scrollTo = ScrollTo(self, 0, bottom)
        await self.handle_scroll_to(scrollTo)
