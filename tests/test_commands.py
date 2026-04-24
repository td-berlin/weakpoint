"""Tests for the modal command parser and dispatcher."""
from pathlib import Path

import pytest

from weakpoint.commands import (
    AddBox,
    AddImage,
    Align,
    AppState,
    Bullets,
    ColorCmd,
    DispatchResult,
    Numbered,
    Open,
    ParseError,
    Quit,
    Save,
    SaveQuit,
    SetTitle,
    dispatch,
    parse,
)
from weakpoint.models import Deck, Image as ImgModel, Slide, TextBox


def test_parse_box_with_text():
    cmd = parse("box 10 5 30 8 hello world")
    assert cmd == AddBox(x=10, y=5, w=30, h=8, text="hello world")


def test_parse_box_without_text():
    assert parse("box 0 0 5 3") == AddBox(x=0, y=0, w=5, h=3, text="")


def test_parse_box_bad_numbers():
    with pytest.raises(ParseError, match="box"):
        parse("box oops 1 2 3")


def test_parse_box_converts_backslash_n_to_newline():
    """Literal ``\\n`` in the box text must become a real newline.

    Users can't type Enter in the command bar (Enter submits), so the
    escape is the only way to get multi-line text through ``:box``.
    """
    cmd = parse("box 0 0 20 5 line1\\nline2")
    assert isinstance(cmd, AddBox)
    assert cmd.text == "line1\nline2"


def test_parse_image():
    assert parse("image pics/cat.png") == AddImage(path="pics/cat.png")


def test_parse_title():
    assert parse("title My Deck") == SetTitle(title="My Deck")


def test_parse_title_empty_allowed():
    assert parse("title") == SetTitle(title="")


def test_parse_align_valid():
    assert parse("align center") == Align(value="center")


def test_parse_align_invalid():
    with pytest.raises(ParseError, match="align"):
        parse("align sideways")


def test_parse_color():
    assert parse("color red") == ColorCmd(value="red")
    assert parse("color #ff8800") == ColorCmd(value="#ff8800")


def test_parse_bullets_and_numbered():
    assert parse("bullets on") == Bullets(on=True)
    assert parse("bullets off") == Bullets(on=False)
    assert parse("numbered on") == Numbered(on=True)


def test_parse_bullets_bad_arg():
    with pytest.raises(ParseError):
        parse("bullets maybe")


def test_parse_write_no_arg():
    assert parse("w") == Save(path=None)


def test_parse_write_with_arg():
    assert parse("w deck.json") == Save(path="deck.json")


def test_parse_open():
    assert parse("o deck.json") == Open(path="deck.json", force=False)
    assert parse("o! deck.json") == Open(path="deck.json", force=True)


def test_parse_quit():
    assert parse("q") == Quit(force=False)
    assert parse("q!") == Quit(force=True)


def test_parse_write_quit():
    assert parse("wq") == SaveQuit(path=None)
    assert parse("wq deck.json") == SaveQuit(path="deck.json")


def test_parse_unknown_verb():
    with pytest.raises(ParseError, match="unknown"):
        parse("bogus")


def test_parse_empty_string():
    with pytest.raises(ParseError):
        parse("")


# --- dispatch tests ------------------------------------------------------


def _state(deck: Deck | None = None, selected_id: str | None = None) -> AppState:
    return AppState(deck=deck or Deck(), selected_id=selected_id, dirty=False, should_quit=False)


def test_dispatch_add_box_appends_to_current_slide():
    state = _state()
    res = dispatch(parse("box 0 0 5 3 hi"), state)
    assert isinstance(res, DispatchResult)
    slide = state.deck.slides[0]
    assert len(slide.text_boxes) == 1
    box = slide.text_boxes[0]
    assert (box.x, box.y, box.w, box.h, box.text) == (0, 0, 5, 3, "hi")
    assert state.selected_id == box.id
    assert state.dirty is True
    assert "box added" in res.message


def test_dispatch_add_box_out_of_bounds_is_rejected():
    state = _state()
    res = dispatch(parse("box 95 0 20 3"), state)
    assert state.deck.slides[0].text_boxes == []
    assert state.dirty is False
    assert "bounds" in res.message.lower()


