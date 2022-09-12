from ast import parse
from colorsys import hls_to_rgb, rgb_to_hls
from typing import Union

from rich.style import Style
from rich.color import Color
import rich


def to_rgb(h: float, l: float, s: float):
    c = hls_to_rgb(h / 360.0, l, s)
    return f"rgb({int(c[0]*255)}, {int(c[1]*255)}, {int(c[2]*255)})"


def parse_color(color: Union[Color, str] = None) -> Color | None:
    if color is None:
        return None

    # print(f"parsing {color}")
    return color if isinstance(color, Color) else Color.parse(color)


def to_int_255(val: float):
    return int(val * 255)


def clamp(val: float):
    return max(0, min(val, 1))


def scale_hls(
    hls: tuple[float, float, float],
    h_step: float = 0.0,
    l_step: float = 0.1,
    s_step: float = 0.1,
) -> tuple[float, float, float]:
    return (clamp(hls[0] + h_step), clamp(hls[1] + l_step), clamp(hls[2] + s_step))


def hls_to_color(hls: tuple[float, float, float]) -> Color:
    tmp = hls_to_rgb(hls[0], hls[1], hls[2])
    return parse_color(
        f"rgb({to_int_255(tmp[0])}, {to_int_255(tmp[1])}, {to_int_255(tmp[2])})"
    )


_button_color = to_rgb(0, 1, 0)
_button_bg_color = to_rgb(230, 0.5, 0.5)


class ButtonStyle:
    """A class to contain styles for different button states.

    Available states are:
        normal: The default state of the button
        disabled: Button appearance when the button is disabled
        hover: The button appearance when the mouse is over the button or the button has focus
        active: The button appearance when the mouse is clicked on the button
    """

    normal: Style
    disabled: Style
    hover: Style
    active: Style

    def __init__(
        self,
        foreground: Union[Color, str] = None,
        background: Union[Color, str] = None,
        disabled_foreground: Union[Color, str] = None,
        disabled_background: Union[Color, str] = None,
        hover_foreground: Union[Color, str] = None,
        hover_background: Union[Color, str] = None,
        active_foreground: Union[Color, str] = None,
        active_background: Union[Color, str] = None,
    ):
        """Create a button style

        If only partial arguments are supplied, poor decisions will be
        made about the remaining styles based on foreground and background

        Args:
            foreground (Union[Color, str], optional): color of the normal text of the button. Defaults to None.
            background (Union[Color, str], optional): background of the button in default state. Defaults to None.
            disabled_foreground (Union[Color, str], optional): color of disabled button text. Defaults to None.
            disabled_background (Union[Color, str], optional): background of disabled button. Defaults to None.
            hover_foreground (Union[Color, str], optional): color of hovering button text. Defaults to None.
            hover_background (Union[Color, str], optional): background while hovering over button. Defaults to None.
            active_foreground (Union[Color, str], optional): color of button text while mouse is down. Defaults to None.
            active_background (Union[Color, str], optional): backround of button while mouse is down. Defaults to None.
        """
        bg: Color = parse_color(background)
        fg: Color = parse_color(foreground)
        dbg: Color = parse_color(disabled_background)
        dfg: Color = parse_color(disabled_foreground)
        hbg: Color = parse_color(hover_background)
        hfg: Color = parse_color(hover_foreground)
        abg: Color = parse_color(active_background)
        afg: Color = parse_color(active_foreground)

        if bg is None:
            bg = parse_color(_button_bg_color)
        if fg is None:
            fg = parse_color(_button_color)

        trip = fg.get_truecolor().normalized
        fg_hls = rgb_to_hls(trip[0], trip[1], trip[2])
        trip = bg.get_truecolor().normalized
        bg_hls = rgb_to_hls(trip[0], trip[1], trip[2])

        darken: bool = fg_hls[1] > bg_hls[1]

        if dbg is None:
            hls = scale_hls(
                bg_hls,
                h_step=0,
                l_step=-0.1 if darken else 0.1,
                s_step=-0.2 if darken else 0.2,
            )
            dbg = hls_to_color(hls)

        if dfg is None:
            hls = scale_hls(
                fg_hls,
                h_step=0,
                l_step=-0.3 if darken else 0.3,
                s_step=-0.2 if darken else 0.2,
            )
            dfg = hls_to_color(hls)

        if hbg is None:
            hls = scale_hls(
                bg_hls, h_step=0, l_step=0.1 if darken else -0.1, s_step=0.0
            )
            hbg = hls_to_color(hls)

        if hfg is None:
            hfg = fg

        if abg is None:
            hls = scale_hls(
                bg_hls, h_step=0, l_step=0.1 if darken else -0.1, s_step=0.0
            )
            abg = hls_to_color(hls)

        if afg is None:
            afg = fg

        self.normal = Style(color=fg, bgcolor=bg)
        self.disabled = Style(color=dfg, bgcolor=dbg)
        self.active = Style(color=afg, bgcolor=abg)
        self.hover = Style(color=hfg, bgcolor=hbg)

    def __rich_repr__(self) -> rich.repr.Result:
        yield "Normal:", self.normal
        yield "Disabled", self.disabled
        yield "Active", self.active
        yield "Hover", self.hover

    def __str__(self) -> str:
        return f"""ButtonStyle:
    normal: {self.normal}    
    disabled: {self.disabled}
    hover: {self.hover}
    active: {self.active}"""
