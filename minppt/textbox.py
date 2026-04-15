"""Text box graphics item for slide content."""
from __future__ import annotations

from enum import Enum, auto

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFocusEvent, QPainter, QPen
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsSceneMouseEvent,
    QGraphicsTextItem,
    QStyleOptionGraphicsItem,
    QWidget,
)


class _Handle(Enum):
    """Which resize handle is being dragged."""

    NONE = auto()
    TOP_LEFT = auto()
    TOP = auto()
    TOP_RIGHT = auto()
    RIGHT = auto()
    BOTTOM_RIGHT = auto()
    BOTTOM = auto()
    BOTTOM_LEFT = auto()
    LEFT = auto()


class _EditableText(QGraphicsTextItem):
    """Child text item used only during inline editing; commits on focus-out."""

    def __init__(self, parent: "TextBoxItem") -> None:
        """Create an editable child pinned to the parent text box."""
        super().__init__(parent.text, parent)
        self._parent_box = parent
        self.setDefaultTextColor(parent.text_color)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        rect = parent.rect()
        self.setPos(rect.topLeft())
        self.setTextWidth(rect.width())

    def focusOutEvent(self, event: QFocusEvent) -> None:
        """Commit edited text back to the parent and remove self."""
        new_text = self.toPlainText()
        self._parent_box.text = new_text
        super().focusOutEvent(event)
        self._parent_box._finish_edit()


class TextBoxItem(QGraphicsRectItem):
    """A resizable, movable text box with custom fill and text colors."""

    HANDLE_SIZE = 8.0
    MIN_SIZE = 20.0

    def __init__(self, rect: QRectF, text: str = "Text") -> None:
        """Create a text box with the given rect and initial text."""
        super().__init__(rect)
        self._text: str = text
        self._fill_color: QColor = QColor(Qt.GlobalColor.white)
        self._text_color: QColor = QColor(Qt.GlobalColor.black)
        self._active_handle: _Handle = _Handle.NONE
        self._editor: _EditableText | None = None
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

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

    def boundingRect(self) -> QRectF:
        """Return the rect plus a margin so selection handles can be drawn."""
        margin = self.HANDLE_SIZE / 2 + 1
        return self.rect().adjusted(-margin, -margin, margin, margin)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """Draw the fill rectangle, centered text, and optional selection handles."""
        painter.save()
        painter.setPen(QPen(Qt.GlobalColor.darkGray, 1))
        painter.setBrush(self._fill_color)
        painter.drawRect(self.rect())

        if self._editor is None:
            painter.setPen(self._text_color)
            painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), self._text)

        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.blue, 1))
            painter.setBrush(Qt.GlobalColor.white)
            for handle_rect in self._handle_rects().values():
                painter.drawRect(handle_rect)
        painter.restore()

    def _handle_rects(self) -> dict[_Handle, QRectF]:
        """Return the small rectangles covering each resize handle."""
        r = self.rect()
        s = self.HANDLE_SIZE
        half = s / 2
        cx = r.center().x()
        cy = r.center().y()
        return {
            _Handle.TOP_LEFT: QRectF(r.left() - half, r.top() - half, s, s),
            _Handle.TOP: QRectF(cx - half, r.top() - half, s, s),
            _Handle.TOP_RIGHT: QRectF(r.right() - half, r.top() - half, s, s),
            _Handle.RIGHT: QRectF(r.right() - half, cy - half, s, s),
            _Handle.BOTTOM_RIGHT: QRectF(r.right() - half, r.bottom() - half, s, s),
            _Handle.BOTTOM: QRectF(cx - half, r.bottom() - half, s, s),
            _Handle.BOTTOM_LEFT: QRectF(r.left() - half, r.bottom() - half, s, s),
            _Handle.LEFT: QRectF(r.left() - half, cy - half, s, s),
        }

    def _handle_at(self, pos: QPointF) -> _Handle:
        """Return the handle (if any) that contains the local point ``pos``."""
        for handle, rect in self._handle_rects().items():
            if rect.contains(pos):
                return handle
        return _Handle.NONE

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Begin resize if clicking a handle; otherwise delegate to default move."""
        if self.isSelected():
            handle = self._handle_at(event.pos())
            if handle is not _Handle.NONE:
                self._active_handle = handle
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Resize if a handle is active; otherwise default move."""
        if self._active_handle is not _Handle.NONE:
            self._resize_from(event.pos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """End any in-progress resize."""
        self._active_handle = _Handle.NONE
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Enter inline text edit mode."""
        if self._editor is None:
            self._editor = _EditableText(self)
            self._editor.setFocus(Qt.FocusReason.MouseFocusReason)
        event.accept()

    def _finish_edit(self) -> None:
        """Clean up the editor child after focus-out."""
        if self._editor is not None:
            self.scene().removeItem(self._editor)
            self._editor = None
            self.update()

    def _resize_from(self, local_pos: QPointF) -> None:
        """Compute the new rect based on which handle is being dragged."""
        r = QRectF(self.rect())
        x, y = local_pos.x(), local_pos.y()
        match self._active_handle:
            case _Handle.TOP_LEFT:
                r.setTopLeft(QPointF(x, y))
            case _Handle.TOP:
                r.setTop(y)
            case _Handle.TOP_RIGHT:
                r.setTopRight(QPointF(x, y))
            case _Handle.RIGHT:
                r.setRight(x)
            case _Handle.BOTTOM_RIGHT:
                r.setBottomRight(QPointF(x, y))
            case _Handle.BOTTOM:
                r.setBottom(y)
            case _Handle.BOTTOM_LEFT:
                r.setBottomLeft(QPointF(x, y))
            case _Handle.LEFT:
                r.setLeft(x)
            case _Handle.NONE:
                return

        if r.width() < self.MIN_SIZE:
            if r.left() != self.rect().left():
                r.setLeft(r.right() - self.MIN_SIZE)
            else:
                r.setRight(r.left() + self.MIN_SIZE)
        if r.height() < self.MIN_SIZE:
            if r.top() != self.rect().top():
                r.setTop(r.bottom() - self.MIN_SIZE)
            else:
                r.setBottom(r.top() + self.MIN_SIZE)

        scene = self.scene()
        if scene is not None:
            scene_rect = scene.sceneRect()
            offset = self.pos()
            local_scene = QRectF(
                scene_rect.x() - offset.x(),
                scene_rect.y() - offset.y(),
                scene_rect.width(),
                scene_rect.height(),
            )
            r = r.intersected(local_scene)

        self.prepareGeometryChange()
        self.setRect(r)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """Clamp the proposed position so the item stays within the scene rect."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos: QPointF = value
            scene_rect = self.scene().sceneRect()
            r = self.rect()
            min_x = scene_rect.left() - r.left()
            max_x = scene_rect.right() - r.right()
            min_y = scene_rect.top() - r.top()
            max_y = scene_rect.bottom() - r.bottom()
            clamped = QPointF(
                min(max(new_pos.x(), min_x), max_x),
                min(max(new_pos.y(), min_y), max_y),
            )
            return clamped
        return super().itemChange(change, value)

    def is_editing(self) -> bool:
        """True while an inline text editor is active on this box."""
        return self._editor is not None
