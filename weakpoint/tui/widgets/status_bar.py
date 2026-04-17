"""Bottom status bar: mode, slide counter, deck name, last message."""
from __future__ import annotations

from textual.reactive import reactive
from textual.widgets import Static


class StatusBar(Static):
    """One-line status bar. Updated via reactive attributes."""

    mode: reactive[str] = reactive("NORMAL")
    slide_i: reactive[int] = reactive(1)
    slide_n: reactive[int] = reactive(1)
    path: reactive[str | None] = reactive(None)
    dirty: reactive[bool] = reactive(False)
    message: reactive[str] = reactive("")
    error: reactive[bool] = reactive(False)

    def watch_mode(self) -> None:
        """Refresh display when mode changes."""
        self._refresh()

    def watch_slide_i(self) -> None:
        """Refresh display when slide index changes."""
        self._refresh()

    def watch_slide_n(self) -> None:
        """Refresh display when total slide count changes."""
        self._refresh()

    def watch_path(self) -> None:
        """Refresh display when deck path changes."""
        self._refresh()

    def watch_dirty(self) -> None:
        """Refresh display when dirty flag changes."""
        self._refresh()

    def watch_message(self) -> None:
        """Refresh display when message changes."""
        self._refresh()

    def watch_error(self) -> None:
        """Refresh display when error flag changes."""
        self._refresh()

    def _refresh(self) -> None:
        """Update the status bar display."""
        name = self.path if self.path else "untitled"
        marker = "*" if self.dirty else ""
        msg = f"  last: {self.message}" if self.message else ""
        style = "[red]" if self.error and self.message else ""
        end = "[/]" if style else ""
        self.update(
            f"{self.mode}  slide {self.slide_i}/{self.slide_n}  {name}{marker}{style}{msg}{end}"
        )
