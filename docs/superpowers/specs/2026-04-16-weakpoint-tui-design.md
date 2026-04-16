# WeakPoint TUI — Design

**Date:** 2026-04-16
**Status:** Proposed
**Scope:** A terminal-only PowerPoint clone, shipped as a subpackage `weakpoint.tui` inside the existing `weakpoint` repo. Independent of the existing PyQt6 GUI.

## Goals

- Edit a deck of slides entirely inside a terminal.
- Text boxes support bold, per-box color, alignment (left/center/right), and bullet/numbered lists.
- Each slide has an optional title rendered at the top.
- Images are supported by converting them to colored ASCII art at render time.
- Keyboard-first, vim-style modal editing.
- Save/load decks as JSON.
- Present mode: one slide fullscreen, arrow keys to advance.

## Non-goals (v1)

- Mouse interaction (may come later; nothing in the design precludes it).
- Rich-text runs inside a single text box — styling is per box, not per character.
- Speaker notes.
- Image formats beyond what Pillow reads (SVG excluded).
- Terminal resizing — slide geometry is fixed.
- Migrations: version bumps will be handled when they happen; none in v1.
- Reuse of the existing `weakpoint.models` module (Qt-bound, unusable here).

## Package layout

```
weakpoint/tui/
  __init__.py
  __main__.py          # python -m weakpoint.tui [deck.json]
  models.py            # Deck, Slide, TextBox, Image — pure data
  persistence.py       # load_deck / save_deck (JSON)
  image_ascii.py       # Pillow-based image → colored-ASCII grid
  render.py            # compose_slide(slide, selected_id) -> Grid; grid_to_rich_text
  commands.py          # parse + dispatch for modal commands
  app.py               # Textual App, key bindings
  widgets/
    __init__.py
    slide_canvas.py    # renders render.compose_slide via Rich Text
    slide_panel.py     # sidebar list of mini slide canvases
    command_bar.py     # ":" prompt
    status_bar.py      # mode + slide counter + last message
  screens/
    __init__.py
    edit_screen.py
    present_screen.py
```

**Boundary rule:** `models`, `persistence`, `image_ascii`, `render`, `commands` must not import Textual. Only `app`, `widgets/`, `screens/` do. This keeps the bulk of the code unit-testable without booting an app.

**Dependencies** added to `pyproject.toml`:
- `textual>=0.60`
- `pillow>=10`

Tests live under `tests/tui/` and share the existing pytest setup.

## Data model (`tui/models.py`)

Pure Python dataclasses. No framework types.

```python
SLIDE_COLS = 100
SLIDE_ROWS = 30

Color = str              # "default", a named color, or "#rrggbb"
Align = Literal["left", "center", "right"]

@dataclass
class TextBox:
    id: str              # uuid4 hex; stable across edits; used for selection
    x: int; y: int       # top-left in cells
    w: int; h: int
    text: str = ""       # "\n" separates lines
    bold: bool = False
    color: Color = "default"
    align: Align = "left"
    bullets: bool = False
    numbered: bool = False    # takes precedence over bullets

@dataclass
class Image:
    id: str
    x: int; y: int
    w: int; h: int
    path: str            # as typed by the user; resolved on render against deck dir

@dataclass
class Slide:
    title: str = ""
    text_boxes: list[TextBox] = field(default_factory=list)
    images: list[Image] = field(default_factory=list)

    def items(self) -> list[TextBox | Image]:
        """Z-order for selection cycling: images first (behind), then text boxes."""

@dataclass
class Deck:
    slides: list[Slide] = field(default_factory=lambda: [Slide()])
    current_index: int = 0
    path: str | None = None
```

Selection is an app-level concern, not a model field: `selected_id: str | None` lives on the Textual `App`.

## Rendering pipeline (`tui/render.py`)

Grid-based compositor. All output passes through `compose_slide`.

