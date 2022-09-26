import textual.events as events
from textual.widgets._button import ButtonPressed
from ..banner import Banner
from ..button import Button
from ..messages import ErrorMessage, HideView, ShowView
from ..tabview import TabView


BANNER = r"""
 ________  ________  ________   ________  ___  ___  ________  _________   
|\   ____\|\   __  \|\   ___  \|\   ____\|\  \|\  \|\   __  \|\___   ___\ 
\ \  \___|\ \  \|\  \ \  \\ \  \ \  \___|\ \  \\\  \ \  \|\  \|___ \  \_| 
 \ \  \    \ \  \\\  \ \  \\ \  \ \  \    \ \   __  \ \   __  \   \ \  \  
  \ \  \____\ \  \\\  \ \  \\ \  \ \  \____\ \  \ \  \ \  \ \  \   \ \  \ 
   \ \_______\ \_______\ \__\\ \__\ \_______\ \__\ \__\ \__\ \__\   \ \__\
    \|_______|\|_______|\|__| \|__|\|_______|\|__|\|__|\|__|\|__|    \|__|
"""

BANNER_2 = r"""
   ______            ________          __ 
  / ____/___  ____  / ____/ /_  ____ _/ /_
 / /   / __ \/ __ \/ /   / __ \/ __ `/ __/
/ /___/ /_/ / / / / /___/ / / / /_/ / /_  
\____/\____/_/ /_/\____/_/ /_/\__,_/\__/  
"""


class IntroView(TabView):
    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)

    async def init(self):
        grid = await self.dock_grid()

        grid.set_gap(1, 1)
        grid.add_column(name="c1", fraction=1)
        grid.add_column(name="c2", fraction=1)
        grid.add_column(name="c3", fraction=1)
        grid.add_column(name="c4", fraction=1)

        grid.add_row(name="r1", fraction=2)
        grid.add_row(name="r2", size=5)
        grid.add_row(name="r3", fraction=1)

        grid.add_areas(
            banner_area="c1-start|c4-end,r1", signup_area="c2,r2", signin_area="c3,r2"
        )

        banner = Banner(banner=BANNER)
        self._signup_button = Button(name="signup_btn", label="Join Us!")
        self._signin_button = Button(name="signin_btn", label="Sign In")

        self.reset_tabs()
        self.add_taborder(self._signup_button, self._signin_button)

        grid.place(
            banner_area=banner,
            signup_area=self._signup_button,
            signin_area=self._signin_button,
        )

    async def on_key(self, event: events.Key):
        await super().on_key(event)
        if event.key == "enter":
            await self.emit(
                ShowView(
                    sender=self,
                    view_name="signupView"
                    if self._signup_button.has_focus
                    else "signinView",
                )
            )

    async def handle_button_pressed(self, event: ButtonPressed):
        if event.sender == self._signup_button:
            event.prevent_default().stop()
            await self.emit(
                ShowView(
                    sender=self,
                    view_name="signupView",
                )
            )
        elif event.sender == self._signin_button:
            event.prevent_default().stop()
            await self.emit(
                ShowView(
                    sender=self,
                    view_name="signinView",
                )
            )

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
        if hasattr(self, "_signin_button"):
            await self._signin_button.focus()

    async def handle_error(self, event: ErrorMessage):
        pass
