# WeakPoint TUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a terminal-only PowerPoint clone as a new subpackage `weakpoint.tui` inside the existing repo.

**Architecture:** Textual App with vim-style modal editing. Pure data model (dataclasses), single-canvas Rich renderable per slide (grid of `(char, color)` cells), Pillow-based image→ASCII conversion. Pure modules (models, persistence, image_ascii, render, commands) must not import Textual and are fully unit-tested; Textual code (app/widgets/screens) is thin glue validated by pilot tests.

**Tech Stack:** Python 3.10+, Textual ≥0.60, Rich (via Textual), Pillow ≥10, pytest ≥8.

**Spec:** `docs/superpowers/specs/2026-04-16-weakpoint-tui-design.md`

---

## File Structure

**Created (new):**
- `weakpoint/tui/__init__.py` — package marker
- `weakpoint/tui/__main__.py` — CLI entry: `python -m weakpoint.tui [path]`
- `weakpoint/tui/models.py` — dataclasses: `TextBox`, `Image`, `Slide`, `Deck`; constants `SLIDE_COLS=100`, `SLIDE_ROWS=30`
- `weakpoint/tui/persistence.py` — `save_deck`, `load_deck`, JSON v1
- `weakpoint/tui/image_ascii.py` — `render(path, cols, rows)` with LRU cache
- `weakpoint/tui/render.py` — `compose_slide`, `compose_slide_small`, `grid_to_rich_text`
- `weakpoint/tui/commands.py` — parser + dispatcher for modal commands
- `weakpoint/tui/app.py` — Textual `App` subclass
- `weakpoint/tui/widgets/__init__.py`
- `weakpoint/tui/widgets/slide_canvas.py` — renders a grid via Rich Text
- `weakpoint/tui/widgets/slide_panel.py` — sidebar mini-canvases
- `weakpoint/tui/widgets/command_bar.py` — `:` input
- `weakpoint/tui/widgets/status_bar.py` — mode + counter + last message
- `weakpoint/tui/screens/__init__.py`
- `weakpoint/tui/screens/edit_screen.py`
- `weakpoint/tui/screens/present_screen.py`
- `tests/tui/__init__.py`
- `tests/tui/conftest.py`
- `tests/tui/fixtures/tiny.png` — 4×2 checkerboard fixture for image_ascii tests
- `tests/tui/test_models.py`
- `tests/tui/test_persistence.py`
- `tests/tui/test_image_ascii.py`
- `tests/tui/test_render.py`
- `tests/tui/test_commands.py`
- `tests/tui/test_app.py`

**Modified:**
- `pyproject.toml` — add `textual>=0.60` and `pillow>=10` runtime deps

---

## Task 1: Package scaffolding + dependencies

**Files:**
- Modify: `pyproject.toml`
- Create: `weakpoint/tui/__init__.py` (empty)
- Create: `weakpoint/tui/widgets/__init__.py` (empty)
- Create: `weakpoint/tui/screens/__init__.py` (empty)
- Create: `tests/tui/__init__.py` (empty)
- Test: `tests/tui/test_import.py`

- [ ] **Step 1: Write the failing smoke test**

`tests/tui/test_import.py`:

```python
"""Smoke test: the tui subpackage imports cleanly."""


def test_tui_package_imports():
    import weakpoint.tui  # noqa: F401
    import weakpoint.tui.widgets  # noqa: F401
    import weakpoint.tui.screens  # noqa: F401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/tui/test_import.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'weakpoint.tui'`

- [ ] **Step 3: Create the three empty `__init__.py` files and `tests/tui/__init__.py`**

Each is an empty file.

- [ ] **Step 4: Add deps to `pyproject.toml`**

Change the `dependencies` list from:

```toml
dependencies = [
    "PyQt6>=6.6",
]
```

to:

```toml
dependencies = [
    "PyQt6>=6.6",
    "textual>=0.60",
    "pillow>=10",
]
```

- [ ] **Step 5: Install the new deps into the active venv**

Run: `pip install -e .`
Expected: textual and pillow installed without error.

- [ ] **Step 6: Run the test to verify it passes**

Run: `pytest tests/tui/test_import.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml weakpoint/tui/ tests/tui/
git commit -m "Scaffold weakpoint.tui subpackage with textual and pillow deps"
```

---

## Task 2: Data model

**Files:**
- Create: `weakpoint/tui/models.py`
- Test: `tests/tui/test_models.py`

- [ ] **Step 1: Write the failing tests**

`tests/tui/test_models.py`:

```python
"""Tests for the pure data model in weakpoint.tui.models."""
from weakpoint.tui.models import (
    SLIDE_COLS,
    SLIDE_ROWS,
    Deck,
    Image,
    Slide,
    TextBox,
)


def test_slide_dimensions_are_100_by_30():
    assert SLIDE_COLS == 100
    assert SLIDE_ROWS == 30


def test_new_deck_has_one_empty_slide_selected():
    deck = Deck()
    assert len(deck.slides) == 1
    assert deck.current_index == 0
    assert deck.path is None


def test_new_slide_is_empty():
    slide = Slide()
    assert slide.title == ""
    assert slide.text_boxes == []
    assert slide.images == []


def test_text_box_defaults():
    box = TextBox(id="x", x=0, y=0, w=10, h=3)
    assert box.text == ""
    assert box.bold is False
    assert box.color == "default"
    assert box.align == "left"
    assert box.bullets is False
    assert box.numbered is False


def test_image_requires_path():
    img = Image(id="i", x=0, y=0, w=10, h=5, path="pic.png")
    assert img.path == "pic.png"


def test_slide_items_orders_images_before_text_boxes():
    slide = Slide()
    img = Image(id="i", x=0, y=0, w=5, h=5, path="p.png")
    box = TextBox(id="b", x=0, y=0, w=5, h=5)
    slide.images.append(img)
    slide.text_boxes.append(box)
    items = slide.items()
    assert items == [img, box]


def test_distinct_default_deck_slides_are_independent():
    d1 = Deck()
    d2 = Deck()
    d1.slides[0].text_boxes.append(TextBox(id="x", x=0, y=0, w=1, h=1))
    assert d2.slides[0].text_boxes == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/tui/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'weakpoint.tui.models'`.

- [ ] **Step 3: Write `weakpoint/tui/models.py`**

```python
"""Pure data model for the weakpoint terminal UI."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


SLIDE_COLS = 100
SLIDE_ROWS = 30

Color = str
Align = Literal["left", "center", "right"]


@dataclass
class TextBox:
    """A rectangular text region on a slide."""

    id: str
    x: int
    y: int
    w: int
    h: int
    text: str = ""
    bold: bool = False
    color: Color = "default"
    align: Align = "left"
    bullets: bool = False
    numbered: bool = False


@dataclass
class Image:
    """An image region on a slide; rendered as colored ASCII at draw time."""

    id: str
    x: int
    y: int
    w: int
    h: int
    path: str


@dataclass
class Slide:
    """One slide: optional title plus text boxes and images."""

    title: str = ""
    text_boxes: list[TextBox] = field(default_factory=list)
    images: list[Image] = field(default_factory=list)

    def items(self) -> list[TextBox | Image]:
        """Return items in draw order: images first (behind), text boxes second (in front)."""
        return [*self.images, *self.text_boxes]


@dataclass
class Deck:
    """The presentation: an ordered list of slides plus the current selection."""

    slides: list[Slide] = field(default_factory=lambda: [Slide()])
    current_index: int = 0
    path: str | None = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/tui/test_models.py -v`
Expected: all 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add weakpoint/tui/models.py tests/tui/test_models.py
git commit -m "Add weakpoint.tui data model"
```

---

## Task 3: Persistence (JSON load/save)

**Files:**
- Create: `weakpoint/tui/persistence.py`
- Test: `tests/tui/test_persistence.py`

- [ ] **Step 1: Write failing tests**

`tests/tui/test_persistence.py`:

```python
"""Tests for deck JSON persistence."""
import json
from pathlib import Path

import pytest

from weakpoint.tui.models import Deck, Image, Slide, TextBox
from weakpoint.tui.persistence import load_deck, save_deck


def _sample_deck() -> Deck:
    slide = Slide(
        title="Intro",
        text_boxes=[
            TextBox(
                id="box1",
                x=10,
                y=5,
                w=30,
                h=4,
                text="hello",
                bold=True,
                color="red",
                align="center",
                bullets=False,
                numbered=False,
            )
        ],
        images=[Image(id="img1", x=40, y=10, w=40, h=12, path="pics/cat.png")],
    )
    return Deck(slides=[slide, Slide(title="Two")], current_index=1)


