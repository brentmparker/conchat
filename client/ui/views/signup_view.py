import textual.events as events
from textual.layout import Layout
from textual.widgets._button import ButtonPressed
from textual_inputs import TextInput
from ..banner import Banner
from ..button import Button
from ..error import Error
from ..messages import HideView, Register, ShowView, InvalidUsername
from ..tabview import TabView

BANNER = r"""
 ________  ___  ________  ________           ___  ___  ________  ___       
|\   ____\|\  \|\   ____\|\   ___  \        |\  \|\  \|\   __  \|\  \      
\ \  \___|\ \  \ \  \___|\ \  \\ \  \       \ \  \\\  \ \  \|\  \ \  \     
 \ \_____  \ \  \ \  \  __\ \  \\ \  \       \ \  \\\  \ \   ____\ \  \    
  \|____|\  \ \  \ \  \|\  \ \  \\ \  \       \ \  \\\  \ \  \___|\ \__\   
    ____\_\  \ \__\ \_______\ \__\\ \__\       \ \_______\ \__\    \|__|   
   |\_________\|__|\|_______|\|__| \|__|        \|_______|\|__|        ___ 
   \|_________|                                                       |\__\
                                                                      \|__|
"""

BANNER_2 = r"""
   _____ _                            __
  / ___/(_)___ _____     __  ______  / /
  \__ \/ / __ `/ __ \   / / / / __ \/ / 
 ___/ / / /_/ / / / /  / /_/ / /_/ /_/  
/____/_/\__, /_/ /_/   \__,_/ .___(_)   
       /____/              /_/          
"""

PASSWORD_MATCH_ERROR = "Passwords must match"
PASSWORD_EMPTY_ERROR = "Must type a password"
USERNAME_EMPTY_ERROR = "Must type a username"
USERNAME_EXISTS_ERROR = "Username already exists"


class SignupView(TabView):
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
        grid.add_row(name="r4", size=3)
        grid.add_row(name="r5", size=3)
        grid.add_row(name="r6", fraction=1)

        grid.add_areas(
            banner_area="c1-start|c4-end,r1",
            username_area="c2-start|c3-end,r2",
            username_error_area="c4,r2",
            password_area="c2-start|c3-end,r3",
            password_confirm_area="c2-start|c3-end,r4",
            password_error_area="c4,r3",
            signup_button_area="c2,r5",
            cancel_button_area="c3,r5",
        )

        self._banner = Banner(name="signupBanner", banner=BANNER)

        self._username_input = TextInput(
            name="usernameInput", placeholder="Username", title="Username"
        )
        self._password_input = TextInput(
            name="passwordInput",
            placeholder="Password",
            title="Password",
            password=True,
        )
        self._password_confirm_input = TextInput(
            name="passwordInput",
            placeholder="Password confirm",
            title="Password confirm",
            password=True,
        )
        self._signup_button = Button(name="signupButton", label="Sign Up!")
        self._cancel_button = Button(name="cancelButton", label="Cancel")
        self._username_error = Error(name="usernameError", error_message="")
        self._password_error = Error(name="passwordError", error_message="")

        self.reset_tabs()
        self.add_taborder(
            self._username_input,
            self._password_input,
            self._password_confirm_input,
            self._signup_button,
            self._cancel_button,
        )

        grid.place(
            banner_area=self._banner,
            username_area=self._username_input,
            username_error_area=self._username_error,
            password_area=self._password_input,
            password_confirm_area=self._password_confirm_input,
            password_error_area=self._password_error,
            signup_button_area=self._signup_button,
            cancel_button_area=self._cancel_button,
        )

    async def on_key(self, event: events.Key):
        await super().on_key(event)

        if event.key == "enter":
            if self._signup_button.has_focus:
                await self._signup_button.dispatch_message(
                    ButtonPressed(self._signup_button)
                )
            elif self._cancel_button.has_focus:
                await self._cancel_button.dispatch_message(
                    ButtonPressed(self._cancel_button)
                )

    async def handle_button_pressed(self, event: ButtonPressed) -> None:
        if event.sender == self._cancel_button:
            event.prevent_default().stop()
            await self.clear()
            await self.emit(ShowView(self, "introView"))
        elif event.sender == self._signup_button:
            event.prevent_default().stop()
            username: str = self._username_input.value.strip()
            password: str = self._password_input.value.strip()
            confirm: str = self._password_confirm_input.value.strip()

            if len(username) == 0:
                self._username_error.error_message = USERNAME_EMPTY_ERROR
                self._username_error.refresh()
                await self._username_input.focus()
                return
            else:
                self._username_error.error_message = ""
                self._username_error.refresh()

            if len(password) == 0:
                self._password_error.error_message = PASSWORD_EMPTY_ERROR
                self._password_error.refresh()
                await self._password_input.focus()
                return
            elif password != confirm:
                self._password_error.error_message = PASSWORD_MATCH_ERROR
                self._password_error.refresh()
                await self._password_input.focus()
            else:
                self._password_error.error_message = ""
                self._password_error.refresh()
                await self.emit(Register(self, username=username, password=password))

    async def handle_invalid_username(self, event: InvalidUsername):
        self._username_error.error_message = "Please try another username"
        self._password_error.error_message = ""
        self._username_error.refresh()
        self._password_error.refresh()
        await self._username_input.focus()

    async def on_hide_view(self, event: HideView):
        if event.view_name != self.name:
            return
        event.prevent_default().stop()
        self._username_input.value = ""
        self._password_input.value = ""
        self._password_confirm_input = ""

        for widget in self.widgets:
            widget.visible = False

    async def on_show_view(self, event: ShowView):
        if event.view_name != self.name:
            return
        for widget in self.widgets:
            widget.visible = True
        event.prevent_default().stop()
        await self._username_input.focus()

    async def clear(self):
        self._username_input.value = ""
        self._password_input.value = ""
        self._password_confirm_input = ""
        self._username_error.error_message = ""
        self._password_error.error_message = ""
        self.refresh()
