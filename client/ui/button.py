from rich.console import RenderableType

from textual import log
from textual.widget import Widget
from textual.widgets._button import ButtonRenderable, ButtonPressed
from textual.reactive import Reactive
import textual.events as events

from .colors import ButtonStyle


class Button(Widget):

    _disabled: Reactive[bool] = Reactive(False)
    _label: Reactive[RenderableType] = Reactive("")
    _focus: Reactive[bool] = Reactive(False)
    _hover: Reactive[bool] = Reactive(False)
    _active: Reactive[bool] = Reactive(False)
    _button_style: Reactive[ButtonStyle] = Reactive(ButtonStyle())

    def __init__(
        self,
        name: str | None = None,
        label: RenderableType = "Button",
        disabled: bool = False,
        button_style: ButtonStyle = None,
    ) -> None:
        """Creates a button widget with custom styling

        Args:
            name (str | None, optional): unique key for this widget. Defaults to None.
            label (RenderableType, optional): text to be displayed on the button. Defaults to "Button".
            disabled (bool, optional): Enables/Disables this button. Defaults to False.
            button_style (ButtonStyle, optional): Styles for the different states of this button. Defaults to None.
        """
        super().__init__(name=name)
        self._disabled = disabled
        self._label = label
        if button_style is not None:
            self._button_style = button_style

        self.style = (
            self._button_style.disabled if self._disabled else self._button_style.normal
        )

    @property
    def has_focus(self) -> bool:
        return self._focus

    @property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, label: str):
        self._label = label

    @property
    def button_style(self) -> ButtonStyle:
        return self._button_style

    @button_style.setter
    def button_style(self, button_style: ButtonStyle) -> None:
        self._button_style = button_style

    async def on_focus(self, event: events.Focus) -> None:
        if self._disabled:
            return
        self._focus = True
        self.style = self._button_style.hover

    async def on_blur(self, event: events.Blur) -> None:
        if self._disabled:
            return
        self._focus = False
        self.style = self._button_style.normal

    async def on_enter(self, event: events.Enter) -> None:
        if self._disabled:
            return
        self._hover = True
        self.style = self._button_style.hover

    async def on_leave(self, event: events.Leave) -> None:
        if self._disabled:
            return
        self._hover = False
        self._active = False
        self.style = self._button_style.normal

    async def on_mouse_down(self, event: events.MouseDown) -> None:
        if self._disabled:
            return
        self.style = self._button_style.active

    async def on_mouse_up(self, event: events.MouseUp) -> None:
        if self._disabled:
            return
        self.style = self._button_style.normal

    async def on_click(self, event: events.Click) -> None:
        event.prevent_default().stop()
        if self._disabled:
            return
        b = ButtonPressed(self)
        log(b.name)
        await self.emit(ButtonPressed(self))

    def render(self) -> RenderableType:
        return ButtonRenderable(self._label, style=self.style)