def test_round_trip(tmp_path: Path):
    deck = _sample_deck()
    target = tmp_path / "deck.wpt.json"
    save_deck(deck, str(target))

    loaded = load_deck(str(target))

    assert loaded.current_index == deck.current_index
    assert [s.title for s in loaded.slides] == ["Intro", "Two"]
    box = loaded.slides[0].text_boxes[0]
    assert box.text == "hello"
    assert box.bold is True
    assert box.color == "red"
    assert box.align == "center"
    img = loaded.slides[0].images[0]
    assert img.path == "pics/cat.png"
    assert loaded.path == str(target)


def test_file_on_disk_has_version_1(tmp_path: Path):
    target = tmp_path / "d.wpt.json"
    save_deck(_sample_deck(), str(target))
    data = json.loads(target.read_text())
    assert data["version"] == 1


def test_unknown_version_rejected(tmp_path: Path):
    target = tmp_path / "d.wpt.json"
    target.write_text(json.dumps({"version": 99, "current_index": 0, "slides": []}))
    with pytest.raises(ValueError, match="version"):
        load_deck(str(target))


def test_malformed_json_rejected(tmp_path: Path):
    target = tmp_path / "d.wpt.json"
    target.write_text("{not json")
    with pytest.raises(ValueError, match="bad deck file"):
        load_deck(str(target))


def test_missing_file_raises_file_not_found(tmp_path: Path):
    target = tmp_path / "nope.wpt.json"
    with pytest.raises(FileNotFoundError):
        load_deck(str(target))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/tui/test_persistence.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Write `weakpoint/tui/persistence.py`**

```python
"""JSON save/load for decks. File format version 1."""
from __future__ import annotations

import json
from dataclasses import asdict

from weakpoint.tui.models import Deck, Image, Slide, TextBox


VERSION = 1


def save_deck(deck: Deck, path: str) -> None:
    """Serialize the deck to JSON and write it to ``path``.

    Sets ``deck.path`` on success so that subsequent ``:w`` calls without
    an argument target the same file.
    """
    payload = {
        "version": VERSION,
        "current_index": deck.current_index,
        "slides": [_slide_to_dict(s) for s in deck.slides],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    deck.path = path


def load_deck(path: str) -> Deck:
    """Read a deck JSON file at ``path`` and return a Deck.

    Raises FileNotFoundError if the file does not exist, ValueError for
    malformed JSON or unsupported version.
    """
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"bad deck file: {exc}") from exc

    version = data.get("version")
    if version != VERSION:
        raise ValueError(f"unsupported deck version: {version!r}")

    deck = Deck(
        slides=[_slide_from_dict(s) for s in data.get("slides", [])],
        current_index=int(data.get("current_index", 0)),
        path=path,
    )
    if not deck.slides:
        deck.slides = [Slide()]
    if not 0 <= deck.current_index < len(deck.slides):
        deck.current_index = 0
    return deck


def _slide_to_dict(slide: Slide) -> dict:
    return {
        "title": slide.title,
        "text_boxes": [asdict(b) for b in slide.text_boxes],
        "images": [asdict(i) for i in slide.images],
    }


def _slide_from_dict(data: dict) -> Slide:
    return Slide(
        title=data.get("title", ""),
        text_boxes=[TextBox(**b) for b in data.get("text_boxes", [])],
        images=[Image(**i) for i in data.get("images", [])],
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/tui/test_persistence.py -v`
Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add weakpoint/tui/persistence.py tests/tui/test_persistence.py
git commit -m "Add JSON deck persistence"
```

---

## Task 4: Image → ASCII conversion

**Files:**
- Create: `weakpoint/tui/image_ascii.py`
- Create: `tests/tui/fixtures/tiny.png` (generated by fixture script, then committed)
- Create: `tests/tui/conftest.py`
- Test: `tests/tui/test_image_ascii.py`

- [ ] **Step 1: Write conftest that creates the fixture on first run**

`tests/tui/conftest.py`:

```python
"""Shared fixtures for weakpoint.tui tests."""
from pathlib import Path

import pytest
from PIL import Image as PILImage


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def tiny_png(tmp_path_factory) -> str:
    """Generate a tiny 4x2 checkerboard PNG and return its absolute path."""
    path = FIXTURES_DIR / "tiny.png"
    if not path.exists():
        FIXTURES_DIR.mkdir(exist_ok=True)
        img = PILImage.new("RGB", (4, 2))
        img.putpixel((0, 0), (0, 0, 0))
        img.putpixel((1, 0), (255, 255, 255))
        img.putpixel((2, 0), (0, 0, 0))
        img.putpixel((3, 0), (255, 255, 255))
        img.putpixel((0, 1), (255, 255, 255))
        img.putpixel((1, 1), (0, 0, 0))
        img.putpixel((2, 1), (255, 255, 255))
        img.putpixel((3, 1), (0, 0, 0))
        img.save(path)
    return str(path)
```

- [ ] **Step 2: Write failing tests**

`tests/tui/test_image_ascii.py`:

```python
"""Tests for Pillow-backed image -> colored ASCII conversion."""
from pathlib import Path

from weakpoint.tui.image_ascii import RAMP, render


def test_render_returns_requested_dimensions(tiny_png: str):
    grid = render(tiny_png, cols=8, rows=4)
    assert len(grid) == 4
    for row in grid:
        assert len(row) == 8


def test_render_cells_are_char_and_hex_color(tiny_png: str):
    grid = render(tiny_png, cols=4, rows=2)
    for row in grid:
        for ch, color in row:
            assert isinstance(ch, str) and len(ch) == 1
            assert ch in RAMP
            assert color.startswith("#")
            assert len(color) == 7


def test_render_dark_pixel_maps_to_dark_char(tiny_png: str):
    # Upper-left pixel of tiny.png is (0,0,0) -> darkest char (space).
    grid = render(tiny_png, cols=4, rows=2)
    assert grid[0][0][0] == RAMP[0]


def test_render_bright_pixel_maps_to_bright_char(tiny_png: str):
    # Upper-right pixel of tiny.png is (255,255,255) -> brightest char '@'.
    grid = render(tiny_png, cols=4, rows=2)
    assert grid[0][3][0] == RAMP[-1]


def test_missing_file_returns_fallback_grid(tmp_path: Path):
    missing = str(tmp_path / "nope.png")
    grid = render(missing, cols=6, rows=3)
    assert len(grid) == 3
    assert len(grid[0]) == 6
    assert grid[0][0][0] == "?"
    # Everything else is blank space at default color.
    assert all(grid[0][c][0] == " " for c in range(1, 6))
    assert all(grid[r][c][0] == " " for r in range(1, 3) for c in range(6))


def test_cache_hit_does_not_reread_file(tiny_png: str, monkeypatch):
    from weakpoint.tui import image_ascii

    calls = {"n": 0}
    real_open = image_ascii.PILImage.open

    def spy_open(path):
        calls["n"] += 1
        return real_open(path)

    monkeypatch.setattr(image_ascii.PILImage, "open", spy_open)
    image_ascii.render.cache_clear()

    render(tiny_png, cols=4, rows=2)
    render(tiny_png, cols=4, rows=2)
    assert calls["n"] == 1
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/tui/test_image_ascii.py -v`
Expected: FAIL — module missing.

- [ ] **Step 4: Write `weakpoint/tui/image_ascii.py`**

```python
"""Image -> colored ASCII grid using Pillow."""
from __future__ import annotations

import os
from functools import lru_cache

from PIL import Image as PILImage
from PIL import UnidentifiedImageError


RAMP = " .:-=+*#%@"
FALLBACK_CHAR = "?"


def render(path: str, cols: int, rows: int) -> list[list[tuple[str, str]]]:
    """Render the image at ``path`` into a grid of (char, '#rrggbb') cells.

    On failure (missing file, unreadable format) returns a fallback grid
    with a single '?' at (0, 0) and spaces elsewhere.
    """
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return _fallback(cols, rows)
    try:
        return _render_cached(os.path.abspath(path), mtime, cols, rows)
    except (UnidentifiedImageError, OSError):
        return _fallback(cols, rows)


@lru_cache(maxsize=32)
def _render_cached(abs_path: str, mtime: float, cols: int, rows: int) -> list[list[tuple[str, str]]]:
    with PILImage.open(abs_path) as im:
        rgb = im.convert("RGB").resize((cols, rows), PILImage.Resampling.LANCZOS)
    pixels = rgb.load()
    grid: list[list[tuple[str, str]]] = []
    last = len(RAMP) - 1
    for y in range(rows):
        row: list[tuple[str, str]] = []
        for x in range(cols):
            r, g, b = pixels[x, y]
            luminance = 0.299 * r + 0.587 * g + 0.114 * b
            idx = int(luminance / 255 * last)
            row.append((RAMP[idx], f"#{r:02x}{g:02x}{b:02x}"))
        grid.append(row)
    return grid


