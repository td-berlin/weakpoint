"""Fullscreen slide display with arrow-key navigation."""
from __future__ import annotations

import os

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen

from weakpoint.widgets.slide_canvas import SlideCanvas


class PresentScreen(Screen):
    """Show the current slide full-window; arrows to advance; q/Esc to exit."""

    BINDINGS = [
        Binding("right", "next", "next"),
        Binding("space", "next", "next"),
        Binding("left", "prev", "prev"),
        Binding("backspace", "prev", "prev"),
        Binding("q", "exit", "exit"),
        Binding("escape", "exit", "exit"),
    ]

    def compose(self) -> ComposeResult:
        """Yield the single full-window canvas."""
        yield SlideCanvas(id="canvas")

    def on_mount(self) -> None:
        """Render the current slide on first mount."""
        self._refresh_canvas()

    def action_next(self) -> None:
        """Advance to the next slide if there is one."""
        deck = self.app.state.deck  # type: ignore[attr-defined]
        if deck.current_index + 1 < len(deck.slides):
            deck.current_index += 1
            self._refresh_canvas()

    def action_prev(self) -> None:
        """Go to the previous slide if there is one."""
        deck = self.app.state.deck  # type: ignore[attr-defined]
        if deck.current_index > 0:
            deck.current_index -= 1
            self._refresh_canvas()

    def action_exit(self) -> None:
        """Pop back to the EditScreen."""
        self.app.pop_screen()

    def _refresh_canvas(self) -> None:
        """Push current deck state into the canvas widget."""
        canvas = self.query_one("#canvas", SlideCanvas)
        deck = self.app.state.deck  # type: ignore[attr-defined]
        canvas.slide = deck.slides[deck.current_index]
        canvas.selected_id = None
        canvas.deck_dir = None if deck.path is None else os.path.dirname(deck.path)
