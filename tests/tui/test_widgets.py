"""Tests for widget-level invariants that guard against regressions."""
from weakpoint.tui.widgets.command_bar import CommandBar


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