```python
Cell = tuple[str, str]   # (char, fg_color)   fg "default" = terminal default
Grid = list[list[Cell]]  # rows x cols

def compose_slide(slide: Slide, selected_id: str | None) -> Grid: ...
def compose_slide_small(slide: Slide, cols: int, rows: int) -> Grid: ...
def grid_to_rich_text(grid: Grid) -> rich.text.Text:
    """Collapse consecutive same-color cells into styled runs."""
```

**Draw rules**
- `draw_title`: centers `slide.title` on row 0, bold, default color.
- `draw_textbox`: paints the border (`+`, `-`, `|`) in the box's color; the border turns red when `selected`. Wraps `text` inside the `w-2 × h-2` interior; each visible line prefixed with `"• "` (bullets) or `"N. "` (numbered, `N` 1-based over the visible lines); `align` applied per line; `bold`/`color` applied to each char.
- `draw_image`: calls `image_ascii.render(path, w, h)` and stamps each `(char, rgb)` into the grid; red border overlay when selected.
- Items are clipped to `[0, SLIDE_COLS) × [0, SLIDE_ROWS)`.

**Commands that create items validate bounds and reject; commands that move/resize clamp.**

## Image → ASCII (`tui/image_ascii.py`)

```python
RAMP = " .:-=+*#%@"

def render(path: str, cols: int, rows: int) -> Grid:
    """One source pixel per output cell.
    LANCZOS resize to (cols, rows); for each cell compute luminance
    L = 0.299R + 0.587G + 0.114B, pick RAMP[int(L/255*(len-1))],
    color from source pixel as '#rrggbb'."""
```

- **Cache:** LRU keyed by `(abs_path, mtime, cols, rows)`, size 32. Cleared at process exit.
- **Errors:** `FileNotFoundError`, `UnidentifiedImageError`, `OSError` → fallback grid (a single `"?"` at `(0,0)`, rest blank) plus a status message. Anything else propagates.

## Modal commands (`tui/commands.py`)

Two modes: `NORMAL` (default) and `COMMAND` (entered via `:`). A third transient state, `INSERT`, is used only while the user types into a text box.

### NORMAL-mode keys

