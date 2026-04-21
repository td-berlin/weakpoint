"""Smoke + end-to-end pilot tests for the Textual app."""
import json
from pathlib import Path

from weakpoint.tui.app import WeakpointTuiApp
from weakpoint.tui.models import TextBox
from weakpoint.tui.screens.edit_screen import EditScreen
from weakpoint.tui.widgets.slide_canvas import SlideCanvas
from weakpoint.tui.widgets.status_bar import StatusBar


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


async def test_tab_cycles_selection_forward_and_back():
    """Tab / Shift+Tab must cycle selected_id through the current slide's items.

    Guards against Textual's default focus-cycling swallowing Tab before the
    app-level ``cycle_selection`` action can run.
    """
    app = WeakpointTuiApp()
    async with app.run_test() as pilot:
        slide = app.state.deck.slides[0]
        slide.text_boxes.append(TextBox(id="a", x=0, y=0, w=10, h=2, text="A"))
        slide.text_boxes.append(TextBox(id="b", x=0, y=3, w=10, h=2, text="B"))
        slide.text_boxes.append(TextBox(id="c", x=0, y=6, w=10, h=2, text="C"))

        assert app.state.selected_id is None

        await pilot.press("tab")
        assert app.state.selected_id == "a"

        await pilot.press("tab")
        assert app.state.selected_id == "b"

        await pilot.press("tab")
        assert app.state.selected_id == "c"

        await pilot.press("tab")
        assert app.state.selected_id == "a"

        await pilot.press("shift+tab")
        assert app.state.selected_id == "c"


async def test_status_bar_shows_item_counter_on_cycle():
    """StatusBar must display ``i/n`` for the currently selected item.

    Before any selection: no counter. After Tab: ``1/3``. After another Tab:
    ``2/3``. This is the visual feedback the user asked for.
    """
    app = WeakpointTuiApp()
    async with app.run_test() as pilot:
        slide = app.state.deck.slides[0]
        slide.text_boxes.append(TextBox(id="a", x=0, y=0, w=10, h=2, text="A"))
        slide.text_boxes.append(TextBox(id="b", x=0, y=3, w=10, h=2, text="B"))
        slide.text_boxes.append(TextBox(id="c", x=0, y=6, w=10, h=2, text="C"))
        app._refresh_ui()

        status = pilot.app.screen.query_one(StatusBar)
        assert status.item_total == 3
        assert status.item_index == 0

        await pilot.press("tab")
        assert status.item_index == 1
        assert status.item_total == 3

        await pilot.press("tab")
        assert status.item_index == 2


async def test_bold_toggle_invalidates_canvas():
    """Pressing ``b`` on a selected text box must invalidate the canvas.

    Textual's reactive compares the old and new value on assignment; because
    the app mutates the current ``Slide`` in place and reassigns the same
    object, the reactive equality check suppresses the redraw. ``_refresh_ui``
    must force ``canvas.refresh()`` so the terminal actually repaints.
    """
    app = WeakpointTuiApp()
    async with app.run_test() as pilot:
        slide = app.state.deck.slides[0]
        slide.text_boxes.append(TextBox(id="a", x=0, y=0, w=10, h=3, text="hi"))
        app._refresh_ui()
        await pilot.press("tab")
        canvas = pilot.app.screen.query_one(SlideCanvas)

        refresh_calls = {"n": 0}
        original_refresh = canvas.refresh

        def spy(*args, **kwargs):
            refresh_calls["n"] += 1
            return original_refresh(*args, **kwargs)

        canvas.refresh = spy

        await pilot.press("b")
        await pilot.pause()

        assert slide.text_boxes[0].bold is True
        assert refresh_calls["n"] > 0, "canvas.refresh() must run after bold toggle"


async def test_bold_toggle_applies_bold_style_to_text():
    """After pressing ``b``, the rendered Rich Text must contain a bold span.

    Guards against the bold style silently not reaching the output — the
    visible symptom the user reported.
    """
    app = WeakpointTuiApp()
    async with app.run_test() as pilot:
        slide = app.state.deck.slides[0]
        slide.text_boxes.append(TextBox(id="a", x=0, y=0, w=10, h=3, text="hi"))
        app._refresh_ui()
        await pilot.press("tab")
        await pilot.press("b")
        await pilot.press("escape")
        await pilot.pause()

        canvas = pilot.app.screen.query_one(SlideCanvas)
        text = canvas.render()
        assert any("bold" in str(span.style) for span in text.spans)
