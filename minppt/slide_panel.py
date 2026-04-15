"""Left-side slide thumbnail list widget."""
from __future__ import annotations

from PyQt6.QtCore import QSize, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QListWidget, QListWidgetItem

from minppt.models import Deck, Slide


THUMB_SIZE = QSize(160, 90)


class SlidePanel(QListWidget):
    """List widget showing a thumbnail per slide; selection picks the active slide."""

    slide_selected = pyqtSignal(int)  # emits new current index

    def __init__(self, deck: Deck) -> None:
        """Bind the panel to ``deck`` and populate initial thumbnails."""
        super().__init__()
        self._deck = deck
        self.setIconSize(THUMB_SIZE)
        self.setFixedWidth(THUMB_SIZE.width() + 40)
        self.currentRowChanged.connect(self._on_row_changed)
        self.refresh()

    def refresh(self) -> None:
        """Rebuild the list to match ``self._deck``."""
        self.blockSignals(True)
        self.clear()
        for i, slide in enumerate(self._deck.slides):
            item = QListWidgetItem(f"Slide {i + 1}")
            item.setIcon(QIcon(slide.render_thumbnail(THUMB_SIZE)))
            self.addItem(item)
        self.setCurrentRow(self._deck.current_index)
        self.blockSignals(False)

    def refresh_thumbnail(self, index: int) -> None:
        """Re-render the thumbnail for a single slide without rebuilding the list."""
        if not 0 <= index < self.count():
            return
        slide = self._deck.slides[index]
        self.item(index).setIcon(QIcon(slide.render_thumbnail(THUMB_SIZE)))

    def _on_row_changed(self, row: int) -> None:
        """Forward selection changes as a high-level signal."""
        if row >= 0:
            self.slide_selected.emit(row)
