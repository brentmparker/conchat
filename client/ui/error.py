from textual.widget import Widget
from textual.reactive import Reactive
from rich.text import Text
from rich.align import Align
from rich.style import Style
from rich.console import RenderableType


class Error(Widget):
    error_message: Reactive[str] = Reactive("")

    def __init__(self, name: str | None = None, error_message: str = "") -> None:
        super().__init__(name)
        self.error_message = error_message
        self.style = Style(color="red")

    def render(self) -> RenderableType:
        return Align(
            renderable=Text(self.error_message, overflow="ellipsis"),
            align="left",
            vertical="middle",
            style=self.style,
        )
