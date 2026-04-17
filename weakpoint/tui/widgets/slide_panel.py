"""Sidebar: vertical list of slide mini-canvases."""
from __future__ import annotations

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget

from weakpoint.tui.models import Deck
from weakpoint.tui.render import compose_slide_small, grid_to_rich_text


MINI_COLS = 20
MINI_ROWS = 6


class SlidePanel(Widget):
    """Renders a list of mini-canvases, one per slide, with the current one marked."""

    deck: reactive[Deck | None] = reactive(None)

    def render(self) -> Text:
        """Render the slide panel with mini-canvases for each slide."""
        if self.deck is None:
            return Text("")
        parts: list[Text] = []
        for i, slide in enumerate(self.deck.slides):
            marker = "▸" if i == self.deck.current_index else " "
            header = Text(f"{i + 1:>2} {marker}", style="bold" if i == self.deck.current_index else "")
            body = grid_to_rich_text(compose_slide_small(slide, MINI_COLS, MINI_ROWS))
            parts.append(header)
            parts.append(Text("\n"))
            parts.append(body)
            parts.append(Text("\n\n"))
        out = Text()
        for p in parts:
            out.append_text(p)
        return out
