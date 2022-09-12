from textual.widget import Widget
from textual.reactive import Reactive
from rich.console import RenderableType
from rich.align import Align


class Banner(Widget):
    banner: Reactive[str] = Reactive("")

    def __init__(self, name: str | None = None, banner: str = "") -> None:
        super().__init__(name)
        self.banner = banner

    def render(self) -> RenderableType:
        return Align.center(self.banner, vertical="middle")
