# Minimal PowerPoint Clone — Design

**Date:** 2026-04-15
**Status:** Approved by user, pending implementation plan

## Goal

A minimal PowerPoint clone in Python. The only features:

1. Add and delete slides.
2. Add text boxes on a slide, with custom fill color and text color.

Explicitly **out of scope:** animations, transitions, images, shapes beyond text boxes, persistence (save/load), export (to `.pptx` or any other format), undo/redo, multi-select, templates, alignment guides, font choice beyond the system default.

## Technology Choices

| Concern | Choice | Reason |
|---|---|---|
| GUI framework | PyQt6 | User preference; rich widget set; `QGraphicsScene` gives selection/drag/z-order for free. |
| Persistence | None | In-memory only. Closing the app discards the deck. |
| Dependencies | `PyQt6` only | No second-order deps needed. |
| Python | ≥ 3.10 | Modern type syntax (`X | None`). |

## Architecture

**One `QGraphicsScene` per slide.** Each `Slide` owns its own `QGraphicsScene`; text boxes are `QGraphicsItem`s inside that scene. Switching slides swaps the scene on the single central `QGraphicsView`.

Rejected alternatives:
- **Custom `QWidget` canvas with manual `paintEvent`** — 5× the code for selection, drag, resize, hit testing. Not justified for the feature set.
- **Single shared scene with per-slide visibility toggles** — awkward thumbnail rendering; couples slides together unnecessarily.

## Project Structure

```
ascii_3d/
├── minppt/
│   ├── __init__.py
│   ├── __main__.py        # entry point: `python -m minppt`
│   ├── app.py             # MainWindow, wires toolbar + slide panel + view
│   ├── models.py          # Deck, Slide
│   ├── textbox.py         # TextBoxItem (resizable, editable)
│   ├── slide_panel.py     # Left-side QListWidget thumbnail list
│   └── toolbar.py         # Top QToolBar with slide/text-box/color actions
├── tests/
│   └── test_models.py     # Headless model logic tests (pytest)
├── pyproject.toml         # PyQt6 dep, ruff config
└── README.md
```

## Data Model

```python
# models.py

class Slide:
    """One slide. Owns its QGraphicsScene and its text boxes."""
    scene: QGraphicsScene            # sceneRect = QRectF(0, 0, 960, 540)
    text_boxes: list[TextBoxItem]
    def add_text_box(self, rect: QRectF) -> TextBoxItem
    def remove_text_box(self, item: TextBoxItem) -> None
    def render_thumbnail(self, size: QSize) -> QPixmap

class Deck:
    """The presentation. Ordered list of slides + current index."""
    slides: list[Slide]
    current_index: int
    def add_slide(self, at: int | None = None) -> Slide   # default: after current
    def remove_slide(self, index: int) -> None            # no-op if only 1 slide
    def move_to(self, index: int) -> None
```

```python
# textbox.py

class TextBoxItem(QGraphicsRectItem):
    """A resizable, movable text box with custom fill + text color."""
    text: str                        # default: "Text"
    fill_color: QColor               # default: Qt.white
    text_color: QColor               # default: Qt.black
    # Flags: ItemIsSelectable | ItemIsMovable | ItemSendsGeometryChanges
    # paint(): draw fill rect, then centered text in text_color
    # paint() when selected: draw 8 resize handles on the rect edges/corners
    # mousePressEvent: hit-test handles; if on a handle, enter resize mode
    # mouseMoveEvent: update rect during handle drag; otherwise default move
    # itemChange(ItemPositionChange, newPos): clamp to scene rect
    # mouseDoubleClickEvent: enter edit mode (child QGraphicsTextItem, focus it)
    # on edit focus-out: copy text back to self.text, remove child, update()
```

**Invariants:**
- `Deck` always has ≥ 1 slide. `remove_slide` on the last slide is a no-op; the UI "– Slide" button is disabled in that state.
- Text boxes are constrained to the slide canvas (960×540). `TextBoxItem.itemChange(ItemPositionChange, newPos)` clamps `newPos` so the item's bounding rect stays inside the scene rect. Resize handle logic also clamps the rect to the scene bounds.

