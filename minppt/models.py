"""Data models for the minimal PowerPoint clone."""
from __future__ import annotations

from PyQt6.QtCore import QRectF
from PyQt6.QtWidgets import QGraphicsScene


SLIDE_WIDTH = 960
SLIDE_HEIGHT = 540


class Slide:
    """One slide: owns a QGraphicsScene and the list of text boxes placed on it."""

    def __init__(self) -> None:
        """Create an empty slide with a 960x540 scene."""
        self.scene: QGraphicsScene = QGraphicsScene()
        self.scene.setSceneRect(QRectF(0, 0, SLIDE_WIDTH, SLIDE_HEIGHT))
        self.text_boxes: list = []


class Deck:
    """The presentation: an ordered list of slides with a current selection."""

    def __init__(self) -> None:
        """Create a deck with exactly one empty slide."""
        self.slides: list[Slide] = [Slide()]
        self.current_index: int = 0

    def add_slide(self, at: int | None = None) -> Slide:
        """Insert a new slide and make it current.

        With no argument, insert directly after the current slide. When ``at``
        is given, insert at that index.
        """
        insert_at = self.current_index + 1 if at is None else at
        new_slide = Slide()
        self.slides.insert(insert_at, new_slide)
        self.current_index = insert_at
        return new_slide

    def remove_slide(self, index: int) -> None:
        """Remove the slide at ``index``; no-op if this is the only slide."""
        if len(self.slides) <= 1:
            return
        del self.slides[index]
        if self.current_index > index:
            self.current_index -= 1
        elif self.current_index >= len(self.slides):
            self.current_index = len(self.slides) - 1

    def move_to(self, index: int) -> None:
        """Select the slide at ``index``."""
        if not 0 <= index < len(self.slides):
            raise IndexError(f"slide index {index} out of range")
        self.current_index = index
