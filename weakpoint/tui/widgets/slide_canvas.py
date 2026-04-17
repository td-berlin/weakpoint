"""Textual widget that renders a single Slide as a Rich Text."""
from __future__ import annotations

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget

from weakpoint.tui.models import Slide
from weakpoint.tui.render import compose_slide, grid_to_rich_text


class SlideCanvas(Widget):
    """Render the active slide at full resolution (100x30 cells)."""

    DEFAULT_CSS = """
    SlideCanvas {
        width: 100;
        height: 30;
    }
    """

    slide: reactive[Slide | None] = reactive(None)
    selected_id: reactive[str | None] = reactive(None)
    deck_dir: reactive[str | None] = reactive(None)

    def render(self) -> Text:
        """Render the slide to Rich Text."""
        if self.slide is None:
            return Text("")
        grid = compose_slide(self.slide, self.selected_id, self.deck_dir)
        return grid_to_rich_text(grid)
