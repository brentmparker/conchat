from textual.reactive import Reactive, watch
from textual.widget import Widget
from textual import events

from rich.style import StyleType
from rich.text import Text
from rich.repr import Result
from rich.panel import Panel
from rich.console import RenderableType


class Header(Widget):

    tall: Reactive[bool] = Reactive(True, layout=True)
    style: Reactive[StyleType] = Reactive("white on blue")
    title: Reactive[str] = Reactive("")
    sub_title: Reactive[str] = Reactive("")

    def __init__(
        self,
        name: str | None = None,
        tall: bool = True,
        style: StyleType = "white on blue",
    ) -> None:
        super().__init__(name)
        self.tall = tall
        self.style = style

    @property
    def full_title(self) -> str:
        return f"{self.title} - {self.sub_title}" if self.sub_title else self.title

    def __rich_repr__(self) -> Result:
        yield self.title

    async def watch_tall(self, tall: bool) -> None:
        self.layout_size = 3 if tall else 1

    def render(self) -> RenderableType:
        header_text = Text(
            self.full_title,
            style=self.style,
            justify="center",
            no_wrap=True,
            overflow="crop",
        )
        header: RenderableType = (
            Panel(header_text, style=self.style) if self.tall else header_text
        )
        return header

    async def on_mount(self, event: events.Mount) -> None:
        async def set_title(title: str) -> None:
            self.title = title

        async def set_sub_title(sub_title: str) -> None:
            self.sub_title = sub_title

        watch(self.app, "title", set_title)
        watch(self.app, "sub_title", set_sub_title)

    async def on_click(self, event: events.Click) -> None:
        self.tall = not self.tall
