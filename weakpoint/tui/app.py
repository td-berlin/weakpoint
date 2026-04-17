"""Textual App that ties screens, widgets, and commands together."""
from __future__ import annotations

import os

from textual.app import App
from textual.binding import Binding

from weakpoint.tui.commands import AppState, ParseError, dispatch, parse
from weakpoint.tui.models import SLIDE_COLS, SLIDE_ROWS, Deck, Slide, TextBox
from weakpoint.tui.persistence import load_deck
from weakpoint.tui.screens.edit_screen import EditScreen
from weakpoint.tui.screens.present_screen import PresentScreen
from weakpoint.tui.widgets.command_bar import CommandBar
from weakpoint.tui.widgets.slide_canvas import SlideCanvas
from weakpoint.tui.widgets.slide_panel import SlidePanel
from weakpoint.tui.widgets.status_bar import StatusBar


MOVE_DELTAS = {"h": (-1, 0), "l": (1, 0), "k": (0, -1), "j": (0, 1)}


class WeakpointTuiApp(App):
    """Terminal-only PowerPoint clone, keyboard-first modal UI."""

    BINDINGS = [
        Binding("colon", "enter_command", "command", priority=True),
        Binding("n", "next_slide", "next slide"),
        Binding("N", "prev_slide", "prev slide"),
        Binding("a", "append_slide", "append slide"),
        Binding("A", "insert_slide_before", "insert slide"),
        Binding("tab", "cycle_selection(1)", "cycle +"),
        Binding("shift+tab", "cycle_selection(-1)", "cycle -"),
        Binding("escape", "deselect", "deselect"),
        Binding("h", "move_selected('h')", "left"),
        Binding("j", "move_selected('j')", "down"),
        Binding("k", "move_selected('k')", "up"),
        Binding("l", "move_selected('l')", "right"),
        Binding("H", "resize_selected('h')", "shrink w"),
        Binding("L", "resize_selected('l')", "grow w"),
        Binding("K", "resize_selected('k')", "shrink h"),
        Binding("J", "resize_selected('j')", "grow h"),
        Binding("x", "delete_selected", "delete item"),
        Binding("b", "toggle_bold", "bold"),
        Binding("i", "edit_text", "insert text"),
        Binding("p", "present", "present"),
        Binding("d,d", "delete_slide", "delete slide"),
        Binding("q", "quit_cmd", "quit"),
    ]

    def __init__(self, initial_path: str | None = None) -> None:
        """Build the App with a fresh deck or load one from ``initial_path``."""
        super().__init__()
        deck = Deck()
        if initial_path:
            try:
                deck = load_deck(initial_path)
            except (FileNotFoundError, ValueError) as exc:
                self._boot_error: str | None = f"could not load {initial_path}: {exc}"
            else:
                self._boot_error = None
        else:
            self._boot_error = None
        self.state = AppState(deck=deck)
        self.state_mode: str = "NORMAL"
        self._insert_target_id: str | None = None

    def on_mount(self) -> None:
        """Install the EditScreen and refresh the UI on first mount."""
        self.push_screen(EditScreen(), callback=self._after_screen_mounted)

    def _after_screen_mounted(self) -> None:
        """Refresh the UI once EditScreen and its children are composed."""
        self._refresh_ui()
        if self._boot_error:
            self._set_status_message(self._boot_error, error=True)

    # --- action handlers -----------------------------------------------

    def action_enter_command(self) -> None:
        """Show the command bar and switch to COMMAND mode."""
        bar = self.screen.query_one(CommandBar)
        bar.show(":")
        self._set_mode("COMMAND")

    def action_next_slide(self) -> None:
        """Advance to the next slide if possible."""
        deck = self.state.deck
        if deck.current_index + 1 < len(deck.slides):
            deck.current_index += 1
            self.state.selected_id = None
            self._refresh_ui()

    def action_prev_slide(self) -> None:
        """Go to the previous slide if possible."""
        deck = self.state.deck
        if deck.current_index > 0:
            deck.current_index -= 1
            self.state.selected_id = None
            self._refresh_ui()

    def action_append_slide(self) -> None:
        """Insert a new slide after the current one and select it."""
        deck = self.state.deck
        deck.slides.insert(deck.current_index + 1, Slide())
        deck.current_index += 1
        self.state.selected_id = None
        self.state.dirty = True
        self._refresh_ui("slide added")

    def action_insert_slide_before(self) -> None:
        """Insert a new slide before the current one and select it."""
        deck = self.state.deck
        deck.slides.insert(deck.current_index, Slide())
        self.state.selected_id = None
        self.state.dirty = True
        self._refresh_ui("slide inserted")

    def action_delete_slide(self) -> None:
        """Delete the current slide; refuses if it's the only one."""
        deck = self.state.deck
        if len(deck.slides) <= 1:
            self._set_status_message("can't delete last slide", error=True)
            return
        del deck.slides[deck.current_index]
        if deck.current_index >= len(deck.slides):
            deck.current_index = len(deck.slides) - 1
        self.state.selected_id = None
        self.state.dirty = True
        self._refresh_ui("slide deleted")

    def action_cycle_selection(self, direction: int) -> None:
        """Cycle through items on the current slide in ``direction`` (+1 or -1)."""
        slide = self._current_slide()
        items = slide.items()
        if not items:
            return
        ids = [it.id for it in items]
        if self.state.selected_id not in ids:
            self.state.selected_id = ids[0 if direction > 0 else -1]
        else:
            i = ids.index(self.state.selected_id)
            self.state.selected_id = ids[(i + direction) % len(ids)]
        self._refresh_ui()

    def action_deselect(self) -> None:
        """Esc: cancel COMMAND/INSERT mode if active, otherwise clear selection."""
        if self.state_mode in ("COMMAND", "INSERT"):
            bar = self.screen.query_one(CommandBar)
            bar.hide()
            self._insert_target_id = None
            self._set_mode("NORMAL")
            self._set_status_message("cancelled")
            return
        self.state.selected_id = None
        self._refresh_ui()

    def action_move_selected(self, key: str) -> None:
        """Move the selected item one cell in the direction of ``key`` (h/j/k/l)."""
        item = self._selected_item()
        if item is None:
            return
        dx, dy = MOVE_DELTAS[key]
        item.x = max(0, min(SLIDE_COLS - item.w, item.x + dx))
        item.y = max(0, min(SLIDE_ROWS - item.h, item.y + dy))
        self.state.dirty = True
        self._refresh_ui()

    def action_resize_selected(self, key: str) -> None:
        """Resize the selected item in the direction of ``key`` (h/j/k/l)."""
        item = self._selected_item()
        if item is None:
            return
        if key == "l":
            item.w = min(SLIDE_COLS - item.x, item.w + 1)
        elif key == "h":
            item.w = max(1, item.w - 1)
        elif key == "j":
            item.h = min(SLIDE_ROWS - item.y, item.h + 1)
        elif key == "k":
            item.h = max(1, item.h - 1)
        self.state.dirty = True
        self._refresh_ui()

    def action_delete_selected(self) -> None:
        """Delete the currently selected item."""
        item = self._selected_item()
        if item is None:
            return
        slide = self._current_slide()
        if item in slide.text_boxes:
            slide.text_boxes.remove(item)
        else:
            slide.images.remove(item)
        self.state.selected_id = None
        self.state.dirty = True
        self._refresh_ui("item deleted")

    def action_toggle_bold(self) -> None:
        """Toggle bold on the selected text box."""
        item = self._selected_item()
        if not isinstance(item, TextBox):
            self._set_status_message("select a text box first", error=True)
            return
        item.bold = not item.bold
        self.state.dirty = True
        self._refresh_ui()

    def action_edit_text(self) -> None:
        """Open the command bar to edit the selected text box's contents."""
        item = self._selected_item()
        if not isinstance(item, TextBox):
            self._set_status_message("select a text box first", error=True)
            return
        bar = self.screen.query_one(CommandBar)
        bar.show("text:")
        bar.value = item.text
        self._set_mode("INSERT")
        self._insert_target_id = item.id

    def action_present(self) -> None:
        """Switch to the present-mode screen."""
        self.push_screen(PresentScreen())

    def action_quit_cmd(self) -> None:
        """Quit (refused if there are unsaved changes)."""
        if self.state.dirty:
            self._set_status_message("unsaved changes — use :q! or :wq", error=True)
            return
        self.exit()

    # --- command bar submission ----------------------------------------

    def on_input_submitted(self, event) -> None:
        """Handle Enter on the command bar: dispatch a command or commit edited text."""
        mode = self.state_mode
        if mode not in ("COMMAND", "INSERT"):
            return
        bar = self.screen.query_one(CommandBar)
        value = event.value
        bar.hide()
        self._set_mode("NORMAL")
        if mode == "INSERT":
            target_id = self._insert_target_id
            self._insert_target_id = None
            if target_id is None:
                return
            slide = self._current_slide()
            for b in slide.text_boxes:
                if b.id == target_id:
                    b.text = value
                    self.state.dirty = True
                    break
            self._refresh_ui("text updated")
            return
        try:
            cmd = parse(value)
        except ParseError as exc:
            self._set_status_message(str(exc), error=True)
            return
        res = dispatch(cmd, self.state)
        if self.state.should_quit:
            self.exit()
            return
        self._set_status_message(res.message, error=res.error)
        self._refresh_ui()

    # --- helpers --------------------------------------------------------

    def _current_slide(self) -> Slide:
        """Return the slide at the current index."""
        return self.state.deck.slides[self.state.deck.current_index]

    def _selected_item(self):
        """Return the currently selected item (TextBox | Image | None)."""
        if self.state.selected_id is None:
            return None
        slide = self._current_slide()
        for it in slide.items():
            if it.id == self.state.selected_id:
                return it
        return None

    def _set_mode(self, mode: str) -> None:
        """Update mode state and reflect it on the status bar."""
        self.state_mode = mode
        try:
            status = self.screen.query_one(StatusBar)
        except Exception:
            return
        status.mode = mode

    def _set_status_message(self, msg: str, error: bool = False) -> None:
        """Push a status message (red if error) to the status bar."""
        try:
            status = self.screen.query_one(StatusBar)
        except Exception:
            return
        status.message = msg
        status.error = error

    def _refresh_ui(self, message: str | None = None) -> None:
        """Push current state into all visible widgets and optionally set a message."""
        deck = self.state.deck
        canvas = self.screen.query_one(SlideCanvas)
        canvas.slide = deck.slides[deck.current_index]
        canvas.selected_id = self.state.selected_id
        canvas.deck_dir = None if deck.path is None else os.path.dirname(deck.path)

        panel = self.screen.query_one(SlidePanel)
        panel.deck = deck
        panel.refresh()

        status = self.screen.query_one(StatusBar)
        status.slide_i = deck.current_index + 1
        status.slide_n = len(deck.slides)
        status.path = deck.path
        status.dirty = self.state.dirty
        if message is not None:
            status.message = message
            status.error = False
