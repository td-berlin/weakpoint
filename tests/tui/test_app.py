"""Smoke + end-to-end pilot tests for the Textual app."""
import json
from pathlib import Path

from weakpoint.tui.app import WeakpointTuiApp
from weakpoint.tui.screens.edit_screen import EditScreen


def _typing_keys(s: str) -> list[str]:
    """Convert a string to a list of Textual key names.

    Maps special characters to their Textual key names so that
    ``pilot.press(*_typing_keys(s))`` works for arbitrary text input.
    """
    mapping = {
        " ": "space",
        ".": "full_stop",
        "!": "exclamation_mark",
    }
    return [mapping.get(ch, ch) for ch in s]


async def test_app_boots_with_edit_screen():
    """App should launch and show EditScreen as the active screen."""
    app = WeakpointTuiApp()
    async with app.run_test() as pilot:
        assert isinstance(pilot.app.screen, EditScreen)


async def test_add_slide_then_add_box_then_save(tmp_path: Path):
    """Full round-trip: add slide, add box via command bar, save to file."""
    app = WeakpointTuiApp()
    target = tmp_path / "deck.wpt.json"
    async with app.run_test() as pilot:
        # Append a new slide (so deck has 2).
        await pilot.press("a")
        assert len(app.state.deck.slides) == 2

        # Open command bar and add a box on current slide.
        await pilot.press("colon")
        await pilot.press(*_typing_keys("box 0 0 20 3 hello"))
        await pilot.press("enter")
        current = app.state.deck.slides[app.state.deck.current_index]
        assert len(current.text_boxes) == 1
        assert current.text_boxes[0].text == "hello"

        # Save to tmp path.
        await pilot.press("colon")
        await pilot.press(*_typing_keys(f"w {target}"))
        await pilot.press("enter")

    assert target.exists()
    data = json.loads(target.read_text())
    assert data["version"] == 1
    assert len(data["slides"]) == 2
    assert any(b["text"] == "hello" for s in data["slides"] for b in s["text_boxes"])
