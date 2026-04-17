"""The main editing screen: sidebar, canvas, status bar, command bar."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen

from weakpoint.tui.widgets.command_bar import CommandBar
from weakpoint.tui.widgets.slide_canvas import SlideCanvas
from weakpoint.tui.widgets.slide_panel import SlidePanel
from weakpoint.tui.widgets.status_bar import StatusBar


class EditScreen(Screen):
    """Layout: [SlidePanel | SlideCanvas] above [StatusBar] above [CommandBar]."""

    DEFAULT_CSS = """
    EditScreen {
        layout: vertical;
    }
    #main {
        height: 1fr;
    }
    #panel {
        width: 24;
    }
    #canvas {
        width: auto;
        height: auto;
    }
    StatusBar {
        height: 1;
        background: $boost;
    }
    """

    def compose(self) -> ComposeResult:
        """Yield the screen's child widgets."""
        with Vertical():
            with Horizontal(id="main"):
                yield SlidePanel(id="panel")
                yield SlideCanvas(id="canvas")
            yield StatusBar(id="status")
            yield CommandBar(id="cmd")
