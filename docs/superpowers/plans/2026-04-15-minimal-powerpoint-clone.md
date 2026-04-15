# Minimal PowerPoint Clone Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal PowerPoint clone in PyQt6 supporting add/delete slides and add text boxes with custom fill and text colors.

**Architecture:** One `QGraphicsScene` per slide, swapped on a central `QGraphicsView`. Text boxes are `QGraphicsRectItem` subclasses with custom paint, resize handles, and double-click edit. No persistence — state lives in memory only.

**Tech Stack:** Python ≥ 3.10, PyQt6, pytest.

**Related spec:** `docs/superpowers/specs/2026-04-15-minimal-powerpoint-clone-design.md`

---

## Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `minppt/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `.gitignore`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "minppt"
version = "0.1.0"
description = "Minimal PowerPoint clone"
requires-python = ">=3.10"
dependencies = [
    "PyQt6>=6.6",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
]

[tool.setuptools.packages.find]
include = ["minppt*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create empty `minppt/__init__.py`**

```python
```

- [ ] **Step 3: Create empty `tests/__init__.py`**

```python
```

- [ ] **Step 4: Create `tests/conftest.py` with a session-scoped QApplication fixture**

```python
"""Shared pytest fixtures."""
import sys

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session", autouse=True)
def qapp() -> QApplication:
    """Provide a session-wide QApplication so QGraphicsScene can be constructed headlessly."""
    app = QApplication.instance() or QApplication(sys.argv)
    yield app
```

- [ ] **Step 5: Create `.gitignore`**

```
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
.venv/
venv/
build/
dist/
```

- [ ] **Step 6: Install in editable mode and verify**

Run:
```bash
python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]" && pytest --collect-only
```
Expected: pytest collects zero tests without errors.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml minppt/ tests/ .gitignore
git commit -m "Scaffold minppt package with PyQt6 and pytest"
```

---

## Task 2: `Slide` model (TDD)

**Files:**
- Create: `tests/test_models.py`
- Create: `minppt/models.py`

- [ ] **Step 1: Write the first failing test**

Create `tests/test_models.py`:

```python
"""Tests for the Deck and Slide models."""
from PyQt6.QtCore import QRectF
from PyQt6.QtWidgets import QGraphicsScene

from minppt.models import Slide


def test_slide_has_scene_with_correct_bounds() -> None:
    """A new slide owns a 960x540 scene."""
    slide = Slide()
    assert isinstance(slide.scene, QGraphicsScene)
    assert slide.scene.sceneRect() == QRectF(0, 0, 960, 540)


def test_slide_starts_with_no_text_boxes() -> None:
    """A new slide has an empty text_boxes list."""
    slide = Slide()
    assert slide.text_boxes == []
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `ImportError: cannot import name 'Slide' from 'minppt.models'` (module doesn't exist yet).

- [ ] **Step 3: Implement `Slide`**

Create `minppt/models.py`:

```python
"""Data models for the minimal PowerPoint clone."""
from __future__ import annotations

from PyQt6.QtCore import QRectF
from PyQt6.QtWidgets import QGraphicsScene


SLIDE_WIDTH = 960
SLIDE_HEIGHT = 540


class Slide:
    """One slide: owns a QGraphicsScene and the list of text boxes placed on it."""

    def __init__(self) -> None:
        """Create an empty slide with a 960x540 scene."""
        self.scene: QGraphicsScene = QGraphicsScene()
        self.scene.setSceneRect(QRectF(0, 0, SLIDE_WIDTH, SLIDE_HEIGHT))
        self.text_boxes: list = []
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/test_models.py minppt/models.py
git commit -m "Add Slide model with 960x540 scene"
```

---

## Task 3: `Deck` model (TDD)

**Files:**
- Modify: `tests/test_models.py`
- Modify: `minppt/models.py`

- [ ] **Step 1: Add failing tests for `Deck`**

Append to `tests/test_models.py`:

```python
from minppt.models import Deck


def test_deck_starts_with_one_slide() -> None:
    """A brand-new deck has exactly one slide, index 0."""
    deck = Deck()
    assert len(deck.slides) == 1
    assert deck.current_index == 0


def test_deck_add_slide_inserts_after_current_by_default() -> None:
    """add_slide() with no argument inserts directly after current_index."""
    deck = Deck()
    new_slide = deck.add_slide()
    assert len(deck.slides) == 2
    assert deck.slides[1] is new_slide
    assert deck.current_index == 1


def test_deck_add_slide_at_zero_inserts_at_start_and_updates_index() -> None:
    """add_slide(at=0) inserts at index 0; current_index moves to the new slide."""
    deck = Deck()
    new_slide = deck.add_slide(at=0)
    assert deck.slides[0] is new_slide
    assert deck.current_index == 0


def test_deck_remove_slide_adjusts_current_index() -> None:
    """Removing the current slide selects the slide that took its place."""
    deck = Deck()
    deck.add_slide()  # now 2 slides, current_index = 1
    deck.remove_slide(1)
    assert len(deck.slides) == 1
    assert deck.current_index == 0


def test_deck_remove_last_slide_is_noop() -> None:
    """remove_slide refuses to delete the only remaining slide."""
    deck = Deck()
    only = deck.slides[0]
    deck.remove_slide(0)
    assert deck.slides == [only]
    assert deck.current_index == 0


def test_deck_remove_earlier_slide_decrements_current_index() -> None:
    """Removing a slide before current_index shifts current_index down by one."""
    deck = Deck()
    deck.add_slide()  # current_index = 1
    deck.remove_slide(0)
    assert deck.current_index == 0


def test_deck_move_to_sets_current_index() -> None:
    """move_to updates current_index."""
    deck = Deck()
    deck.add_slide()
    deck.add_slide()  # 3 slides
    deck.move_to(0)
    assert deck.current_index == 0
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `ImportError: cannot import name 'Deck'`.

- [ ] **Step 3: Implement `Deck`**

Append to `minppt/models.py`:

```python
class Deck:
    """The presentation: an ordered list of slides with a current selection."""

    def __init__(self) -> None:
        """Create a deck with exactly one empty slide."""
        self.slides: list[Slide] = [Slide()]
        self.current_index: int = 0

    def add_slide(self, at: int | None = None) -> Slide:
        """Insert a new slide and make it current.

        With no argument, insert directly after the current slide. When ``at``
        is given, insert at that index.
        """
        insert_at = self.current_index + 1 if at is None else at
        new_slide = Slide()
        self.slides.insert(insert_at, new_slide)
        self.current_index = insert_at
        return new_slide

    def remove_slide(self, index: int) -> None:
        """Remove the slide at ``index``; no-op if this is the only slide."""
        if len(self.slides) <= 1:
            return
        del self.slides[index]
        if self.current_index > index:
            self.current_index -= 1
        elif self.current_index >= len(self.slides):
            self.current_index = len(self.slides) - 1

    def move_to(self, index: int) -> None:
        """Select the slide at ``index``."""
        if not 0 <= index < len(self.slides):
            raise IndexError(f"slide index {index} out of range")
        self.current_index = index
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/test_models.py minppt/models.py
git commit -m "Add Deck model with add/remove/move operations"
```

---

## Task 4: `TextBoxItem` — text and color properties (TDD)

**Files:**
- Create: `minppt/textbox.py`
- Modify: `tests/test_models.py`

- [ ] **Step 1: Add failing tests for `TextBoxItem` properties**

Append to `tests/test_models.py`:

```python
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from minppt.textbox import TextBoxItem


def test_textbox_defaults() -> None:
    """A fresh TextBoxItem has default text, white fill, black text color."""
    item = TextBoxItem(QRectF(0, 0, 200, 80))
    assert item.text == "Text"
    assert item.fill_color == QColor(Qt.GlobalColor.white)
    assert item.text_color == QColor(Qt.GlobalColor.black)


def test_textbox_setters_persist_values() -> None:
    """Setting text/fill_color/text_color stores the assigned value."""
    item = TextBoxItem(QRectF(0, 0, 200, 80))
    item.text = "Hello"
    item.fill_color = QColor("red")
    item.text_color = QColor("blue")
    assert item.text == "Hello"
    assert item.fill_color == QColor("red")
    assert item.text_color == QColor("blue")


def test_textbox_uses_provided_rect() -> None:
    """The item's rect matches the constructor argument."""
    item = TextBoxItem(QRectF(10, 20, 300, 100))
    assert item.rect() == QRectF(10, 20, 300, 100)
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `ImportError: cannot import name 'TextBoxItem'`.

- [ ] **Step 3: Implement the minimal `TextBoxItem`**

Create `minppt/textbox.py`:

```python
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
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: 12 passed.

- [ ] **Step 5: Commit**

```bash
git add minppt/textbox.py tests/test_models.py
git commit -m "Add TextBoxItem with text and color properties"
```

---

## Task 5: `Slide.add_text_box` / `remove_text_box` (TDD)

**Files:**
- Modify: `minppt/models.py`
- Modify: `tests/test_models.py`

- [ ] **Step 1: Add failing tests**

Append to `tests/test_models.py`:

```python
def test_slide_add_text_box_appends_to_scene_and_list() -> None:
    """add_text_box creates a TextBoxItem, adds it to the scene and tracking list."""
    slide = Slide()
    item = slide.add_text_box(QRectF(10, 20, 200, 80))
    assert isinstance(item, TextBoxItem)
    assert item in slide.text_boxes
    assert item in slide.scene.items()


def test_slide_remove_text_box_removes_from_scene_and_list() -> None:
    """remove_text_box removes the item from both the scene and tracking list."""
    slide = Slide()
    item = slide.add_text_box(QRectF(0, 0, 100, 50))
    slide.remove_text_box(item)
    assert item not in slide.text_boxes
    assert item not in slide.scene.items()
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `AttributeError: 'Slide' object has no attribute 'add_text_box'`.

- [ ] **Step 3: Implement the methods**

In `minppt/models.py`, change the top import and add methods to `Slide`:

Change the imports at the top of the file to:

```python
from __future__ import annotations

from PyQt6.QtCore import QRectF, QSize
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import QGraphicsScene

from minppt.textbox import TextBoxItem
```

Replace the `Slide` class body's `__init__` (keep it) and add these methods to `Slide`:

```python
    def add_text_box(self, rect: QRectF) -> TextBoxItem:
        """Create a text box with the given rect, add it to the scene, and return it."""
        item = TextBoxItem(rect)
        self.scene.addItem(item)
        self.text_boxes.append(item)
        return item

    def remove_text_box(self, item: TextBoxItem) -> None:
        """Remove a text box from the scene and tracking list."""
        if item in self.text_boxes:
            self.text_boxes.remove(item)
        self.scene.removeItem(item)

    def render_thumbnail(self, size: QSize) -> QPixmap:
        """Render the slide's scene into a QPixmap of the requested size."""
        pixmap = QPixmap(size)
        pixmap.fill()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.scene.render(painter)
        painter.end()
        return pixmap
```

Also change the `text_boxes` type hint in `Slide.__init__` to:

```python
        self.text_boxes: list[TextBoxItem] = []
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: 14 passed.

- [ ] **Step 5: Commit**

```bash
git add minppt/models.py tests/test_models.py
git commit -m "Add Slide text box operations and thumbnail rendering"
```

---

## Task 6: `TextBoxItem` — selection handles, resize, clamp, inline edit

This task is UI-interactive; tests cover only the scene-rect clamp (headless). Everything else is validated in the Task 10 smoke test.

**Files:**
- Modify: `minppt/textbox.py`
- Modify: `tests/test_models.py`

- [ ] **Step 1: Add failing test for position clamping**

Append to `tests/test_models.py`:

```python
def test_textbox_clamps_position_to_scene_rect() -> None:
    """A text box cannot be moved outside the 960x540 scene rect."""
    slide = Slide()
    item = slide.add_text_box(QRectF(0, 0, 200, 80))
    # Try to push the item far off-screen; itemChange should clamp it back.
    item.setPos(5000, 5000)
    pos = item.scenePos()
    # The rect's right/bottom must not exceed the scene rect.
    assert pos.x() + item.rect().width() <= 960 + 1e-6
    assert pos.y() + item.rect().height() <= 540 + 1e-6
```

- [ ] **Step 2: Run the new test — verify it fails**

Run: `pytest tests/test_models.py::test_textbox_clamps_position_to_scene_rect -v`
Expected: FAIL — the item's position is not clamped.

- [ ] **Step 3: Replace `minppt/textbox.py` with the full implementation**

Overwrite `minppt/textbox.py` with:

```python
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
        # Center within the parent rect.
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

    # --- properties ------------------------------------------------------

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

    # --- painting --------------------------------------------------------

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

    # --- resize handles --------------------------------------------------

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

    # --- mouse behavior --------------------------------------------------

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

        # Enforce minimum size.
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

        # Clamp to scene rect (accounting for item position offset).
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

    # --- position clamp --------------------------------------------------

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
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: 15 passed.

- [ ] **Step 5: Commit**

```bash
git add minppt/textbox.py tests/test_models.py
git commit -m "Add resize handles, inline edit, and scene-rect clamp to TextBoxItem"
```

---

## Task 7: `SlidePanel` widget

**Files:**
- Create: `minppt/slide_panel.py`

- [ ] **Step 1: Create the slide panel**

Create `minppt/slide_panel.py`:

```python
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
```

- [ ] **Step 2: Sanity-check import**

Run: `python -c "from minppt.slide_panel import SlidePanel; print('ok')"`
Expected: prints `ok` without error.

- [ ] **Step 3: Commit**

```bash
git add minppt/slide_panel.py
git commit -m "Add SlidePanel thumbnail list widget"
```

---

## Task 8: `Toolbar` widget

**Files:**
- Create: `minppt/toolbar.py`

- [ ] **Step 1: Create the toolbar**

Create `minppt/toolbar.py`:

```python
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
```

- [ ] **Step 2: Sanity-check import**

Run: `python -c "from minppt.toolbar import Toolbar; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add minppt/toolbar.py
git commit -m "Add Toolbar widget with slide and text-box actions"
```

---

## Task 9: `MainWindow` wiring and entry point

**Files:**
- Create: `minppt/app.py`
- Create: `minppt/__main__.py`

- [ ] **Step 1: Create `minppt/app.py`**

```python
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

    # --- wiring ----------------------------------------------------------

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

    # --- slots -----------------------------------------------------------

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
        # Center a 200x80 box on the 960x540 slide.
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

    # --- state -----------------------------------------------------------

    def _update_toolbar_state(self) -> None:
        """Sync toolbar enabled-state with deck and selection."""
        self._toolbar.set_delete_slide_enabled(len(self._deck.slides) > 1)
        self._toolbar.set_color_actions_enabled(self._selected_text_box() is not None)
```

- [ ] **Step 2: Create `minppt/__main__.py`**

```python
"""Entry point: ``python -m minppt``."""
from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from minppt.app import MainWindow


def main() -> int:
    """Launch the GUI and return the exit code."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run the full test suite**

Run: `pytest -v`
Expected: 15 passed.

- [ ] **Step 4: Commit**

```bash
git add minppt/app.py minppt/__main__.py
git commit -m "Wire MainWindow and add python -m minppt entry point"
```

---

## Task 10: Manual smoke test

No code changes — run the app and verify every feature works end-to-end.

**Files:** none

- [ ] **Step 1: Launch the app**

Run: `python -m minppt`
Expected: window opens showing toolbar, one slide thumbnail on the left, blank slide canvas on the right.

- [ ] **Step 2: Verify add/delete slide**

- Click `+ Slide`. Expected: second thumbnail appears, canvas switches to the new blank slide.
- Click `+ Slide` again. Expected: third thumbnail.
- Click the first thumbnail. Expected: canvas switches back to slide 1.
- Click `- Slide`. Expected: current slide is removed, thumbnails renumber, canvas shows neighbor slide.
- Delete until one slide remains. Expected: `- Slide` button becomes disabled.

- [ ] **Step 3: Verify add and edit text box**

- Click `+ Text Box`. Expected: box labeled "Text" appears centered on the slide and is auto-selected with 8 handles visible.
- Drag the box. Expected: box moves and cannot leave the slide area.
- Drag a corner handle. Expected: box resizes, respects a minimum size, and cannot extend past the slide edge.
- Double-click the box. Expected: inline text editor appears; type a new string; click outside. Expected: box shows the new text.

- [ ] **Step 4: Verify color pickers**

- Select the text box. Click `Fill...`. Pick red. Expected: box fill turns red; thumbnail updates.
- Click `Text...`. Pick white. Expected: text is white on red.
- Click an empty area to deselect. Expected: `Fill...` and `Text...` buttons become disabled.

- [ ] **Step 5: Verify delete text box**

- Click a text box to select it. Press `Delete`. Expected: box is removed; thumbnail updates.

- [ ] **Step 6: Verify multi-slide thumbnails**

- Add a second slide. Add different text boxes to each. Expected: both thumbnails show their respective contents correctly.

- [ ] **Step 7: Commit any final fixes**

If the smoke test revealed issues, fix them and commit. If everything works:

```bash
echo "Smoke test passed: $(date)" >> docs/superpowers/specs/2026-04-15-minimal-powerpoint-clone-design.md
# (optional — or skip and just note it)
```

---

## Done

All spec requirements implemented:
- [x] Add slide (Task 9)
- [x] Delete slide (Task 9)
- [x] Add text box with default colors (Task 9)
- [x] Custom fill color via `QColorDialog` (Task 9)
- [x] Custom text color via `QColorDialog` (Task 9)
- [x] Slide thumbnail navigation (Tasks 7, 9)
- [x] Invariant: ≥ 1 slide (Task 3)
- [x] Invariant: text boxes clamped to canvas (Task 6)
- [x] Headless model tests (Tasks 2, 3, 4, 5, 6)
