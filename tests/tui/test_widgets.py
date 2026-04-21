"""Tests for widget-level invariants that guard against regressions."""
from textual.color import Color

from weakpoint.tui.app import WeakpointTuiApp
from weakpoint.tui.widgets.command_bar import CommandBar
from weakpoint.tui.widgets.slide_canvas import SlideCanvas


def test_command_bar_is_always_compact():
    """CommandBar must render as 1-row borderless Input.

    The surrounding layout gives it ``height: 1``. Without ``compact=True``
    Textual's default border (3 rows) is clipped and the typed text becomes
    invisible — the regression this test exists to prevent.
    """
    bar = CommandBar()
    assert bar.compact is True


def test_command_bar_hidden_by_default():
    """CommandBar must not be visible until ``show()`` is called."""
    bar = CommandBar()
    assert "-visible" not in bar.classes


def test_command_bar_show_hide_toggles_visible_class():
    """``show()`` / ``hide()`` must flip the ``-visible`` CSS class."""
    bar = CommandBar()
    bar.add_class("-visible")
    assert "-visible" in bar.classes
    bar.remove_class("-visible")
    assert "-visible" not in bar.classes


async def test_slide_canvas_has_solid_white_border():
    """SlideCanvas must render a solid white border on all four sides.

    The border frames the 100x30 content area and must stay intact; this
    test guards against accidental CSS regressions.
    """
    app = WeakpointTuiApp()
    async with app.run_test() as pilot:
        canvas = pilot.app.screen.query_one(SlideCanvas)
        white = Color.parse("white")
        for side in ("border_top", "border_right", "border_bottom", "border_left"):
            edge_type, edge_color = getattr(canvas.styles, side)
            assert edge_type == "solid", f"{side} type is {edge_type!r}"
            assert edge_color == white, f"{side} color is {edge_color!r}"