def _fallback(cols: int, rows: int) -> list[list[tuple[str, str]]]:
    grid = [[(" ", "default") for _ in range(cols)] for _ in range(rows)]
    if rows > 0 and cols > 0:
        grid[0][0] = (FALLBACK_CHAR, "default")
    return grid


# Expose cache_clear on render for tests and app shutdown.
render.cache_clear = _render_cached.cache_clear  # type: ignore[attr-defined]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/tui/test_image_ascii.py -v`
Expected: 6 tests PASS. (The fixture PNG is generated on first run and committed in the next step.)

- [ ] **Step 6: Verify the fixture was created**

Run: `ls tests/tui/fixtures/`
Expected: `tiny.png` present.

- [ ] **Step 7: Commit**

```bash
git add weakpoint/tui/image_ascii.py tests/tui/conftest.py tests/tui/test_image_ascii.py tests/tui/fixtures/tiny.png
git commit -m "Add image-to-colored-ASCII conversion with LRU cache"
```

---

## Task 5: Render composer

**Files:**
- Create: `weakpoint/tui/render.py`
- Test: `tests/tui/test_render.py`

- [ ] **Step 1: Write failing tests**

`tests/tui/test_render.py`:

```python
"""Tests for the slide grid composer."""
from weakpoint.tui.models import SLIDE_COLS, SLIDE_ROWS, Image, Slide, TextBox
from weakpoint.tui.render import (
    blank_grid,
    compose_slide,
    compose_slide_small,
    grid_to_rich_text,
)


def _chars(grid, row):
    return "".join(cell[0] for cell in grid[row])


def test_blank_grid_is_spaces():
    grid = blank_grid(5, 2)
    assert len(grid) == 2
    assert len(grid[0]) == 5
    assert all(cell == (" ", "default") for row in grid for cell in row)


def test_compose_returns_canvas_of_slide_dimensions():
    grid = compose_slide(Slide(), selected_id=None, deck_dir=None)
    assert len(grid) == SLIDE_ROWS
    assert all(len(row) == SLIDE_COLS for row in grid)


def test_title_is_centered_on_row_zero():
    slide = Slide(title="Hi")
    grid = compose_slide(slide, selected_id=None, deck_dir=None)
    row = _chars(grid, 0)
    # "Hi" centered in 100 cols -> columns 49, 50.
    assert row[49:51] == "Hi"
    assert row[:49].strip() == ""
    assert row[51:].strip() == ""


def test_textbox_draws_rectangular_border():
    box = TextBox(id="b", x=2, y=2, w=6, h=3)
    slide = Slide(text_boxes=[box])
    grid = compose_slide(slide, selected_id=None, deck_dir=None)
    # Corners
    assert grid[2][2][0] == "+"
    assert grid[2][7][0] == "+"
    assert grid[4][2][0] == "+"
    assert grid[4][7][0] == "+"
    # Horizontal edges
    assert grid[2][3][0] == "-"
    assert grid[4][5][0] == "-"
    # Vertical edges
    assert grid[3][2][0] == "|"
    assert grid[3][7][0] == "|"


def test_textbox_text_renders_inside_border_with_left_align():
    box = TextBox(id="b", x=0, y=0, w=10, h=3, text="hello", align="left")
    slide = Slide(text_boxes=[box])
    grid = compose_slide(slide, selected_id=None, deck_dir=None)
    inside_row = _chars(grid, 1)
    assert inside_row.startswith("|hello")


def test_textbox_text_center_align():
    box = TextBox(id="b", x=0, y=0, w=10, h=3, text="hi", align="center")
    slide = Slide(text_boxes=[box])
    grid = compose_slide(slide, selected_id=None, deck_dir=None)
    # interior width = 8; "hi" centered -> 3 leading spaces.
    inside_row = _chars(grid, 1)
    assert inside_row[:10] == "|   hi   |"


def test_textbox_text_right_align():
    box = TextBox(id="b", x=0, y=0, w=10, h=3, text="hi", align="right")
    slide = Slide(text_boxes=[box])
    grid = compose_slide(slide, selected_id=None, deck_dir=None)
    inside_row = _chars(grid, 1)
    assert inside_row[:10] == "|      hi|"


def test_bullets_prefix_each_logical_line():
    box = TextBox(id="b", x=0, y=0, w=20, h=5, text="a\nb", bullets=True)
    slide = Slide(text_boxes=[box])
    grid = compose_slide(slide, selected_id=None, deck_dir=None)
    assert "• a" in _chars(grid, 1)
    assert "• b" in _chars(grid, 2)


def test_numbered_prefix_overrides_bullets():
    box = TextBox(
        id="b", x=0, y=0, w=20, h=5, text="one\ntwo", bullets=True, numbered=True
    )
    slide = Slide(text_boxes=[box])
    grid = compose_slide(slide, selected_id=None, deck_dir=None)
    assert "1. one" in _chars(grid, 1)
    assert "2. two" in _chars(grid, 2)


def test_selected_textbox_border_is_red():
    box = TextBox(id="b", x=1, y=1, w=5, h=3)
    slide = Slide(text_boxes=[box])
    grid = compose_slide(slide, selected_id="b", deck_dir=None)
    assert grid[1][1] == ("+", "red")
    assert grid[1][5] == ("+", "red")
    assert grid[3][1] == ("+", "red")
    assert grid[3][5] == ("+", "red")


def test_unselected_textbox_border_uses_box_color():
    box = TextBox(id="b", x=1, y=1, w=5, h=3, color="green")
    slide = Slide(text_boxes=[box])
    grid = compose_slide(slide, selected_id=None, deck_dir=None)
    assert grid[1][1][1] == "green"


def test_image_draws_via_image_ascii(monkeypatch):
    from weakpoint.tui import render as render_mod

    def fake(path, cols, rows):
        return [[("X", "#abcdef") for _ in range(cols)] for _ in range(rows)]

    monkeypatch.setattr(render_mod, "image_render", fake)

    img = Image(id="i", x=0, y=0, w=4, h=2, path="anything.png")
    slide = Slide(images=[img])
    grid = compose_slide(slide, selected_id=None, deck_dir=None)
    assert grid[0][0] == ("X", "#abcdef")
    assert grid[0][3] == ("X", "#abcdef")
    assert grid[1][2] == ("X", "#abcdef")


def test_image_path_resolved_against_deck_dir(monkeypatch, tmp_path):
    from weakpoint.tui import render as render_mod

    seen = {}

    def fake(path, cols, rows):
        seen["path"] = path
        return [[(" ", "default") for _ in range(cols)] for _ in range(rows)]

    monkeypatch.setattr(render_mod, "image_render", fake)

    img = Image(id="i", x=0, y=0, w=2, h=1, path="sub/pic.png")
    slide = Slide(images=[img])
    compose_slide(slide, selected_id=None, deck_dir=str(tmp_path))
    assert seen["path"] == str(tmp_path / "sub" / "pic.png")


def test_image_absolute_path_not_rejoined(monkeypatch, tmp_path):
    from weakpoint.tui import render as render_mod

    seen = {}

    def fake(path, cols, rows):
        seen["path"] = path
        return [[(" ", "default") for _ in range(cols)] for _ in range(rows)]

    monkeypatch.setattr(render_mod, "image_render", fake)

    abs_path = str(tmp_path / "pic.png")
    img = Image(id="i", x=0, y=0, w=2, h=1, path=abs_path)
    slide = Slide(images=[img])
    compose_slide(slide, selected_id=None, deck_dir="/some/other/dir")
    assert seen["path"] == abs_path


def test_compose_slide_small_scales_to_requested_size():
    slide = Slide()
    grid = compose_slide_small(slide, cols=20, rows=6)
    assert len(grid) == 6
    assert all(len(row) == 20 for row in grid)


def test_grid_to_rich_text_produces_single_text_with_newlines():
    from rich.text import Text

    grid = [[("a", "red"), ("b", "red")], [("c", "default"), ("d", "default")]]
    out = grid_to_rich_text(grid)
    assert isinstance(out, Text)
    assert out.plain == "ab\ncd"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/tui/test_render.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'weakpoint.tui.render'`.

- [ ] **Step 3: Write `weakpoint/tui/render.py`**

