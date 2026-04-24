"""Pure data model for the weakpoint terminal UI."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


SLIDE_COLS = 100
SLIDE_ROWS = 30

Color = str
Align = Literal["left", "center", "right"]


@dataclass
class TextBox:
    """A rectangular text region on a slide."""

    id: str
    x: int
    y: int
    w: int
    h: int
    text: str = ""
    bold: bool = False
    color: Color = "default"
    align: Align = "left"
    bullets: bool = False
    numbered: bool = False


@dataclass
class Image:
    """An image region on a slide; rendered as colored ASCII at draw time."""

    id: str
    x: int
    y: int
    w: int
    h: int
    path: str


@dataclass
class Slide:
    """One slide: optional title plus text boxes and images."""

    title: str = ""
    text_boxes: list[TextBox] = field(default_factory=list)
    images: list[Image] = field(default_factory=list)

    def items(self) -> list[TextBox | Image]:
        """Return items in draw order: images first (behind), text boxes second (in front)."""
        return [*self.images, *self.text_boxes]


@dataclass
class Deck:
    """The presentation: an ordered list of slides plus the current selection."""

    slides: list[Slide] = field(default_factory=lambda: [Slide()])
    current_index: int = 0
    path: str | None = None
