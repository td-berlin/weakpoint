"""Modal commands: parser + dispatcher.

Parsing is pure and has no dependencies on the app. Dispatching takes an
AppState value object, mutates it, and returns a DispatchResult.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union


class ParseError(ValueError):
    """Raised when a user-entered command string cannot be parsed."""


@dataclass(frozen=True)
class AddBox:
    x: int
    y: int
    w: int
    h: int
    text: str = ""


@dataclass(frozen=True)
class AddImage:
    path: str


@dataclass(frozen=True)
class SetTitle:
    title: str


@dataclass(frozen=True)
class Align:
    value: Literal["left", "center", "right"]


@dataclass(frozen=True)
class ColorCmd:
    value: str


@dataclass(frozen=True)
class Bullets:
    on: bool


@dataclass(frozen=True)
class Numbered:
    on: bool


@dataclass(frozen=True)
class Save:
    path: str | None
    force_quit: bool


@dataclass(frozen=True)
class SaveQuit:
    path: str | None


@dataclass(frozen=True)
class Open:
    path: str
    force: bool


@dataclass(frozen=True)
class Quit:
    force: bool


Command = Union[
    AddBox,
    AddImage,
    SetTitle,
    Align,
    ColorCmd,
    Bullets,
    Numbered,
    Save,
    SaveQuit,
    Open,
    Quit,
]


def parse(line: str) -> Command:
    """Parse a command string (without the leading ':') into a Command."""
    stripped = line.strip()
    if not stripped:
        raise ParseError("empty command")
    head, _, rest = stripped.partition(" ")
    rest = rest.strip()

    if head == "box":
        return _parse_box(rest)
    if head == "image":
        if not rest:
            raise ParseError("image requires a path")
        return AddImage(path=rest)
    if head == "title":
        return SetTitle(title=rest)
    if head == "align":
        if rest not in ("left", "center", "right"):
            raise ParseError(f"align: expected left|center|right, got {rest!r}")
        return Align(value=rest)  # type: ignore[arg-type]
    if head == "color":
        if not rest:
            raise ParseError("color requires a value")
        return ColorCmd(value=rest)
    if head == "bullets":
        return Bullets(on=_parse_on_off("bullets", rest))
    if head == "numbered":
        return Numbered(on=_parse_on_off("numbered", rest))
    if head == "w":
        return Save(path=rest or None, force_quit=False)
    if head == "wq":
        return SaveQuit(path=rest or None)
    if head == "o":
        if not rest:
            raise ParseError("o requires a path")
        return Open(path=rest, force=False)
    if head == "o!":
        if not rest:
            raise ParseError("o! requires a path")
        return Open(path=rest, force=True)
    if head == "q":
        return Quit(force=False)
    if head == "q!":
        return Quit(force=True)
    raise ParseError(f"unknown command: {head!r}")


def _parse_box(rest: str) -> AddBox:
    parts = rest.split(" ", 4)
    if len(parts) < 4:
        raise ParseError("box requires: box X Y W H [TEXT]")
    try:
        x, y, w, h = (int(parts[i]) for i in range(4))
    except ValueError as exc:
        raise ParseError(f"box: bad number ({exc})") from exc
    text = parts[4] if len(parts) == 5 else ""
    return AddBox(x=x, y=y, w=w, h=h, text=text)


def _parse_on_off(verb: str, arg: str) -> bool:
    if arg == "on":
        return True
    if arg == "off":
        return False
    raise ParseError(f"{verb}: expected on|off, got {arg!r}")