```python
"""Compose a Slide into a grid of (char, color) cells and render to Rich Text."""
from __future__ import annotations

import os
import textwrap

from rich.text import Text

from weakpoint.tui.image_ascii import render as image_render
from weakpoint.tui.models import (
    SLIDE_COLS,
    SLIDE_ROWS,
    Image,
    Slide,
    TextBox,
)


Cell = tuple[str, str]
Grid = list[list[Cell]]

DEFAULT = "default"
SELECTED_COLOR = "red"


def blank_grid(cols: int, rows: int) -> Grid:
    """Return a rows x cols grid of blank cells at the default color."""
    return [[(" ", DEFAULT) for _ in range(cols)] for _ in range(rows)]


def compose_slide(slide: Slide, selected_id: str | None, deck_dir: str | None) -> Grid:
    """Compose a full-size slide grid (SLIDE_COLS x SLIDE_ROWS)."""
    return _compose(slide, selected_id, deck_dir, SLIDE_COLS, SLIDE_ROWS, draw_title=True)


def compose_slide_small(slide: Slide, cols: int, rows: int) -> Grid:
    """Compose a scaled-down slide grid for the sidebar panel."""
    scale_x = cols / SLIDE_COLS
    scale_y = rows / SLIDE_ROWS
    grid = blank_grid(cols, rows)
    for item in slide.items():
        sx = int(item.x * scale_x)
        sy = int(item.y * scale_y)
        sw = max(1, int(item.w * scale_x))
        sh = max(1, int(item.h * scale_y))
        ex = min(cols - 1, sx + sw - 1)
        ey = min(rows - 1, sy + sh - 1)
        if ex <= sx or ey <= sy:
            continue
        color = getattr(item, "color", DEFAULT) if isinstance(item, TextBox) else DEFAULT
        for x in range(sx, ex + 1):
            grid[sy][x] = ("-", color)
            grid[ey][x] = ("-", color)
        for y in range(sy, ey + 1):
            grid[y][sx] = ("|", color)
            grid[y][ex] = ("|", color)
    return grid


def grid_to_rich_text(grid: Grid) -> Text:
    """Flatten a grid into a single Rich Text with per-run color styling."""
    out = Text()
    for r, row in enumerate(grid):
        if r > 0:
            out.append("\n")
        run_chars: list[str] = []
        run_color = row[0][1]
        for ch, color in row:
            if color != run_color:
                out.append("".join(run_chars), style=run_color if run_color != DEFAULT else "")
                run_chars = []
                run_color = color
            run_chars.append(ch)
        out.append("".join(run_chars), style=run_color if run_color != DEFAULT else "")
    return out


def _compose(
    slide: Slide,
    selected_id: str | None,
    deck_dir: str | None,
    cols: int,
    rows: int,
    *,
    draw_title: bool,
) -> Grid:
    grid = blank_grid(cols, rows)
    if draw_title and slide.title:
        _draw_title(grid, slide.title, cols)
    for img in slide.images:
        _draw_image(grid, img, deck_dir, selected=img.id == selected_id, cols=cols, rows=rows)
    for box in slide.text_boxes:
        _draw_textbox(grid, box, selected=box.id == selected_id, cols=cols, rows=rows)
    return grid


def _draw_title(grid: Grid, title: str, cols: int) -> None:
    text = title[:cols]
    start = max(0, (cols - len(text)) // 2)
    for i, ch in enumerate(text):
        grid[0][start + i] = (ch, DEFAULT)


def _draw_textbox(grid: Grid, box: TextBox, *, selected: bool, cols: int, rows: int) -> None:
    x1, y1 = box.x, box.y
    x2 = min(cols - 1, box.x + box.w - 1)
    y2 = min(rows - 1, box.y + box.h - 1)
    if x2 <= x1 or y2 <= y1:
        return
    border_color = SELECTED_COLOR if selected else box.color
    for x in range(x1, x2 + 1):
        grid[y1][x] = ("-", border_color)
        grid[y2][x] = ("-", border_color)
    for y in range(y1, y2 + 1):
        grid[y][x1] = ("|", border_color)
        grid[y][x2] = ("|", border_color)
    for cx, cy in ((x1, y1), (x2, y1), (x1, y2), (x2, y2)):
        grid[cy][cx] = ("+", border_color)

    inner_w = x2 - x1 - 1
    inner_h = y2 - y1 - 1
    if inner_w <= 0 or inner_h <= 0:
        return

    text_color = box.color
    lines_out = _layout_lines(box, inner_w)[:inner_h]
    for li, line in enumerate(lines_out):
        padded = _align(line, inner_w, box.align)
        for i, ch in enumerate(padded[:inner_w]):
            grid[y1 + 1 + li][x1 + 1 + i] = (ch, text_color)


def _layout_lines(box: TextBox, inner_w: int) -> list[str]:
    logical_lines = box.text.split("\n") if box.text else [""]
    out: list[str] = []
    for idx, logical in enumerate(logical_lines, start=1):
        if box.numbered:
            prefix = f"{idx}. "
        elif box.bullets:
            prefix = "• "
        else:
            prefix = ""
        avail = max(1, inner_w - len(prefix))
        wrapped = textwrap.wrap(logical, width=avail) or [""]
        for wi, piece in enumerate(wrapped):
            pad = prefix if wi == 0 else " " * len(prefix)
            out.append(pad + piece)
    return out


def _align(text: str, width: int, align: str) -> str:
    if len(text) >= width:
        return text[:width]
    if align == "center":
        left = (width - len(text)) // 2
        right = width - len(text) - left
        return " " * left + text + " " * right
    if align == "right":
        return " " * (width - len(text)) + text
    return text + " " * (width - len(text))


def _draw_image(
    grid: Grid,
    img: Image,
    deck_dir: str | None,
    *,
    selected: bool,
    cols: int,
    rows: int,
) -> None:
    x1, y1 = img.x, img.y
    x2 = min(cols - 1, img.x + img.w - 1)
    y2 = min(rows - 1, img.y + img.h - 1)
    if x2 < x1 or y2 < y1:
        return

    resolved = img.path
    if not os.path.isabs(resolved) and deck_dir:
        resolved = os.path.join(deck_dir, resolved)

    sub_cols = x2 - x1 + 1
    sub_rows = y2 - y1 + 1
    tiles = image_render(resolved, sub_cols, sub_rows)
    for r in range(sub_rows):
        for c in range(sub_cols):
            grid[y1 + r][x1 + c] = tiles[r][c]

    if selected:
        for x in range(x1, x2 + 1):
            grid[y1][x] = (grid[y1][x][0], SELECTED_COLOR)
            grid[y2][x] = (grid[y2][x][0], SELECTED_COLOR)
        for y in range(y1, y2 + 1):
            grid[y][x1] = (grid[y][x1][0], SELECTED_COLOR)
            grid[y][x2] = (grid[y][x2][0], SELECTED_COLOR)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/tui/test_render.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add weakpoint/tui/render.py tests/tui/test_render.py
git commit -m "Add slide grid composer and Rich Text conversion"
```

---

## Task 6: Commands — parsing

**Files:**
- Create: `weakpoint/tui/commands.py` (parser only at this step; dispatch added in Task 7)
- Test: `tests/tui/test_commands.py` (parser tests at this step)

- [ ] **Step 1: Write failing parser tests**

`tests/tui/test_commands.py`:

```python
"""Tests for the modal command parser and dispatcher."""
import pytest

from weakpoint.tui.commands import (
    AddBox,
    AddImage,
    Align,
    Bullets,
    ColorCmd,
    Numbered,
    Open,
    ParseError,
    Quit,
    Save,
    SaveQuit,
    SetTitle,
    parse,
)


def test_parse_box_with_text():
    cmd = parse("box 10 5 30 8 hello world")
    assert cmd == AddBox(x=10, y=5, w=30, h=8, text="hello world")


def test_parse_box_without_text():
    assert parse("box 0 0 5 3") == AddBox(x=0, y=0, w=5, h=3, text="")


def test_parse_box_bad_numbers():
    with pytest.raises(ParseError, match="box"):
        parse("box oops 1 2 3")


def test_parse_image():
    assert parse("image pics/cat.png") == AddImage(path="pics/cat.png")


def test_parse_title():
    assert parse("title My Deck") == SetTitle(title="My Deck")


def test_parse_title_empty_allowed():
    assert parse("title") == SetTitle(title="")


def test_parse_align_valid():
    assert parse("align center") == Align(value="center")


def test_parse_align_invalid():
    with pytest.raises(ParseError, match="align"):
        parse("align sideways")


def test_parse_color():
    assert parse("color red") == ColorCmd(value="red")
    assert parse("color #ff8800") == ColorCmd(value="#ff8800")


def test_parse_bullets_and_numbered():
    assert parse("bullets on") == Bullets(on=True)
    assert parse("bullets off") == Bullets(on=False)
    assert parse("numbered on") == Numbered(on=True)


def test_parse_bullets_bad_arg():
    with pytest.raises(ParseError):
        parse("bullets maybe")


def test_parse_write_no_arg():
    assert parse("w") == Save(path=None, force_quit=False)


def test_parse_write_with_arg():
    assert parse("w deck.json") == Save(path="deck.json", force_quit=False)


def test_parse_open():
    assert parse("o deck.json") == Open(path="deck.json", force=False)
    assert parse("o! deck.json") == Open(path="deck.json", force=True)


def test_parse_quit():
    assert parse("q") == Quit(force=False)
    assert parse("q!") == Quit(force=True)


def test_parse_write_quit():
    assert parse("wq") == SaveQuit(path=None)
    assert parse("wq deck.json") == SaveQuit(path="deck.json")


def test_parse_unknown_verb():
    with pytest.raises(ParseError, match="unknown"):
        parse("bogus")


def test_parse_empty_string():
    with pytest.raises(ParseError):
        parse("")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/tui/test_commands.py -v`
