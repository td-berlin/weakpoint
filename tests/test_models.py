"""Tests for the Deck and Slide models."""
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsScene

from weakpoint.models import Deck, Slide
from weakpoint.textbox import TextBoxItem


def test_slide_has_scene_with_correct_bounds() -> None:
    """A new slide owns a 960x540 scene."""
    slide = Slide()
    assert isinstance(slide.scene, QGraphicsScene)
    assert slide.scene.sceneRect() == QRectF(0, 0, 960, 540)


def test_slide_starts_with_no_text_boxes() -> None:
    """A new slide has an empty text_boxes list."""
    slide = Slide()
    assert slide.text_boxes == []


def test_deck_starts_with_one_slide() -> None:
    """A brand-new deck has exactly one slide, index 0."""
    deck = Deck()
    assert len(deck.slides) == 1
    assert deck.current_index == 0


def test_deck_add_slide_inserts_after_current_by_default() -> None:
    """add_slide() with no argument inserts directly after current_index."""
    deck = Deck()
    new_slide = deck.add_slide()
    assert len(deck.slides) == 2
    assert deck.slides[1] is new_slide
    assert deck.current_index == 1


def test_deck_add_slide_at_zero_inserts_at_start_and_updates_index() -> None:
    """add_slide(at=0) inserts at index 0; current_index moves to the new slide."""
    deck = Deck()
    new_slide = deck.add_slide(at=0)
    assert deck.slides[0] is new_slide
    assert deck.current_index == 0


def test_deck_remove_slide_adjusts_current_index() -> None:
    """Removing the current slide selects the slide that took its place."""
    deck = Deck()
    deck.add_slide()  # now 2 slides, current_index = 1
    deck.remove_slide(1)
    assert len(deck.slides) == 1
    assert deck.current_index == 0


def test_deck_remove_last_slide_is_noop() -> None:
    """remove_slide refuses to delete the only remaining slide."""
    deck = Deck()
    only = deck.slides[0]
    deck.remove_slide(0)
    assert deck.slides == [only]
    assert deck.current_index == 0


def test_deck_remove_earlier_slide_decrements_current_index() -> None:
    """Removing a slide before current_index shifts current_index down by one."""
    deck = Deck()
    deck.add_slide()  # current_index = 1
    deck.remove_slide(0)
    assert deck.current_index == 0


def test_deck_move_to_sets_current_index() -> None:
    """move_to updates current_index."""
    deck = Deck()
    deck.add_slide()
    deck.add_slide()  # 3 slides
    deck.move_to(0)
    assert deck.current_index == 0


def test_textbox_defaults() -> None:
    """A fresh TextBoxItem has empty text, white fill, black text color."""
    item = TextBoxItem(QRectF(0, 0, 200, 80))
    assert item.text == ""
    assert item.fill_color == QColor(Qt.GlobalColor.white)
    assert item.text_color == QColor(Qt.GlobalColor.black)


def test_textbox_setters_persist_values() -> None:
    """Setting text/fill_color/text_color stores the assigned value."""
    item = TextBoxItem(QRectF(0, 0, 200, 80))
    item.text = "Hello"
    item.fill_color = QColor("red")
    item.text_color = QColor("blue")
    assert item.text == "Hello"
    assert item.fill_color == QColor("red")
    assert item.text_color == QColor("blue")


def test_textbox_uses_provided_rect() -> None:
    """The item's rect matches the constructor argument."""
    item = TextBoxItem(QRectF(10, 20, 300, 100))
    assert item.rect() == QRectF(10, 20, 300, 100)


def test_slide_add_text_box_appends_to_scene_and_list() -> None:
    """add_text_box creates a TextBoxItem, adds it to the scene and tracking list."""
    slide = Slide()
    item = slide.add_text_box(QRectF(10, 20, 200, 80))
    assert isinstance(item, TextBoxItem)
    assert item in slide.text_boxes
    assert item in slide.scene.items()


def test_slide_remove_text_box_removes_from_scene_and_list() -> None:
    """remove_text_box removes the item from both the scene and tracking list."""
    slide = Slide()
    item = slide.add_text_box(QRectF(0, 0, 100, 50))
    slide.remove_text_box(item)
    assert item not in slide.text_boxes
    assert item not in slide.scene.items()


def test_textbox_default_font_size_and_bold() -> None:
    """A fresh TextBoxItem has default font size 18 and is not bold."""
    item = TextBoxItem(QRectF(0, 0, 200, 80))
    assert item.font_size == 18
    assert item.bold is False


def test_textbox_font_setters_persist_values() -> None:
    """Setting font_size and bold stores the assigned values."""
    item = TextBoxItem(QRectF(0, 0, 200, 80))
    item.font_size = 32
    item.bold = True
    assert item.font_size == 32
    assert item.bold is True


def test_textbox_clamps_position_to_scene_rect() -> None:
    """A text box cannot be moved outside the 960x540 scene rect."""
    slide = Slide()
    item = slide.add_text_box(QRectF(0, 0, 200, 80))
    # Try to push the item far off-screen; itemChange should clamp it back.
    item.setPos(5000, 5000)
    pos = item.scenePos()
    # The rect's right/bottom must not exceed the scene rect.
    assert pos.x() + item.rect().width() <= 960 + 1e-6
    assert pos.y() + item.rect().height() <= 540 + 1e-6