def test_dispatch_add_image_places_default_sized_box_at_center():
    state = _state()
    dispatch(parse("image pics/cat.png"), state)
    images = state.deck.slides[0].images
    assert len(images) == 1
    img = images[0]
    # Default 40x12 centered in 100x30 -> (30, 9).
    assert (img.x, img.y, img.w, img.h) == (30, 9, 40, 12)
    assert img.path == "pics/cat.png"
    assert state.selected_id == img.id


def test_dispatch_set_title():
    state = _state()
    dispatch(parse("title My Deck"), state)
    assert state.deck.slides[0].title == "My Deck"
    assert state.dirty is True


def test_dispatch_align_requires_selected_textbox():
    state = _state()
    res = dispatch(parse("align center"), state)
    assert "select" in res.message.lower()
    assert state.dirty is False


def test_dispatch_align_mutates_selected_textbox():
    deck = Deck()
    box = TextBox(id="B", x=0, y=0, w=5, h=3)
    deck.slides[0].text_boxes.append(box)
    state = _state(deck, selected_id="B")
    dispatch(parse("align right"), state)
    assert box.align == "right"


def test_dispatch_color():
    deck = Deck()
    box = TextBox(id="B", x=0, y=0, w=5, h=3)
    deck.slides[0].text_boxes.append(box)
    state = _state(deck, selected_id="B")
    dispatch(parse("color #ff8800"), state)
    assert box.color == "#ff8800"


def test_dispatch_bullets_and_numbered():
    deck = Deck()
    box = TextBox(id="B", x=0, y=0, w=5, h=3)
    deck.slides[0].text_boxes.append(box)
    state = _state(deck, selected_id="B")
    dispatch(parse("bullets on"), state)
    assert box.bullets is True
    dispatch(parse("numbered on"), state)
    assert box.numbered is True


def test_dispatch_save_requires_path_when_deck_untitled(tmp_path):
    state = _state()
    res = dispatch(parse("w"), state)
    assert "path" in res.message.lower()
    assert not any(tmp_path.iterdir())


def test_dispatch_save_with_path_writes_file(tmp_path):
    state = _state()
    target = tmp_path / "d.wpt.json"
    dispatch(parse(f"w {target}"), state)
    assert target.exists()
    assert state.dirty is False
    assert state.deck.path == str(target)


def test_dispatch_save_reuses_deck_path(tmp_path):
    state = _state()
    target = tmp_path / "d.wpt.json"
    dispatch(parse(f"w {target}"), state)
    # Make dirty then save with no arg; should write to same file.
    dispatch(parse("title Hi"), state)
    assert state.dirty is True
    dispatch(parse("w"), state)
    assert state.dirty is False


def test_dispatch_open_loads_file(tmp_path):
    # Save a deck, then load it from a fresh state.
    state = _state()
    dispatch(parse("title Saved"), state)
    target = tmp_path / "d.wpt.json"
    dispatch(parse(f"w {target}"), state)

    fresh = _state()
    dispatch(parse(f"o {target}"), fresh)
    assert fresh.deck.slides[0].title == "Saved"
    assert fresh.deck.path == str(target)


def test_dispatch_open_refused_when_dirty(tmp_path):
    state = _state()
    dispatch(parse("title X"), state)  # dirty=True
    target = tmp_path / "d.wpt.json"
    Path(target).write_text('{"version":1,"current_index":0,"slides":[]}')
    res = dispatch(parse(f"o {target}"), state)
    assert "unsaved" in res.message.lower()
    assert state.deck.slides[0].title == "X"  # unchanged


def test_dispatch_open_force_discards_changes(tmp_path):
    state = _state()
    dispatch(parse("title X"), state)
    target = tmp_path / "d.wpt.json"
    Path(target).write_text(
        '{"version":1,"current_index":0,"slides":[{"title":"From File","text_boxes":[],"images":[]}]}'
    )
    dispatch(parse(f"o! {target}"), state)
    assert state.deck.slides[0].title == "From File"
    assert state.dirty is False


def test_dispatch_quit_refused_when_dirty():
    state = _state()
    dispatch(parse("title X"), state)
    res = dispatch(parse("q"), state)
    assert state.should_quit is False
    assert "unsaved" in res.message.lower()


def test_dispatch_quit_force():
    state = _state()
    dispatch(parse("title X"), state)
    dispatch(parse("q!"), state)
    assert state.should_quit is True


def test_dispatch_save_quit(tmp_path):
    state = _state()
    target = tmp_path / "d.wpt.json"
    dispatch(parse(f"wq {target}"), state)
    assert state.should_quit is True
    assert target.exists()
