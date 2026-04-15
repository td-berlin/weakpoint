"""Tests for the Deck and Slide models."""
from PyQt6.QtCore import QRectF
from PyQt6.QtWidgets import QGraphicsScene

from minppt.models import Slide


def test_slide_has_scene_with_correct_bounds() -> None:
    """A new slide owns a 960x540 scene."""
    slide = Slide()
    assert isinstance(slide.scene, QGraphicsScene)
    assert slide.scene.sceneRect() == QRectF(0, 0, 960, 540)


def test_slide_starts_with_no_text_boxes() -> None:
    """A new slide has an empty text_boxes list."""
    slide = Slide()
    assert slide.text_boxes == []
