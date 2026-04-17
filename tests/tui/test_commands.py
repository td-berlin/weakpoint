"""Tests for the modal command parser and dispatcher."""
import pytest

from weakpoint.tui.commands import (
    AddBox,
    AddImage,
    Align,
    Bullets,
    ColorCmd,
    Numbered,
    Open,
    ParseError,
    Quit,
    Save,
    SaveQuit,
    SetTitle,
    parse,
)


def test_parse_box_with_text():
    cmd = parse("box 10 5 30 8 hello world")
    assert cmd == AddBox(x=10, y=5, w=30, h=8, text="hello world")


def test_parse_box_without_text():
    assert parse("box 0 0 5 3") == AddBox(x=0, y=0, w=5, h=3, text="")


def test_parse_box_bad_numbers():
    with pytest.raises(ParseError, match="box"):
        parse("box oops 1 2 3")


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
    assert parse("w") == Save(path=None, force_quit=False)


def test_parse_write_with_arg():
    assert parse("w deck.json") == Save(path="deck.json", force_quit=False)


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
