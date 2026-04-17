"""Tests for deck JSON persistence."""
import json
from pathlib import Path

import pytest

from weakpoint.tui.models import Deck, Image, Slide, TextBox
from weakpoint.tui.persistence import load_deck, save_deck


def _sample_deck() -> Deck:
    slide = Slide(
        title="Intro",
        text_boxes=[
            TextBox(
                id="box1",
                x=10,
                y=5,
                w=30,
                h=4,
                text="hello",
                bold=True,
                color="red",
                align="center",
                bullets=False,
                numbered=False,
            )
        ],
        images=[Image(id="img1", x=40, y=10, w=40, h=12, path="pics/cat.png")],
    )
    return Deck(slides=[slide, Slide(title="Two")], current_index=1)


def test_round_trip(tmp_path: Path):
    deck = _sample_deck()
    target = tmp_path / "deck.wpt.json"
    save_deck(deck, str(target))

    loaded = load_deck(str(target))

    assert loaded.current_index == deck.current_index
    assert [s.title for s in loaded.slides] == ["Intro", "Two"]
    box = loaded.slides[0].text_boxes[0]
    assert box.text == "hello"
    assert box.bold is True
    assert box.color == "red"
    assert box.align == "center"
    img = loaded.slides[0].images[0]
    assert img.path == "pics/cat.png"
    assert loaded.path == str(target)


def test_file_on_disk_has_version_1(tmp_path: Path):
    target = tmp_path / "d.wpt.json"
    save_deck(_sample_deck(), str(target))
    data = json.loads(target.read_text())
    assert data["version"] == 1


def test_unknown_version_rejected(tmp_path: Path):
    target = tmp_path / "d.wpt.json"
    target.write_text(json.dumps({"version": 99, "current_index": 0, "slides": []}))
    with pytest.raises(ValueError, match="version"):
        load_deck(str(target))


def test_malformed_json_rejected(tmp_path: Path):
    target = tmp_path / "d.wpt.json"
    target.write_text("{not json")
    with pytest.raises(ValueError, match="bad deck file"):
        load_deck(str(target))


def test_missing_file_raises_file_not_found(tmp_path: Path):
    target = tmp_path / "nope.wpt.json"
    with pytest.raises(FileNotFoundError):
        load_deck(str(target))
