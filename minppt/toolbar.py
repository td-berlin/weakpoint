"""Top toolbar with slide and text-box actions."""
from __future__ import annotations

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QToolBar


class Toolbar(QToolBar):
    """Toolbar exposing add/delete-slide, add-text-box, and color actions."""

    def __init__(self) -> None:
        """Create all actions; callers wire them to MainWindow slots."""
        super().__init__("Main")
        self.setMovable(False)

        self.add_slide_action = QAction("+ Slide", self)
        self.delete_slide_action = QAction("- Slide", self)
        self.add_text_box_action = QAction("+ Text Box", self)
        self.fill_color_action = QAction("Fill...", self)
        self.text_color_action = QAction("Text...", self)

        self.addAction(self.add_slide_action)
        self.addAction(self.delete_slide_action)
        self.addSeparator()
        self.addAction(self.add_text_box_action)
        self.addAction(self.fill_color_action)
        self.addAction(self.text_color_action)

    def set_delete_slide_enabled(self, enabled: bool) -> None:
        """Enable/disable the delete-slide action (disabled when 1 slide remains)."""
        self.delete_slide_action.setEnabled(enabled)

    def set_color_actions_enabled(self, enabled: bool) -> None:
        """Enable/disable fill and text color actions based on selection."""
        self.fill_color_action.setEnabled(enabled)
        self.text_color_action.setEnabled(enabled)