Expected: module missing, all tests FAIL.

- [ ] **Step 3: Write the parser portion of `weakpoint/tui/commands.py`**

```python
"""Modal commands: parser + dispatcher.

Parsing is pure and has no dependencies on the app. Dispatching takes an
AppState value object, mutates it, and returns a DispatchResult.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Union


class ParseError(ValueError):
    """Raised when a user-entered command string cannot be parsed."""


@dataclass(frozen=True)
class AddBox:
    x: int
    y: int
    w: int
    h: int
    text: str = ""


@dataclass(frozen=True)
class AddImage:
    path: str


@dataclass(frozen=True)
class SetTitle:
    title: str


@dataclass(frozen=True)
class Align:
    value: Literal["left", "center", "right"]


@dataclass(frozen=True)
class ColorCmd:
    value: str


@dataclass(frozen=True)
class Bullets:
    on: bool


@dataclass(frozen=True)
class Numbered:
    on: bool


@dataclass(frozen=True)
class Save:
    path: str | None
    force_quit: bool


@dataclass(frozen=True)
class SaveQuit:
    path: str | None


@dataclass(frozen=True)
class Open:
    path: str
    force: bool


@dataclass(frozen=True)
class Quit:
    force: bool


Command = Union[
    AddBox,
    AddImage,
    SetTitle,
    Align,
    ColorCmd,
    Bullets,
    Numbered,
    Save,
    SaveQuit,
    Open,
    Quit,
]


def parse(line: str) -> Command:
    """Parse a command string (without the leading ':') into a Command."""
    stripped = line.strip()
    if not stripped:
        raise ParseError("empty command")
    head, _, rest = stripped.partition(" ")
    rest = rest.strip()

    if head == "box":
        return _parse_box(rest)
    if head == "image":
        if not rest:
            raise ParseError("image requires a path")
        return AddImage(path=rest)
    if head == "title":
        return SetTitle(title=rest)
    if head == "align":
        if rest not in ("left", "center", "right"):
            raise ParseError(f"align: expected left|center|right, got {rest!r}")
        return Align(value=rest)  # type: ignore[arg-type]
    if head == "color":
        if not rest:
            raise ParseError("color requires a value")
        return ColorCmd(value=rest)
    if head == "bullets":
        return Bullets(on=_parse_on_off("bullets", rest))
    if head == "numbered":
        return Numbered(on=_parse_on_off("numbered", rest))
    if head == "w":
        return Save(path=rest or None, force_quit=False)
    if head == "wq":
        return SaveQuit(path=rest or None)
    if head == "o":
        if not rest:
            raise ParseError("o requires a path")
        return Open(path=rest, force=False)
    if head == "o!":
        if not rest:
            raise ParseError("o! requires a path")
        return Open(path=rest, force=True)
    if head == "q":
        return Quit(force=False)
    if head == "q!":
        return Quit(force=True)
    raise ParseError(f"unknown command: {head!r}")


def _parse_box(rest: str) -> AddBox:
    parts = rest.split(" ", 4)
    if len(parts) < 4:
        raise ParseError("box requires: box X Y W H [TEXT]")
    try:
        x, y, w, h = (int(parts[i]) for i in range(4))
    except ValueError as exc:
        raise ParseError(f"box: bad number ({exc})") from exc
    text = parts[4] if len(parts) == 5 else ""
    return AddBox(x=x, y=y, w=w, h=h, text=text)


def _parse_on_off(verb: str, arg: str) -> bool:
    if arg == "on":
        return True
    if arg == "off":
        return False
    raise ParseError(f"{verb}: expected on|off, got {arg!r}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/tui/test_commands.py -v`
Expected: all 17 parser tests PASS.

- [ ] **Step 5: Commit**

```bash
git add weakpoint/tui/commands.py tests/tui/test_commands.py
git commit -m "Add modal command parser"
```

---

## Task 7: Commands — dispatcher & app state

**Files:**
- Modify: `weakpoint/tui/commands.py` (append `AppState` + `dispatch`)
- Modify: `tests/tui/test_commands.py` (append dispatch tests)

- [ ] **Step 1: Append dispatch tests to `tests/tui/test_commands.py`**

```python
# --- dispatch tests ------------------------------------------------------

from pathlib import Path

from weakpoint.tui.commands import AppState, DispatchResult, dispatch
from weakpoint.tui.models import Deck, Image as ImgModel, Slide, TextBox


def _state(deck: Deck | None = None, selected_id: str | None = None) -> AppState:
    return AppState(deck=deck or Deck(), selected_id=selected_id, dirty=False, should_quit=False)


def test_dispatch_add_box_appends_to_current_slide():
    state = _state()
    res = dispatch(parse("box 0 0 5 3 hi"), state)
    assert isinstance(res, DispatchResult)
    slide = state.deck.slides[0]
    assert len(slide.text_boxes) == 1
    box = slide.text_boxes[0]
    assert (box.x, box.y, box.w, box.h, box.text) == (0, 0, 5, 3, "hi")
    assert state.selected_id == box.id
    assert state.dirty is True
    assert "box added" in res.message


def test_dispatch_add_box_out_of_bounds_is_rejected():
    state = _state()
    res = dispatch(parse("box 95 0 20 3"), state)
    assert state.deck.slides[0].text_boxes == []
    assert state.dirty is False
    assert "bounds" in res.message.lower()


def test_dispatch_add_image_places_default_sized_box_at_center():
    state = _state()
    dispatch(parse("image pics/cat.png"), state)
    images = state.deck.slides[0].images
    assert len(images) == 1
    img = images[0]
    # Default 40x12 centered in 100x30 -> (30, 9).
    assert (img.x, img.y, img.w, img.h) == (30, 9, 40, 12)
    assert img.path == "pics/cat.png"
    assert state.selected_id == img.id


def test_dispatch_set_title():
    state = _state()
    dispatch(parse("title My Deck"), state)
    assert state.deck.slides[0].title == "My Deck"
    assert state.dirty is True


def test_dispatch_align_requires_selected_textbox():
    state = _state()
    res = dispatch(parse("align center"), state)
    assert "select" in res.message.lower()
    assert state.dirty is False


def test_dispatch_align_mutates_selected_textbox():
    deck = Deck()
    box = TextBox(id="B", x=0, y=0, w=5, h=3)
    deck.slides[0].text_boxes.append(box)
    state = _state(deck, selected_id="B")
    dispatch(parse("align right"), state)
    assert box.align == "right"


def test_dispatch_color():
    deck = Deck()
    box = TextBox(id="B", x=0, y=0, w=5, h=3)
    deck.slides[0].text_boxes.append(box)
    state = _state(deck, selected_id="B")
    dispatch(parse("color #ff8800"), state)
    assert box.color == "#ff8800"


def test_dispatch_bullets_and_numbered():
    deck = Deck()
    box = TextBox(id="B", x=0, y=0, w=5, h=3)
    deck.slides[0].text_boxes.append(box)
    state = _state(deck, selected_id="B")
    dispatch(parse("bullets on"), state)
    assert box.bullets is True
    dispatch(parse("numbered on"), state)
    assert box.numbered is True


def test_dispatch_save_requires_path_when_deck_untitled(tmp_path):
    state = _state()
    res = dispatch(parse("w"), state)
    assert "path" in res.message.lower()
    assert not any(tmp_path.iterdir())


def test_dispatch_save_with_path_writes_file(tmp_path):
    state = _state()
    target = tmp_path / "d.wpt.json"
    dispatch(parse(f"w {target}"), state)
    assert target.exists()
    assert state.dirty is False
    assert state.deck.path == str(target)


def test_dispatch_save_reuses_deck_path(tmp_path):
    state = _state()
    target = tmp_path / "d.wpt.json"
    dispatch(parse(f"w {target}"), state)
    # Make dirty then save with no arg; should write to same file.
    dispatch(parse("title Hi"), state)
    assert state.dirty is True
    dispatch(parse("w"), state)
    assert state.dirty is False


def test_dispatch_open_loads_file(tmp_path):
    # Save a deck, then load it from a fresh state.
    state = _state()
    dispatch(parse("title Saved"), state)
    target = tmp_path / "d.wpt.json"
    dispatch(parse(f"w {target}"), state)

    fresh = _state()
    dispatch(parse(f"o {target}"), fresh)
    assert fresh.deck.slides[0].title == "Saved"
    assert fresh.deck.path == str(target)


def test_dispatch_open_refused_when_dirty(tmp_path):
    state = _state()
    dispatch(parse("title X"), state)  # dirty=True
    target = tmp_path / "d.wpt.json"
    Path(target).write_text('{"version":1,"current_index":0,"slides":[]}')
    res = dispatch(parse(f"o {target}"), state)
    assert "unsaved" in res.message.lower()
    assert state.deck.slides[0].title == "X"  # unchanged


def test_dispatch_open_force_discards_changes(tmp_path):
    state = _state()
    dispatch(parse("title X"), state)
    target = tmp_path / "d.wpt.json"
    Path(target).write_text(
        '{"version":1,"current_index":0,"slides":[{"title":"From File","text_boxes":[],"images":[]}]}'
    )
    dispatch(parse(f"o! {target}"), state)
    assert state.deck.slides[0].title == "From File"
    assert state.dirty is False


def test_dispatch_quit_refused_when_dirty():
    state = _state()
    dispatch(parse("title X"), state)
    res = dispatch(parse("q"), state)
    assert state.should_quit is False
    assert "unsaved" in res.message.lower()


def test_dispatch_quit_force():
    state = _state()
    dispatch(parse("title X"), state)
    dispatch(parse("q!"), state)
    assert state.should_quit is True


def test_dispatch_save_quit(tmp_path):
    state = _state()
    target = tmp_path / "d.wpt.json"
    dispatch(parse(f"wq {target}"), state)
    assert state.should_quit is True
    assert target.exists()
```

