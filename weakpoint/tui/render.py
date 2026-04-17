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
    """Build the character grid for a slide at the given dimensions."""
    grid = blank_grid(cols, rows)
    if draw_title and slide.title:
        _draw_title(grid, slide.title, cols)
    for img in slide.images:
        _draw_image(grid, img, deck_dir, selected=img.id == selected_id, cols=cols, rows=rows)
    for box in slide.text_boxes:
        _draw_textbox(grid, box, selected=box.id == selected_id, cols=cols, rows=rows)
    return grid


def _draw_title(grid: Grid, title: str, cols: int) -> None:
    """Write the slide title centered on row 0."""
    text = title[:cols]
    start = max(0, (cols - len(text)) // 2)
    for i, ch in enumerate(text):
        grid[0][start + i] = (ch, DEFAULT)


def _draw_textbox(grid: Grid, box: TextBox, *, selected: bool, cols: int, rows: int) -> None:
    """Draw a TextBox border and its text content onto the grid."""
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
    """Expand box text into display lines, applying bullet/number prefixes and wrapping."""
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
    """Pad or truncate text to exactly width characters using the given alignment."""
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
    """Render an image into the grid, resolving its path relative to deck_dir if needed."""
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
