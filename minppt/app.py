"""Main application window — wires the deck, slide panel, toolbar, and canvas."""
from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QColorDialog,
    QGraphicsView,
    QMainWindow,
    QSplitter,
)

from minppt.models import Deck, Slide
from minppt.slide_panel import SlidePanel
from minppt.textbox import TextBoxItem
from minppt.toolbar import Toolbar


class MainWindow(QMainWindow):
    """Root window holding deck state and all child widgets."""

    def __init__(self) -> None:
        """Build the window and wire every signal/slot."""
        super().__init__()
        self.setWindowTitle("minppt")
        self.resize(1200, 720)

        self._deck = Deck()

        self._toolbar = Toolbar()
        self.addToolBar(self._toolbar)

        self._slide_panel = SlidePanel(self._deck)
        self._view = QGraphicsView()
        self._view.setRenderHints(self._view.renderHints())
        self._view.setScene(self._deck.slides[0].scene)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._slide_panel)
        splitter.addWidget(self._view)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        self._delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self._view)
        self._delete_shortcut.activated.connect(self._delete_selected_text_box)

        self._connect_signals()
        self._subscribe_scene_changes(self._deck.slides[0])
        self._update_toolbar_state()

    def _connect_signals(self) -> None:
        """Hook toolbar actions and panel selection to methods on this window."""
        self._toolbar.add_slide_action.triggered.connect(self._add_slide)
        self._toolbar.delete_slide_action.triggered.connect(self._delete_slide)
        self._toolbar.add_text_box_action.triggered.connect(self._add_text_box)
        self._toolbar.fill_color_action.triggered.connect(self._pick_fill_color)
        self._toolbar.text_color_action.triggered.connect(self._pick_text_color)
        self._slide_panel.slide_selected.connect(self._on_slide_selected)

    def _subscribe_scene_changes(self, slide: Slide) -> None:
        """Refresh the thumbnail whenever ``slide``'s scene changes."""
        slide.scene.changed.connect(lambda _regions, s=slide: self._on_scene_changed(s))
        slide.scene.selectionChanged.connect(self._update_toolbar_state)

    def _add_slide(self) -> None:
        """Insert a new slide after the current one and select it."""
        new_slide = self._deck.add_slide()
        self._slide_panel.refresh()
        self._view.setScene(new_slide.scene)
        self._subscribe_scene_changes(new_slide)
        self._update_toolbar_state()

    def _delete_slide(self) -> None:
        """Remove the current slide; disabled when only one remains."""
        if len(self._deck.slides) <= 1:
            return
        self._deck.remove_slide(self._deck.current_index)
        self._slide_panel.refresh()
        self._view.setScene(self._deck.slides[self._deck.current_index].scene)
        self._update_toolbar_state()

    def _add_text_box(self) -> None:
        """Add a default-sized text box centered on the current slide."""
        slide = self._deck.slides[self._deck.current_index]
        rect = QRectF(380, 230, 200, 80)
        item = slide.add_text_box(rect)
        slide.scene.clearSelection()
        item.setSelected(True)
        item.setFocus()

    def _delete_selected_text_box(self) -> None:
        """Remove the selected text box from the current slide (ignored if mid-edit)."""
        item = self._selected_text_box()
        if item is None or item.is_editing():
            return
        slide = self._deck.slides[self._deck.current_index]
        slide.remove_text_box(item)
        self._update_toolbar_state()

    def _selected_text_box(self) -> TextBoxItem | None:
        """Return the currently selected text box, if any."""
        slide = self._deck.slides[self._deck.current_index]
        for it in slide.scene.selectedItems():
            if isinstance(it, TextBoxItem):
                return it
        return None

    def _pick_fill_color(self) -> None:
        """Prompt for a fill color and apply it to the selected text box."""
        item = self._selected_text_box()
        if item is None:
            return
        color = QColorDialog.getColor(item.fill_color, self, "Fill color")
        if color.isValid():
            item.fill_color = color

    def _pick_text_color(self) -> None:
        """Prompt for a text color and apply it to the selected text box."""
        item = self._selected_text_box()
        if item is None:
            return
        color = QColorDialog.getColor(item.text_color, self, "Text color")
        if color.isValid():
            item.text_color = color

    def _on_slide_selected(self, row: int) -> None:
        """React to thumbnail selection by swapping the visible scene."""
        self._deck.move_to(row)
        self._view.setScene(self._deck.slides[row].scene)
        self._update_toolbar_state()

    def _on_scene_changed(self, slide: Slide) -> None:
        """Refresh the thumbnail for the slide that changed."""
        try:
            index = self._deck.slides.index(slide)
        except ValueError:
            return
        self._slide_panel.refresh_thumbnail(index)

    def _update_toolbar_state(self) -> None:
        """Sync toolbar enabled-state with deck and selection."""
        self._toolbar.set_delete_slide_enabled(len(self._deck.slides) > 1)
        self._toolbar.set_color_actions_enabled(self._selected_text_box() is not None)