- [ ] **Step 2: Run the new tests — they must FAIL**

Run: `pytest tests/tui/test_commands.py -v`
Expected: new dispatch tests FAIL (imports missing); earlier parser tests still PASS.

- [ ] **Step 3: Append `AppState`, `DispatchResult`, and `dispatch` to `weakpoint/tui/commands.py`**

Append the following at the bottom of the file:

```python
# --- dispatcher ---------------------------------------------------------

import os
import uuid
from dataclasses import dataclass

from weakpoint.tui.models import (
    SLIDE_COLS,
    SLIDE_ROWS,
    Deck,
    Image as ImageModel,
    Slide,
    TextBox,
)
from weakpoint.tui.persistence import load_deck, save_deck


DEFAULT_IMAGE_W = 40
DEFAULT_IMAGE_H = 12


@dataclass
class AppState:
    """Mutable state the dispatcher operates on."""

    deck: Deck
    selected_id: str | None = None
    dirty: bool = False
    should_quit: bool = False


@dataclass
class DispatchResult:
    """Status message returned for display in the status bar."""

    message: str
    error: bool = False


def dispatch(cmd: Command, state: AppState) -> DispatchResult:
    """Apply ``cmd`` to ``state`` and return a status message."""
    try:
        return _dispatch(cmd, state)
    except Exception as exc:  # noqa: BLE001
        return DispatchResult(message=str(exc), error=True)


def _dispatch(cmd: Command, state: AppState) -> DispatchResult:
    if isinstance(cmd, AddBox):
        return _do_add_box(cmd, state)
    if isinstance(cmd, AddImage):
        return _do_add_image(cmd, state)
    if isinstance(cmd, SetTitle):
        _current(state).title = cmd.title
        state.dirty = True
        return DispatchResult(message="title set")
    if isinstance(cmd, Align):
        return _mutate_selected_box(state, lambda b: setattr(b, "align", cmd.value), "alignment set")
    if isinstance(cmd, ColorCmd):
        return _mutate_selected_box(state, lambda b: setattr(b, "color", cmd.value), "color set")
    if isinstance(cmd, Bullets):
        return _mutate_selected_box(state, lambda b: setattr(b, "bullets", cmd.on), "bullets set")
    if isinstance(cmd, Numbered):
        return _mutate_selected_box(state, lambda b: setattr(b, "numbered", cmd.on), "numbered set")
    if isinstance(cmd, Save):
        return _do_save(cmd.path, state)
    if isinstance(cmd, SaveQuit):
        res = _do_save(cmd.path, state)
        if not res.error:
            state.should_quit = True
        return res
    if isinstance(cmd, Open):
        return _do_open(cmd, state)
    if isinstance(cmd, Quit):
        if state.dirty and not cmd.force:
            return DispatchResult(message="unsaved changes — use :q! or :wq", error=True)
        state.should_quit = True
        return DispatchResult(message="bye")
    raise ValueError(f"unhandled command: {cmd!r}")


def _current(state: AppState) -> Slide:
    return state.deck.slides[state.deck.current_index]


def _new_id() -> str:
    return uuid.uuid4().hex


def _in_bounds(x: int, y: int, w: int, h: int) -> bool:
    return w > 0 and h > 0 and x >= 0 and y >= 0 and x + w <= SLIDE_COLS and y + h <= SLIDE_ROWS


def _do_add_box(cmd: AddBox, state: AppState) -> DispatchResult:
    if not _in_bounds(cmd.x, cmd.y, cmd.w, cmd.h):
        return DispatchResult(message="out of bounds", error=True)
    box = TextBox(id=_new_id(), x=cmd.x, y=cmd.y, w=cmd.w, h=cmd.h, text=cmd.text)
    _current(state).text_boxes.append(box)
    state.selected_id = box.id
    state.dirty = True
    return DispatchResult(message="box added")


def _do_add_image(cmd: AddImage, state: AppState) -> DispatchResult:
    x = (SLIDE_COLS - DEFAULT_IMAGE_W) // 2
    y = (SLIDE_ROWS - DEFAULT_IMAGE_H) // 2
    img = ImageModel(id=_new_id(), x=x, y=y, w=DEFAULT_IMAGE_W, h=DEFAULT_IMAGE_H, path=cmd.path)
    _current(state).images.append(img)
    state.selected_id = img.id
    state.dirty = True
    return DispatchResult(message=f"image added: {cmd.path}")


def _mutate_selected_box(state: AppState, fn, msg: str) -> DispatchResult:
    box = _selected_box(state)
    if box is None:
        return DispatchResult(message="select a text box first", error=True)
    fn(box)
    state.dirty = True
    return DispatchResult(message=msg)


def _selected_box(state: AppState) -> TextBox | None:
    if state.selected_id is None:
        return None
    for b in _current(state).text_boxes:
        if b.id == state.selected_id:
            return b
    return None


def _do_save(path: str | None, state: AppState) -> DispatchResult:
    target = path or state.deck.path
    if target is None:
        return DispatchResult(message="save: path required (deck is untitled)", error=True)
    save_deck(state.deck, target)
    state.dirty = False
    return DispatchResult(message=f"saved {os.path.basename(target)}")


def _do_open(cmd: Open, state: AppState) -> DispatchResult:
    if state.dirty and not cmd.force:
        return DispatchResult(message="unsaved changes — use :o! to discard", error=True)
    loaded = load_deck(cmd.path)
    state.deck = loaded
    state.selected_id = None
    state.dirty = False
    return DispatchResult(message=f"opened {os.path.basename(cmd.path)}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/tui/test_commands.py -v`
Expected: all parser + dispatch tests PASS.

- [ ] **Step 5: Commit**

```bash
git add weakpoint/tui/commands.py tests/tui/test_commands.py
git commit -m "Add modal command dispatcher with app state"
```

---

## Task 8: Widgets — SlideCanvas and StatusBar

**Files:**
- Create: `weakpoint/tui/widgets/slide_canvas.py`
- Create: `weakpoint/tui/widgets/status_bar.py`

(These widgets are thin wrappers around `render.py` / formatted strings; their behavior is tested end-to-end in Task 12. They have no unit tests of their own.)