## UI Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ Toolbar: [+ Slide] [– Slide] │ [+ Text Box] [Fill…] [Text…]      │
├────────────┬─────────────────────────────────────────────────────┤
│ Slide 1 ▸  │                                                     │
│ ┌────────┐ │                                                     │
│ │ thumb  │ │         QGraphicsView (current slide)               │
│ └────────┘ │                                                     │
│ Slide 2    │            — 960×540 slide canvas —                 │
│ ┌────────┐ │                                                     │
│ │ thumb  │ │                                                     │
│ └────────┘ │                                                     │
└────────────┴─────────────────────────────────────────────────────┘
```

- `QMainWindow` + `QToolBar` + central `QSplitter` (horizontal).
- **SlidePanel** — `QListWidget` in `IconMode`, vertical flow, icon size 160×90, label "Slide N". Current selection drives the active slide.
- **Canvas** — `QGraphicsView` whose scene is swapped when the selection changes.
- **Color dialogs** — `QColorDialog.getColor()` on toolbar click.
- **Enable/disable rules:**
  - "– Slide" disabled when `len(deck.slides) == 1`.
  - "+ Text Box" always enabled (requires a slide, which always exists).
  - "Fill…" / "Text…" disabled unless exactly one `TextBoxItem` is selected.

**Thumbnail refresh:** the main window connects each `Slide.scene.changed` signal to a slot that re-renders that slide's thumbnail via `QGraphicsScene.render()` into a `QPixmap` and updates the corresponding `QListWidgetItem` icon. No debouncing — the scene is small and updates are infrequent relative to frame rate.

## Interactions

| Action | How |
|---|---|
| Add slide | "+ Slide" → `Deck.add_slide()` after current index → select new slide |
| Delete slide | "– Slide" → `Deck.remove_slide(current_index)` → select the slide that took its place, or the previous slide if the deleted one was last (disabled when only 1 slide) |
| Switch slide | Click thumbnail → `view.setScene(slide.scene)` → update toolbar enable state |
| Add text box | "+ Text Box" → insert 200×80 `TextBoxItem` at slide center with default text "Text", white fill, black text → auto-select it |
| Move text box | Drag (built-in via `ItemIsMovable`) |
| Resize text box | Drag one of 8 handles shown on selection |
| Edit text | Double-click → swap to child `QGraphicsTextItem` in edit mode → commit on focus-out |
| Delete text box | `Delete` key with text box selected → `slide.remove_text_box(item)` |
| Change fill color | Select box → "Fill…" → `QColorDialog` → update `fill_color` → repaint |
| Change text color | Select box → "Text…" → `QColorDialog` → update `text_color` → repaint |

## Error Handling

This is a local desktop app with no I/O, no network, no file access, no persistence. There is nothing to fail from the outside. The only invariants are the ones listed above (≥ 1 slide, text boxes bounded to scene rect), enforced in the model and mirrored in the UI's enable/disable state.

## Testing

**Scope:** headless model tests only. No UI interaction tests — manual smoke test at the end of implementation.

**File:** `tests/test_models.py` with `pytest`. Uses a module-scoped `QApplication` fixture so `QGraphicsScene` can be constructed without showing any window.

**Cases to cover:**
- `Deck` starts with exactly 1 slide; `current_index == 0`.
- `Deck.add_slide()` with no arg inserts after `current_index` and returns the new `Slide`.
- `Deck.add_slide(at=0)` inserts at index 0; `current_index` is updated to point at the new slide (the returned one).
- `Deck.remove_slide(i)` removes and adjusts `current_index` to stay valid.
- `Deck.remove_slide(0)` when `len(slides) == 1` is a no-op (deck unchanged).
- `Slide.add_text_box(rect)` returns a `TextBoxItem`, adds it to `scene.items()` and to `text_boxes`.
- `Slide.remove_text_box(item)` removes from both.
- `TextBoxItem.text`, `fill_color`, `text_color` setters persist the assigned value.

## Running

```
pip install PyQt6
python -m minppt
```

## Open Questions

None. All design choices have been agreed with the user.
