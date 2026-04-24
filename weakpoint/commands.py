"""Modal commands: parser + dispatcher.

Parsing is pure and has no dependencies on the app. Dispatching takes an
AppState value object, mutates it, and returns a DispatchResult.
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Literal, Union

from weakpoint.models import (
    SLIDE_COLS,
    SLIDE_ROWS,
    Deck,
    Image as ImageModel,
    Slide,
    TextBox,
)
from weakpoint.persistence import load_deck, save_deck


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
        return Save(path=rest or None)
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
    """Parse 'X Y W H [TEXT]' into AddBox; raise ParseError on bad numbers.

    Literal ``\\n`` sequences in the text are converted to real newlines so
    users can create multi-line boxes from the single-line command bar.
    """
    parts = rest.split(" ", 4)
    if len(parts) < 4:
        raise ParseError("box requires: box X Y W H [TEXT]")
    try:
        x, y, w, h = (int(parts[i]) for i in range(4))
    except ValueError as exc:
        raise ParseError(f"box: bad number ({exc})") from exc
    text = unescape_newlines(parts[4]) if len(parts) == 5 else ""
    return AddBox(x=x, y=y, w=w, h=h, text=text)


def unescape_newlines(s: str) -> str:
    """Convert literal ``\\n`` sequences in user-typed text to real newlines."""
    return s.replace("\\n", "\n")


def _parse_on_off(verb: str, arg: str) -> bool:
    """Return True for 'on', False for 'off'; raise ParseError otherwise."""
    if arg == "on":
        return True
    if arg == "off":
        return False
    raise ParseError(f"{verb}: expected on|off, got {arg!r}")


# --- dispatcher ---------------------------------------------------------

DEFAULT_IMAGE_W = 40
DEFAULT_IMAGE_H = 12


@dataclass
class AppState:
    """Mutable state the dispatcher operates on."""

    deck: Deck
    selected_id: str | None = None
    dirty: bool = False
    should_quit: bool = False


@dataclass
class DispatchResult:
    """Status message returned for display in the status bar."""

    message: str
    error: bool = False


def dispatch(cmd: Command, state: AppState) -> DispatchResult:
    """Apply ``cmd`` to ``state`` and return a status message."""
    try:
        return _dispatch(cmd, state)
    except Exception as exc:  # noqa: BLE001
        return DispatchResult(message=str(exc), error=True)


def _dispatch(cmd: Command, state: AppState) -> DispatchResult:
    """Apply ``cmd`` to ``state`` without exception wrapping; see ``dispatch``."""
    if isinstance(cmd, AddBox):
        return _do_add_box(cmd, state)
    if isinstance(cmd, AddImage):
        return _do_add_image(cmd, state)
    if isinstance(cmd, SetTitle):
        _current(state).title = cmd.title
        state.dirty = True
        return DispatchResult(message="title set")
    if isinstance(cmd, Align):
        return _mutate_selected_box(state, lambda b: setattr(b, "align", cmd.value), "alignment set")
    if isinstance(cmd, ColorCmd):
        return _mutate_selected_box(state, lambda b: setattr(b, "color", cmd.value), "color set")
    if isinstance(cmd, Bullets):
        return _mutate_selected_box(state, lambda b: setattr(b, "bullets", cmd.on), "bullets set")
    if isinstance(cmd, Numbered):
        return _mutate_selected_box(state, lambda b: setattr(b, "numbered", cmd.on), "numbered set")
    if isinstance(cmd, Save):
        return _do_save(cmd.path, state)
    if isinstance(cmd, SaveQuit):
        res = _do_save(cmd.path, state)
        if not res.error:
            state.should_quit = True
        return res
    if isinstance(cmd, Open):
        return _do_open(cmd, state)
    if isinstance(cmd, Quit):
        if state.dirty and not cmd.force:
            return DispatchResult(message="unsaved changes — use :q! or :wq", error=True)
        state.should_quit = True
        return DispatchResult(message="bye")
    raise ValueError(f"unhandled command: {cmd!r}")


def _current(state: AppState) -> Slide:
    """Return the slide at ``state.deck.current_index``."""
    return state.deck.slides[state.deck.current_index]


def _new_id() -> str:
    """Return a fresh uuid4 hex string."""
    return uuid.uuid4().hex


def _in_bounds(x: int, y: int, w: int, h: int) -> bool:
    """True iff a w×h rectangle at (x, y) fits inside the slide canvas."""
    return w > 0 and h > 0 and x >= 0 and y >= 0 and x + w <= SLIDE_COLS and y + h <= SLIDE_ROWS


def _do_add_box(cmd: AddBox, state: AppState) -> DispatchResult:
    """Insert a new TextBox if it fits; reject otherwise."""
    if not _in_bounds(cmd.x, cmd.y, cmd.w, cmd.h):
        return DispatchResult(message="out of bounds", error=True)
    box = TextBox(id=_new_id(), x=cmd.x, y=cmd.y, w=cmd.w, h=cmd.h, text=cmd.text)
    _current(state).text_boxes.append(box)
    state.selected_id = box.id
    state.dirty = True
    return DispatchResult(message="box added")


def _do_add_image(cmd: AddImage, state: AppState) -> DispatchResult:
    """Insert an image with default 40x12 size, centered on the slide."""
    x = (SLIDE_COLS - DEFAULT_IMAGE_W) // 2
    y = (SLIDE_ROWS - DEFAULT_IMAGE_H) // 2
    img = ImageModel(id=_new_id(), x=x, y=y, w=DEFAULT_IMAGE_W, h=DEFAULT_IMAGE_H, path=cmd.path)
    _current(state).images.append(img)
    state.selected_id = img.id
    state.dirty = True
    return DispatchResult(message=f"image added: {cmd.path}")


def _mutate_selected_box(state: AppState, fn, msg: str) -> DispatchResult:
    """Apply ``fn`` to the selected TextBox; error if nothing selected."""
    box = _selected_box(state)
    if box is None:
        return DispatchResult(message="select a text box first", error=True)
    fn(box)
    state.dirty = True
    return DispatchResult(message=msg)


def _selected_box(state: AppState) -> TextBox | None:
    """Return the currently selected TextBox, or None."""
    if state.selected_id is None:
        return None
    for b in _current(state).text_boxes:
        if b.id == state.selected_id:
            return b
    return None


def _do_save(path: str | None, state: AppState) -> DispatchResult:
    """Write the deck to ``path`` (or deck.path); error if both are None."""
    target = path or state.deck.path
    if target is None:
        return DispatchResult(message="save: path required (deck is untitled)", error=True)
    save_deck(state.deck, target)
    state.dirty = False
    return DispatchResult(message=f"saved {os.path.basename(target)}")


def _do_open(cmd: Open, state: AppState) -> DispatchResult:
    """Replace state.deck with the deck loaded from ``cmd.path``."""
    if state.dirty and not cmd.force:
        return DispatchResult(message="unsaved changes — use :o! to discard", error=True)
    loaded = load_deck(cmd.path)
    state.deck = loaded
    state.selected_id = None
    state.dirty = False
    return DispatchResult(message=f"opened {os.path.basename(cmd.path)}")
