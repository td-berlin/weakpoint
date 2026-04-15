"""Tests for the Deck and Slide models."""
from PyQt6.QtCore import QRectF
from PyQt6.QtWidgets import QGraphicsScene

from minppt.models import Deck, Slide


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
