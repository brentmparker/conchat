from datetime import timezone, datetime


def _args_to_string(*args, **kwargs) -> str:
    print(kwargs)
    s = [f"{k}: {v}" for k, v in kwargs.items()]
    return "\n\t".join(s)


one = "one"
two = "two"
three = "three"
print(f"Test:\n\t{_args_to_string(vone=one, vtwo=two, vthree=three)}")

# time = datetime.now(timezone.utc)
# timestr = str(time)
# isostr = time.isoformat()
# print(time)
# print(timestr)
# print(isostr)

# newtime = datetime.fromisoformat(isostr)
# local = newtime.astimezone(datetime.now().tzinfo)

# print(newtime)
# print(local)

# import json
# import os
# from typing import Dict, List

# if __name__ == "__main__":
#     base_path = os.path.dirname(os.path.abspath(__file__))
#     in_path = os.path.join(base_path, "networking", "hamlet.json")
#     out_path = os.path.join(base_path, "networking", "hamlet2.json")

#     speaker_id: int = 2
#     speakers: Dict[str, str] = {}
#     hamlet: Dict = None

#     with open(in_path, "r") as in_file:
#         hamlet = json.loads(in_file.read())
#         messages = hamlet.get("hamlet", None)
#         if messages is None or len(messages) == 0:
#             print("Found no messages")

#         for i, message in enumerate(hamlet["hamlet"]):
#             username = message["username"]
#             userid = speakers.get(username, None)
#             if userid is None:
#                 speaker_id = speaker_id + 1
#                 speakers[username] = f"{speaker_id}"
#             hamlet["hamlet"][i]["userid"] = speakers[username]

#     with open(out_path, "w") as out_file:
#         hamlet = json.dumps(hamlet)
#         out_file.write(hamlet)


# from textual.app import App, DockView
# from textual import events
# from textual.widgets import Header, Footer, Button, ButtonPressed
# from textual.geometry import Size


# class Director:
#     def __init__(self, app):
#         self.app = app
#         self.scenes = {}

#     def create_scene(self, name):
#         if name in self.scenes:
#             raise ValueError(f"Scene {name} already exists")
#         self.scenes[name] = DockView(name=name)
#         return self.scenes[name]

#     def delete_scene(self, name):
#         del self.scenes[name]

#     async def set_scene(self, scene_name):
#         view = self.scenes[scene_name]
#         resize = events.Resize(self.app, Size(self.app.console.size))
#         await self.pop_view()
#         await view.on_resize(resize)
#         await self.app.push_view(view)

#     async def pop_view(self) -> None:
#         if len(self.app._view_stack) > 1:
#             view = self.app._view_stack.pop()
#             await self.app.remove(view)
#             self.app.refresh()


# class MultiPageApp(App):
#     async def on_load(self, event: events.Load) -> None:
#         await self.bind("q", "quit", "Quit")
#         await self.bind("escape", "pop_view", "Escape")
#         await self.bind("a", "set_scene('Alpha')", "Alpha")
#         await self.bind("b", "set_scene('Beta')", "Beta")

#     async def on_mount(self, event: events.Mount) -> None:
#         def make_button(text: str, style: str) -> Button:
#             return Button(f"| {text} |", style=style, name=text)

#         async def assemble(view, header, footer, names, styles):
#             await view.dock(header, edge="top")
#             await view.dock(footer, edge="bottom")
#             grid = await view.dock_grid()
#             btns = [make_button(n, s) for n, s in zip(names, styles)]

#             grid.add_column("c1", fraction=1, max_size=30)
#             grid.add_column("c2", fraction=1, max_size=30)
#             grid.add_row("r1", fraction=1, max_size=10)
#             grid.add_row("r2", fraction=1, max_size=10)
#             grid.place(*btns)

#         self.director = Director(self)
#         header, footer = Header(), Footer()
#         h_style, a_style, b_style = "red", "blue", "green"

#         await assemble(self.view, header, footer, ["Alpha", "Beta"], [a_style, b_style])

#         view = self.director.create_scene("Alpha")
#         await assemble(view, header, footer, ["Home", "Beta"], [h_style, b_style])

#         view = self.director.create_scene("Beta")
#         await assemble(view, header, footer, ["Home", "Alpha"], [h_style, a_style])

#     async def action_pop_view(self):
#         await self.director.pop_view()

#     async def action_set_scene(self, scene_name):
#         await self.director.set_scene(scene_name)

#     async def handle_button_pressed(self, message: ButtonPressed) -> None:
#         assert isinstance(message.sender, Button)
#         button_name = message.sender.name
#         if button_name == "Home":
#             await self.director.pop_view()
#         else:
#             await self.director.set_scene(button_name)


# MultiPageApp.run(title="Multi Page App", log="textual.log")
