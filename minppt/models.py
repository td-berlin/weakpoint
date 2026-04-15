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
