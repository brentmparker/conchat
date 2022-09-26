import textual.events as events
from textual.layout import Layout
from textual.widgets._button import ButtonPressed
from textual_inputs import TextInput
from ..messages import ErrorMessage, HideView, Login, ShowView, InvalidLogin
from ..tabview import TabView
from ..banner import Banner
from ..button import Button
from ..error import Error

BANNER = r"""
 ________  ___  ________  ________           ___  ________      
|\   ____\|\  \|\   ____\|\   ___  \        |\  \|\   ___  \    
\ \  \___|\ \  \ \  \___|\ \  \\ \  \       \ \  \ \  \\ \  \   
 \ \_____  \ \  \ \  \  __\ \  \\ \  \       \ \  \ \  \\ \  \  
  \|____|\  \ \  \ \  \|\  \ \  \\ \  \       \ \  \ \  \\ \  \ 
    ____\_\  \ \__\ \_______\ \__\\ \__\       \ \__\ \__\\ \__\
   |\_________\|__|\|_______|\|__| \|__|        \|__|\|__| \|__|
   \|_________|                                                 
"""

BANNER_2 = r"""
   _____ _                _     
  / ___/(_)___ _____     (_)___ 
  \__ \/ / __ `/ __ \   / / __ \
 ___/ / / /_/ / / / /  / / / / /
/____/_/\__, /_/ /_/  /_/_/ /_/ 
       /____/                   
"""


class SigninView(TabView):
    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)

    async def init(self):
        grid = await self.dock_grid()

        grid.set_gap(1, 1)

        grid.add_column(name="c1", fraction=1)
        grid.add_column(name="c2", fraction=1)
        grid.add_column(name="c3", fraction=1)
        grid.add_column(name="c4", fraction=1)

        grid.add_row(name="r1", fraction=3)
        grid.add_row(name="r2", size=3)
        grid.add_row(name="r3", size=3)
        grid.add_row(name="r4", size=1)
        grid.add_row(name="r5", size=3)
        grid.add_row(name="r6", fraction=1)

        grid.add_areas(
            banner_area="c1-start|c4-end,r1",
            username_area="c2-start|c3-end,r2",
            password_area="c2-start|c3-end,r3",
            error_area="c2-start|c3-end,r4",
            signin_button_area="c2,r5",
            cancel_button_area="c3,r5",
        )

        self._banner = Banner(name="banner", banner=BANNER)

        self._username_input = TextInput(
            name="usernameInput", placeholder="Username", title="Username"
        )
        self._password_input = TextInput(
            name="passwordInput",
            placeholder="Password",
            title="Password",
            password=True,
        )
        self._signin_button = Button(name="signupButton", label="Sign in")
        self._cancel_button = Button(name="cancelButton", label="Cancel")
        self._error = Error(name="error", error_message="")

        self.reset_tabs()
        self.add_taborder(
            self._username_input,
            self._password_input,
            self._signin_button,
            self._cancel_button,
        )

        grid.place(
            banner_area=self._banner,
            username_area=self._username_input,
            password_area=self._password_input,
            signin_button_area=self._signin_button,
            cancel_button_area=self._cancel_button,
            error_area=self._error,
        )

    async def on_key(self, event: events.Key):
        await super().on_key(event)
        if event.key == "enter":
            if self._cancel_button.has_focus:
                await self._cancel_button.dispatch_message(
                    ButtonPressed(self._cancel_button)
                )
            elif self._signin_button.has_focus:
                await self._signin_button.dispatch_message(
                    ButtonPressed(self._signin_button)
                )
            elif self._password_input.has_focus:
                await self._password_input.dispatch_message(
                    ButtonPressed(self._signin_button)
                )

    async def on_hide_view(self, event: HideView):
        if event.view_name != self.name:
            return
        await self.clear()
        for widget in self.widgets:
            widget.visible = False
        event.prevent_default().stop()

    async def on_show_view(self, event: ShowView):
        if event.view_name != self.name:
            return
        for widget in self.widgets:
            widget.visible = True
        event.prevent_default().stop()
        await self._username_input.focus()

    async def handle_button_pressed(self, event: ButtonPressed) -> None:
        if event.sender == self._cancel_button:
            event.prevent_default().stop()
            await self.clear()
            await self.emit(ShowView(self, "introView"))
        elif event.sender == self._signin_button:
            event.prevent_default().stop()
            username = self._username_input.value.strip()
            password = self._password_input.value.strip()

            if len(username) == 0:
                self._error.error_message = "Must enter a username"
                await self._username_input.focus()
                return
            if len(password) == 0:
                self._error.error_message = "Must enter a password"
                await self._password_input.focus()
                return
            await self.emit(Login(self, username=username, password=password))

    async def handle_invalid_login(self, event: InvalidLogin):
        self._error.error_message = "Invalid username or password"
        await self._username_input.focus()

    async def handle_error(self, event: ErrorMessage):
        self._error.error_message = event.error_message
        self._error.refresh()

    async def clear(self):
        self._username_input.value = ""
        self._password_input.value = ""
