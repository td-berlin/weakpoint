"""Text box graphics item for slide content."""
from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QStyleOptionGraphicsItem,
    QWidget,
)


class TextBoxItem(QGraphicsRectItem):
    """A resizable, movable text box with custom fill and text colors."""

    HANDLE_SIZE = 8.0

    def __init__(self, rect: QRectF, text: str = "Text") -> None:
        """Create a text box with the given rect and initial text."""
        super().__init__(rect)
        self._text: str = text
        self._fill_color: QColor = QColor(Qt.GlobalColor.white)
        self._text_color: QColor = QColor(Qt.GlobalColor.black)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

    @property
    def text(self) -> str:
        """The displayed text."""
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value
        self.update()

    @property
    def fill_color(self) -> QColor:
        """The rectangle fill color."""
        return self._fill_color

    @fill_color.setter
    def fill_color(self, value: QColor) -> None:
        self._fill_color = QColor(value)
        self.update()

    @property
    def text_color(self) -> QColor:
        """The color used to draw the text."""
        return self._text_color

    @text_color.setter
    def text_color(self, value: QColor) -> None:
        self._text_color = QColor(value)
        self.update()

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """Draw the fill rectangle and centered text."""
        painter.save()
        painter.setPen(QPen(Qt.GlobalColor.darkGray, 1))
        painter.setBrush(self._fill_color)
        painter.drawRect(self.rect())

        painter.setPen(self._text_color)
        painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), self._text)
        painter.restore()
