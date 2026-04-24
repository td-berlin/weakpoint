"""JSON save/load for decks. File format version 1."""
from __future__ import annotations

import json
from dataclasses import asdict

from weakpoint.models import Deck, Image, Slide, TextBox


VERSION = 1


def save_deck(deck: Deck, path: str) -> None:
    """Serialize the deck to JSON and write it to ``path``.

    Sets ``deck.path`` on success so that subsequent ``:w`` calls without
    an argument target the same file.
    """
    payload = {
        "version": VERSION,
        "current_index": deck.current_index,
        "slides": [_slide_to_dict(s) for s in deck.slides],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    deck.path = path


def load_deck(path: str) -> Deck:
    """Read a deck JSON file at ``path`` and return a Deck.

    Raises FileNotFoundError if the file does not exist, ValueError for
    malformed JSON or unsupported version.
    """
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"bad deck file: {exc}") from exc

    version = data.get("version")
    if version != VERSION:
        raise ValueError(f"unsupported deck version: {version!r}")

    deck = Deck(
        slides=[_slide_from_dict(s) for s in data.get("slides", [])],
        current_index=int(data.get("current_index", 0)),
        path=path,
    )
    if not deck.slides:
        deck.slides = [Slide()]
    if not 0 <= deck.current_index < len(deck.slides):
        deck.current_index = 0
    return deck


def _slide_to_dict(slide: Slide) -> dict:
    """Serialize a Slide to a JSON-ready dict."""
    return {
        "title": slide.title,
        "text_boxes": [asdict(b) for b in slide.text_boxes],
        "images": [asdict(i) for i in slide.images],
    }


def _slide_from_dict(data: dict) -> Slide:
    """Reconstruct a Slide from a JSON dict (raises TypeError on schema drift)."""
    return Slide(
        title=data.get("title", ""),
        text_boxes=[TextBox(**b) for b in data.get("text_boxes", [])],
        images=[Image(**i) for i in data.get("images", [])],
    )
