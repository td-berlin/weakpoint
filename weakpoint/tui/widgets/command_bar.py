"""Textual Input used as the `:`-prompt in COMMAND mode."""
from __future__ import annotations

from textual.widgets import Input


class CommandBar(Input):
    """Single-line input; hidden by default, shown when entering COMMAND mode."""

    DEFAULT_CSS = """
    CommandBar {
        display: none;
        height: 1;
    }
    CommandBar.-visible {
        display: block;
    }
    """

    def show(self, prefix: str = ":") -> None:
        """Show the bar, clear content, optionally leading with a prefix prompt."""
        self.add_class("-visible")
        self.value = ""
        self.placeholder = prefix
        self.focus()

    def hide(self) -> None:
        """Hide the bar and clear content."""
        self.remove_class("-visible")
        self.value = ""
