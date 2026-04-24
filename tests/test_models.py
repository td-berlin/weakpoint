"""Tests for the pure data model in weakpoint.models."""
from weakpoint.models import (
    SLIDE_COLS,
    SLIDE_ROWS,
    Deck,
    Image,
    Slide,
    TextBox,
)


def test_slide_dimensions_are_100_by_30():
    assert SLIDE_COLS == 100
    assert SLIDE_ROWS == 30


def test_new_deck_has_one_empty_slide_selected():
    deck = Deck()
    assert len(deck.slides) == 1
    assert deck.current_index == 0
    assert deck.path is None


def test_new_slide_is_empty():
    slide = Slide()
    assert slide.title == ""
    assert slide.text_boxes == []
    assert slide.images == []


def test_text_box_defaults():
    box = TextBox(id="x", x=0, y=0, w=10, h=3)
    assert box.text == ""
    assert box.bold is False
    assert box.color == "default"
    assert box.align == "left"
    assert box.bullets is False
    assert box.numbered is False


def test_image_requires_path():
    img = Image(id="i", x=0, y=0, w=10, h=5, path="pic.png")
    assert img.path == "pic.png"


def test_slide_items_orders_images_before_text_boxes():
    slide = Slide()
    img = Image(id="i", x=0, y=0, w=5, h=5, path="p.png")
    box = TextBox(id="b", x=0, y=0, w=5, h=5)
    slide.images.append(img)
    slide.text_boxes.append(box)
    items = slide.items()
    assert items == [img, box]


def test_distinct_default_deck_slides_are_independent():
    d1 = Deck()
    d2 = Deck()
    d1.slides[0].text_boxes.append(TextBox(id="x", x=0, y=0, w=1, h=1))
    assert d2.slides[0].text_boxes == []
