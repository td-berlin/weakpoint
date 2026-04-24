"""Textual Input used as the `:`-prompt in COMMAND mode."""
from __future__ import annotations

from typing import Any

from textual.widgets import Input


class CommandBar(Input):
    """Single-line input; hidden by default, shown when entering COMMAND mode.

    Uses Textual's ``compact=True`` so the Input renders as a borderless 1-row
    field; the default Input is 3 rows with a border, which would be clipped by
    our fixed ``height: 1`` and hide the user's typed text.
    """

    DEFAULT_CSS = """
    CommandBar {
        display: none;
    }
    CommandBar.-visible {
        display: block;
    }
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Force ``compact=True`` so the Input is a 1-row borderless field."""
        kwargs["compact"] = True
        super().__init__(*args, **kwargs)

    def on_mount(self) -> None:
        """Ensure the bar starts unfocusable while hidden."""
        self.can_focus = False

    def show(self, prefix: str = ":") -> None:
        """Show the bar, clear content, optionally leading with a prefix prompt."""
        self.can_focus = True
        self.add_class("-visible")
        self.value = ""
        self.placeholder = prefix
        self.focus()

    def hide(self) -> None:
        """Hide the bar, clear content, and return focus to the screen."""
        self.can_focus = False
        self.remove_class("-visible")
        self.value = ""
        self.blur()
