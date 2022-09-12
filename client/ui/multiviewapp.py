from asyncio import events
from typing import Dict, Type
from textual import events
from textual.driver import Driver
from textual.app import App, ViewType
from textual.geometry import Size
from .messages import HideView, ShowView


class Director:
    def __init__(self, app: App) -> None:
        self.app = app
        self.views: Dict[ViewType] = {}

    def add_view(self, view: ViewType) -> ViewType:
        if view.name in self.views:
            raise ValueError(f"View {view.name} already exists")

        self.views[view.name] = view
        return view

    def remove_view(self, name: str) -> ViewType:
        if name not in self.views:
            raise ValueError(f"View {name} does not exist")
        del self.views[name]

    async def push_view(self, name: str):
        if name not in self.views:
            raise ValueError(f"View {name} does not exist")

        view: ViewType = self.views[name]
        resize = events.Resize(
            self.app, Size(self.app.console.size.width, self.app.console.size.height)
        )
        await self.pop_view()
        await view.on_resize(resize)
        await self.app.push_view(view)
        # self.app.refresh()
        await self.app.on_resize(resize)
        await view.dispatch_message(ShowView(self, name))

    async def pop_view(self) -> None:
        if len(self.app._view_stack) > 1:
            view = self.app._view_stack.pop()
            await view.dispatch_message(HideView(self.app, view.name))
            await self.app.remove(view)
            # self.app.refresh()


class MultiviewApp(App):
    _director: Director

    def __init__(
        self,
        screen: bool = True,
        driver_class: Type[Driver] | None = None,
        log: str = "",
        log_verbosity: int = 1,
        title: str = "Textual Application",
    ):
        super().__init__(screen, driver_class, log, log_verbosity, title)
        self._director = Director(app=self)

    async def swap_to_view(self, name: str):
        await self._director.push_view(name)

    def add_view(self, view: ViewType):
        if view is None:
            return
        self._director.add_view(view)

    async def on_hide_view(self, event: HideView):
        pass

    async def on_show_view(self, event: ShowView):
        if event.view_name not in self._director.views:
            return
        event.prevent_default().stop()
        await self.swap_to_view(event.view_name)
