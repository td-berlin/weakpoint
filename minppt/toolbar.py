"""Top toolbar with slide and text-box actions."""
from __future__ import annotations

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QSpinBox, QToolBar


class Toolbar(QToolBar):
    """Toolbar exposing slide, text-box, color, and font actions."""

    def __init__(self) -> None:
        """Create all actions; callers wire them to MainWindow slots."""
        super().__init__("Main")
        self.setMovable(False)

        self.add_slide_action = QAction("+ Slide", self)
        self.delete_slide_action = QAction("- Slide", self)
        self.add_text_box_action = QAction("+ Text Box", self)
        self.fill_color_action = QAction("Fill...", self)
        self.text_color_action = QAction("Text...", self)
        self.bold_action = QAction("Bold", self)
        self.bold_action.setCheckable(True)

        self.size_spinbox = QSpinBox()
        self.size_spinbox.setRange(6, 144)
        self.size_spinbox.setValue(18)
        self.size_spinbox.setPrefix("Size: ")

        self.addAction(self.add_slide_action)
        self.addAction(self.delete_slide_action)
        self.addSeparator()
        self.addAction(self.add_text_box_action)
        self.addAction(self.fill_color_action)
        self.addAction(self.text_color_action)
        self.addSeparator()
        self.addWidget(self.size_spinbox)
        self.addAction(self.bold_action)

    def set_delete_slide_enabled(self, enabled: bool) -> None:
        """Enable/disable the delete-slide action (disabled when 1 slide remains)."""
        self.delete_slide_action.setEnabled(enabled)

    def set_color_actions_enabled(self, enabled: bool) -> None:
        """Enable/disable fill and text color actions based on selection."""
        self.fill_color_action.setEnabled(enabled)
        self.text_color_action.setEnabled(enabled)

    def set_font_actions_enabled(self, enabled: bool) -> None:
        """Enable/disable the size spinbox and bold action based on selection."""
        self.size_spinbox.setEnabled(enabled)
        self.bold_action.setEnabled(enabled)