- [ ] **Step 1: Write `weakpoint/tui/widgets/slide_canvas.py`**

```python
"""Textual widget that renders a single Slide as a Rich Text."""
from __future__ import annotations

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget

from weakpoint.tui.models import Slide
from weakpoint.tui.render import compose_slide, grid_to_rich_text


class SlideCanvas(Widget):
    """Render the active slide at full resolution (100x30 cells)."""

    slide: reactive[Slide | None] = reactive(None)
    selected_id: reactive[str | None] = reactive(None)
    deck_dir: reactive[str | None] = reactive(None)

    def render(self) -> Text:
        if self.slide is None:
            return Text("")
        grid = compose_slide(self.slide, self.selected_id, self.deck_dir)
        return grid_to_rich_text(grid)
```

- [ ] **Step 2: Write `weakpoint/tui/widgets/status_bar.py`**

```python
"""Bottom status bar: mode, slide counter, deck name, last message."""
from __future__ import annotations

from textual.reactive import reactive
from textual.widgets import Static


class StatusBar(Static):
    """One-line status bar. Updated via ``update_status``."""

    mode: reactive[str] = reactive("NORMAL")
    slide_i: reactive[int] = reactive(1)
    slide_n: reactive[int] = reactive(1)
    path: reactive[str | None] = reactive(None)
    dirty: reactive[bool] = reactive(False)
    message: reactive[str] = reactive("")
    error: reactive[bool] = reactive(False)

    def watch_mode(self) -> None:
        self._refresh()

    def watch_slide_i(self) -> None:
        self._refresh()

    def watch_slide_n(self) -> None:
        self._refresh()

    def watch_path(self) -> None:
        self._refresh()

    def watch_dirty(self) -> None:
        self._refresh()

    def watch_message(self) -> None:
        self._refresh()

    def watch_error(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        name = self.path if self.path else "untitled"
        marker = "*" if self.dirty else ""
        msg = f"  last: {self.message}" if self.message else ""
        style = "[red]" if self.error and self.message else ""
        end = "[/]" if style else ""
        self.update(
            f"{self.mode}  slide {self.slide_i}/{self.slide_n}  {name}{marker}{style}{msg}{end}"
        )
```

- [ ] **Step 3: Smoke-check the modules import**

Run: `python -c "from weakpoint.tui.widgets.slide_canvas import SlideCanvas; from weakpoint.tui.widgets.status_bar import StatusBar; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 4: Commit**

```bash
git add weakpoint/tui/widgets/slide_canvas.py weakpoint/tui/widgets/status_bar.py
git commit -m "Add SlideCanvas and StatusBar widgets"
```

---

## Task 9: Widgets — CommandBar and SlidePanel

**Files:**
- Create: `weakpoint/tui/widgets/command_bar.py`
- Create: `weakpoint/tui/widgets/slide_panel.py`

- [ ] **Step 1: Write `weakpoint/tui/widgets/command_bar.py`**

```python
"""Textual Input used as the `:`-prompt in COMMAND mode."""
from __future__ import annotations

from textual.widgets import Input


class CommandBar(Input):
    """Single-line input; hidden by default, shown when entering COMMAND mode."""

    DEFAULT_CSS = """
    CommandBar {
        display: none;
        height: 1;
    }
    CommandBar.-visible {
        display: block;
    }
    """

    def show(self, prefix: str = ":") -> None:
        """Show the bar, clear content, optionally leading with a prefix prompt."""
        self.add_class("-visible")
        self.value = ""
        self.placeholder = prefix
        self.focus()

    def hide(self) -> None:
        self.remove_class("-visible")
        self.value = ""
```

- [ ] **Step 2: Write `weakpoint/tui/widgets/slide_panel.py`**

```python
"""Sidebar: vertical list of slide mini-canvases."""
from __future__ import annotations

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget

from weakpoint.tui.models import Deck
from weakpoint.tui.render import compose_slide_small, grid_to_rich_text


MINI_COLS = 20
MINI_ROWS = 6


class SlidePanel(Widget):
    """Renders a list of mini-canvases, one per slide, with the current one marked."""

    deck: reactive[Deck | None] = reactive(None)

    def render(self) -> Text:
        if self.deck is None:
            return Text("")
        parts: list[Text] = []
        for i, slide in enumerate(self.deck.slides):
            marker = "▸" if i == self.deck.current_index else " "
            header = Text(f"{i + 1:>2} {marker}", style="bold" if i == self.deck.current_index else "")
            body = grid_to_rich_text(compose_slide_small(slide, MINI_COLS, MINI_ROWS))
            parts.append(header)
            parts.append(Text("\n"))
            parts.append(body)
            parts.append(Text("\n\n"))
        out = Text()
        for p in parts:
            out.append_text(p)
        return out
```

- [ ] **Step 3: Smoke-check imports**

Run: `python -c "from weakpoint.tui.widgets.command_bar import CommandBar; from weakpoint.tui.widgets.slide_panel import SlidePanel; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 4: Commit**

```bash
git add weakpoint/tui/widgets/command_bar.py weakpoint/tui/widgets/slide_panel.py
git commit -m "Add CommandBar and SlidePanel widgets"
```

---

## Task 10: Screens — EditScreen and PresentScreen

**Files:**
- Create: `weakpoint/tui/screens/edit_screen.py`
- Create: `weakpoint/tui/screens/present_screen.py`

- [ ] **Step 1: Write `weakpoint/tui/screens/edit_screen.py`**

```python
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
        width: 1fr;
    }
    StatusBar {
        height: 1;
        background: $boost;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="main"):
                yield SlidePanel(id="panel")
                yield SlideCanvas(id="canvas")
            yield StatusBar(id="status")
            yield CommandBar(id="cmd")
```

- [ ] **Step 2: Write `weakpoint/tui/screens/present_screen.py`**

```python
"""Fullscreen slide display with arrow-key navigation."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen

from weakpoint.tui.widgets.slide_canvas import SlideCanvas


class PresentScreen(Screen):
    """Show the current slide full-window; arrows to advance; q/Esc to exit."""

    BINDINGS = [
        Binding("right", "next", "next"),
        Binding("space", "next", "next"),
        Binding("left", "prev", "prev"),
        Binding("backspace", "prev", "prev"),
        Binding("q", "exit", "exit"),
        Binding("escape", "exit", "exit"),
    ]

    def compose(self) -> ComposeResult:
        yield SlideCanvas(id="canvas")

    def on_mount(self) -> None:
        self._refresh_canvas()

    def action_next(self) -> None:
        app = self.app
        deck = app.state.deck  # type: ignore[attr-defined]
        if deck.current_index + 1 < len(deck.slides):
            deck.current_index += 1
            self._refresh_canvas()

    def action_prev(self) -> None:
        app = self.app
        deck = app.state.deck  # type: ignore[attr-defined]
        if deck.current_index > 0:
            deck.current_index -= 1
            self._refresh_canvas()

    def action_exit(self) -> None:
        self.app.pop_screen()

    def _refresh_canvas(self) -> None:
        canvas = self.query_one("#canvas", SlideCanvas)
        deck = self.app.state.deck  # type: ignore[attr-defined]
        canvas.slide = deck.slides[deck.current_index]
        canvas.selected_id = None
        canvas.deck_dir = (
            None if deck.path is None else __import__("os").path.dirname(deck.path)
        )
```

- [ ] **Step 3: Smoke-check imports**

Run: `python -c "from weakpoint.tui.screens.edit_screen import EditScreen; from weakpoint.tui.screens.present_screen import PresentScreen; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 4: Commit**

```bash
git add weakpoint/tui/screens/edit_screen.py weakpoint/tui/screens/present_screen.py
git commit -m "Add EditScreen and PresentScreen"
```

---

## Task 11: App — wire everything together

**Files:**
- Create: `weakpoint/tui/app.py`
- Create: `weakpoint/tui/__main__.py`

- [ ] **Step 1: Write `weakpoint/tui/app.py`**

```python
"""Textual App that ties screens, widgets, and commands together."""
from __future__ import annotations