| Key | Action |
|---|---|
| `n` / `N` | next / prev slide |
| `a` | append new slide after current |
| `A` | insert new slide before current |
| `dd` | delete current slide (no-op if it's the only one) |
| `Tab` / `Shift+Tab` | cycle selection through items on current slide |
| `Esc` | deselect |
| `h` `j` `k` `l` | move selected item 1 cell (clamped) |
| `H` `J` `K` `L` | resize selected item (clamped) |
| `x` | delete selected item |
| `b` | toggle bold on selected text box |
| `i` | enter text-edit on selected box (single-line input; `Enter` commits, `Esc` cancels) |
| `p` | start present mode |
| `:` | enter COMMAND mode |
| `q` | quit (refused if dirty; tells user to use `:q!` or `:wq`) |

### COMMAND-mode verbs

```
box X Y W H [TEXT…]            add text box at X,Y sized WxH
image PATH                     add image, default 40x12 box at slide center
title TEXT…                    set current slide's title
align left|center|right        set alignment on selected text box
color NAME|#hex                set color on selected text box
bullets on|off
numbered on|off
w [PATH]                       save; first save requires PATH
o PATH                         open deck (refused if dirty)
o! PATH                        open deck, discard unsaved changes
q                              quit (refused if dirty)
q!                             quit, discard unsaved changes
wq [PATH]                      save and quit (PATH required if deck is untitled)
```

Parser is hand-rolled, returns a `Command` dataclass per verb. `dispatch(cmd, state)` is a pure function returning `DispatchResult(new_state, message)`. Easy to unit-test; no Textual dependencies.

Unknown verbs, bad args, out-of-bounds coords produce a red status message; no exception reaches the UI.

## Screens (`tui/screens/`)

### EditScreen

```
┌──────────────┬────────────────────────────────────────────────────────────┐
│ Slides       │                                                            │
│              │                                                            │
│ 1 ▸ [mini]   │            (100×30 SlideCanvas — the slide)                │
│ 2   [mini]   │                                                            │
│ 3   [mini]   │                                                            │
│ ...          │                                                            │
│              │                                                            │
├──────────────┴────────────────────────────────────────────────────────────┤
│ NORMAL  slide 2/5  untitled*                            last: box added   │
├───────────────────────────────────────────────────────────────────────────┤
│ :                                                                         │
└───────────────────────────────────────────────────────────────────────────┘
```

- Sidebar: `SlidePanel` — list of mini-canvases at 20×6 cells via `compose_slide_small`. Current slide highlighted.
- Center: `SlideCanvas` at fixed 100×30. Terminal bigger → letterbox; smaller → clip (bindings still work).
- StatusBar: `MODE  slide i/N  <path|untitled>[*]  last: <message>`. `*` indicates unsaved changes.
- CommandBar: hidden in NORMAL; shown and focused when `:` or `i` is pressed.

### PresentScreen

- One fullscreen `SlideCanvas`, no chrome, selection suppressed.
- `←` / `→` or `space` / `backspace` advance; `q` / `Esc` returns to EditScreen.

### App state (Textual `App`)

- `deck: Deck`
- `selected_id: str | None`
- `mode: Literal["normal", "command", "insert"]`
- `dirty: bool`

Key bindings defined at the App level; forwarded to the active screen.

## Persistence (`tui/persistence.py`)

JSON, one file per deck (`.wpt.json`). Images referenced by path.

```json
{
  "version": 1,
  "current_index": 0,
  "slides": [
    {
      "title": "Intro",
      "text_boxes": [
        {"id":"a1b2…","x":10,"y":5,"w":30,"h":4,"text":"hello",
         "bold":true,"color":"red","align":"center",
         "bullets":false,"numbered":false}
      ],
      "images": [
        {"id":"c3d4…","x":40,"y":10,"w":40,"h":12,"path":"pics/cat.png"}
      ]
    }
  ]
}
```

**Path resolution**
- `Image.path` stored verbatim (as the user typed).
- On load, resolved relative to the deck file's directory for `image_ascii.render`.
- On save, never rewritten.

**API**
```python
def save_deck(deck: Deck, path: str) -> None: ...
def load_deck(path: str) -> Deck: ...
```

Unknown `version` raises. Malformed JSON raises. The app catches both, shows a status message, and opens a fresh empty deck.

## Error handling

A user action never crashes the app.

- `commands.dispatch` is wrapped in `try/except Exception`; the message becomes the red status-bar text.
- `image_ascii.render` swallows `FileNotFoundError`, `UnidentifiedImageError`, `OSError`; returns fallback grid plus a status message. Other exceptions propagate (real bug).
- `persistence.load_deck` raises on bad input; the app catches and falls back to a fresh deck.
- No logging framework in v1. Tests assert on returned status strings, not log output.

**Unsaved-changes guard**
- `dirty` flag set on every mutating command.
- `q` and `:q` refuse when `dirty`; message suggests `:q!` or `:wq`.
- `:w` clears the flag.

## Testing (`tests/tui/`)

**Pure modules** (no Textual)
- `models` — default state, `items()` z-order.
- `commands` — parser round-trips per verb; dispatch mutates correctly and returns expected status; bad input returns errors, never raises.
- `persistence` — save → load round-trips equality; malformed JSON rejected; version mismatch rejected.
- `image_ascii` — tiny fixture PNG (checked into `tests/tui/fixtures/`) produces a grid of the requested size with non-empty chars; missing file returns fallback grid.
- `render.compose_slide` — golden tests on small synthetic slides assert grid shape and selection-highlight cells.

**Textual**
- Smoke test: `App.run_test()` pilot — boots, `EditScreen` visible, `SlideCanvas` present.
- End-to-end pilot: press `a`, `:box 0 0 20 3 hello`, `:w /tmp/x.wpt.json`; assert the file is written with the expected JSON.

**Not tested**: pixel-perfect rendering output; terminal resize (fixed geometry); PresentScreen navigation beyond smoke test.

**Entry points**
- `python -m weakpoint.tui` → blank deck, EditScreen.
- `python -m weakpoint.tui path.wpt.json` → opens that deck.