import os
import uuid

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
        super().__init__()
        deck = Deck()
        if initial_path:
            try:
                deck = load_deck(initial_path)
            except (FileNotFoundError, ValueError) as exc:
                self._boot_error = f"could not load {initial_path}: {exc}"
            else:
                self._boot_error = None
        else:
            self._boot_error = None
        self.state = AppState(deck=deck)

    def on_mount(self) -> None:
        self.push_screen(EditScreen())
        self._refresh_ui()
        if self._boot_error:
            self._set_status_message(self._boot_error, error=True)

    # --- action handlers -----------------------------------------------

    def action_enter_command(self) -> None:
        bar = self.query_one(CommandBar)
        bar.show(":")
        self._set_mode("COMMAND")

    def action_next_slide(self) -> None:
        deck = self.state.deck
        if deck.current_index + 1 < len(deck.slides):
            deck.current_index += 1
            self.state.selected_id = None
            self._refresh_ui()

    def action_prev_slide(self) -> None:
        deck = self.state.deck
        if deck.current_index > 0:
            deck.current_index -= 1
            self.state.selected_id = None
            self._refresh_ui()

    def action_append_slide(self) -> None:
        deck = self.state.deck
        deck.slides.insert(deck.current_index + 1, Slide())
        deck.current_index += 1
        self.state.selected_id = None
        self.state.dirty = True
        self._refresh_ui("slide added")

    def action_insert_slide_before(self) -> None:
        deck = self.state.deck
        deck.slides.insert(deck.current_index, Slide())
        self.state.selected_id = None
        self.state.dirty = True
        self._refresh_ui("slide inserted")

    def action_delete_slide(self) -> None:
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
        self.state.selected_id = None
        self._refresh_ui()

    def action_move_selected(self, key: str) -> None:
        item = self._selected_item()
        if item is None:
            return
        dx, dy = MOVE_DELTAS[key]
        item.x = max(0, min(SLIDE_COLS - item.w, item.x + dx))
        item.y = max(0, min(SLIDE_ROWS - item.h, item.y + dy))
        self.state.dirty = True
        self._refresh_ui()

    def action_resize_selected(self, key: str) -> None:
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
        item = self._selected_item()
        if not isinstance(item, TextBox):
            self._set_status_message("select a text box first", error=True)
            return
        item.bold = not item.bold
        self.state.dirty = True
        self._refresh_ui()

    def action_edit_text(self) -> None:
        item = self._selected_item()
        if not isinstance(item, TextBox):
            self._set_status_message("select a text box first", error=True)
            return
        bar = self.query_one(CommandBar)
        bar.show("text:")
        bar.value = item.text
        self._set_mode("INSERT")
        self._insert_target_id = item.id  # type: ignore[attr-defined]

    def action_present(self) -> None:
        self.push_screen(PresentScreen())

    def action_quit_cmd(self) -> None:
        if self.state.dirty:
            self._set_status_message("unsaved changes — use :q! or :wq", error=True)
            return
        self.exit()

    # --- command bar submission ----------------------------------------

    def on_input_submitted(self, event) -> None:  # noqa: ANN001
        bar = self.query_one(CommandBar)
        value = event.value
        mode = self.state_mode  # type: ignore[attr-defined]
        bar.hide()
        self._set_mode("NORMAL")
        if mode == "INSERT":
            target_id = getattr(self, "_insert_target_id", None)
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
        return self.state.deck.slides[self.state.deck.current_index]

    def _selected_item(self):
        if self.state.selected_id is None:
            return None
        slide = self._current_slide()
        for it in slide.items():
            if it.id == self.state.selected_id:
                return it
        return None

    def _set_mode(self, mode: str) -> None:
        self.state_mode = mode  # type: ignore[attr-defined]
        try:
            status = self.query_one(StatusBar)
        except Exception:  # widget not mounted yet
            return
        status.mode = mode

    def _set_status_message(self, msg: str, error: bool = False) -> None:
        try:
            status = self.query_one(StatusBar)
        except Exception:
            return
        status.message = msg
        status.error = error

    def _refresh_ui(self, message: str | None = None) -> None:
        deck = self.state.deck
        canvas = self.query_one(SlideCanvas)
        canvas.slide = deck.slides[deck.current_index]
        canvas.selected_id = self.state.selected_id
        canvas.deck_dir = None if deck.path is None else os.path.dirname(deck.path)

        panel = self.query_one(SlidePanel)
        panel.deck = deck
        panel.refresh()

        status = self.query_one(StatusBar)
        status.slide_i = deck.current_index + 1
        status.slide_n = len(deck.slides)
        status.path = deck.path
        status.dirty = self.state.dirty
        if message is not None:
            status.message = message
            status.error = False
```

- [ ] **Step 2: Write `weakpoint/tui/__main__.py`**

```python
"""CLI entry point: ``python -m weakpoint.tui [deck.json]``."""
from __future__ import annotations

import sys

from weakpoint.tui.app import WeakpointTuiApp


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else None
    WeakpointTuiApp(initial_path=path).run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Smoke-check import**

Run: `python -c "from weakpoint.tui.app import WeakpointTuiApp; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 4: Commit**

```bash
git add weakpoint/tui/app.py weakpoint/tui/__main__.py
git commit -m "Wire weakpoint.tui App and CLI entry point"
```

---

## Task 12: End-to-end pilot test

**Files:**
- Create: `tests/tui/test_app.py`

- [ ] **Step 1: Write the failing pilot test**

`tests/tui/test_app.py`:

```python
"""Smoke + end-to-end pilot tests for the Textual app."""
import json
from pathlib import Path

import pytest

from weakpoint.tui.app import WeakpointTuiApp


@pytest.mark.asyncio
async def test_app_boots_with_edit_screen():
    app = WeakpointTuiApp()
    async with app.run_test() as pilot:
        # EditScreen is active after mount.
        from weakpoint.tui.screens.edit_screen import EditScreen

        assert isinstance(pilot.app.screen, EditScreen)


@pytest.mark.asyncio
async def test_add_slide_then_add_box_then_save(tmp_path: Path):
    app = WeakpointTuiApp()
    target = tmp_path / "deck.wpt.json"
    async with app.run_test() as pilot:
        # Append a new slide (so deck has 2).
        await pilot.press("a")
        assert len(app.state.deck.slides) == 2

        # Open command bar and add a box on current slide.
        await pilot.press("colon")
        await pilot.press(*list("box 0 0 20 3 hello"))
        await pilot.press("enter")
        current = app.state.deck.slides[app.state.deck.current_index]
        assert len(current.text_boxes) == 1
        assert current.text_boxes[0].text == "hello"

        # Save to tmp path.
        await pilot.press("colon")
        await pilot.press(*list(f"w {target}"))
        await pilot.press("enter")

    assert target.exists()
    data = json.loads(target.read_text())
    assert data["version"] == 1
    assert len(data["slides"]) == 2
    assert any(b["text"] == "hello" for s in data["slides"] for b in s["text_boxes"])
```

- [ ] **Step 2: Add pytest-asyncio to dev deps if missing**

Check `pyproject.toml` `[project.optional-dependencies].dev` — if `pytest-asyncio` isn't listed, add it:

```toml
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.23",
]
```

And add `asyncio_mode = "auto"` to the pytest config:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

Then: `pip install -e ".[dev]"`.

- [ ] **Step 3: Run the pilot tests**

Run: `pytest tests/tui/test_app.py -v`
Expected: both tests PASS.

- [ ] **Step 4: Run the full test suite**

Run: `pytest -v`
Expected: all tui tests plus the pre-existing `tests/test_models.py` pass.

- [ ] **Step 5: Manual smoke — launch the app**

Run: `python -m weakpoint.tui`
Expected: the TUI opens with an empty slide and the status bar showing `NORMAL  slide 1/1  untitled`.
Press `:q`, then `Enter`. App exits cleanly.

- [ ] **Step 6: Commit**

```bash
git add tests/tui/test_app.py pyproject.toml
git commit -m "Add end-to-end pilot tests and pytest-asyncio config"
```

---

## Self-Review

**Spec coverage check (every spec section maps to a task):**

| Spec section | Implemented by |
|---|---|
| Package layout | Task 1 + directory creation across Tasks 2-11 |
| Data model | Task 2 |
| Rendering pipeline | Task 5 |
| Image → ASCII | Task 4 |
| Modal commands | Tasks 6 + 7 |
| Screens & UI layout | Task 10 |
| Persistence | Task 3 |
| Error handling | Task 7 (dispatch try/except), Task 4 (image fallback), Task 11 (boot error) |
| Testing strategy | Tasks 2-7, 12 |

**Placeholder scan:** no TBDs, no "similar to…", every code step contains the full code. ✓

**Type consistency:** `AppState.selected_id: str | None`, used in `AppState` (Task 7), `SlideCanvas.selected_id` (Task 8), `compose_slide(..., selected_id, ...)` (Task 5) — all match. `DispatchResult.message` (Task 7) accessed as `.message` everywhere. ✓

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-16-weakpoint-tui.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — I execute tasks in this session using executing-plans, batched with checkpoints for review.

Which approach?
