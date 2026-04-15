"""Render a deck's state as ASCII art for terminal display on exit."""
from __future__ import annotations

from weakpoint.models import SLIDE_HEIGHT, SLIDE_WIDTH, Deck
from weakpoint.textbox import TextBoxItem


CANVAS_W = 80
CANVAS_H = 22


def _scale_x(x: float) -> int:
    """Scale a scene x-coordinate (0..960) to a canvas column (0..CANVAS_W-1)."""
    return max(0, min(CANVAS_W - 1, int(x / SLIDE_WIDTH * CANVAS_W)))


def _scale_y(y: float) -> int:
    """Scale a scene y-coordinate (0..540) to a canvas row (0..CANVAS_H-1)."""
    return max(0, min(CANVAS_H - 1, int(y / SLIDE_HEIGHT * CANVAS_H)))


def _draw_box(canvas: list[list[str]], item: TextBoxItem) -> None:
    """Stamp a text box's border and centered text onto the canvas grid."""
    rect = item.rect().translated(item.pos())
    x1 = _scale_x(rect.left())
    y1 = _scale_y(rect.top())
    x2 = _scale_x(rect.right())
    y2 = _scale_y(rect.bottom())
    if x2 <= x1 or y2 <= y1:
        return

    for x in range(x1, x2 + 1):
        canvas[y1][x] = "-"
        canvas[y2][x] = "-"
    for y in range(y1, y2 + 1):
        canvas[y][x1] = "|"
        canvas[y][x2] = "|"
    for cx, cy in ((x1, y1), (x2, y1), (x1, y2), (x2, y2)):
        canvas[cy][cx] = "+"

    inner_w = max(0, x2 - x1 - 1)
    if inner_w == 0:
        return
    text = item.text or ""
    if item.bold and text:
        text = f"**{text}**"
    text = text[:inner_w]
    tx = x1 + 1 + (inner_w - len(text)) // 2
    ty = (y1 + y2) // 2
    for i, ch in enumerate(text):
        canvas[ty][tx + i] = ch


def render_deck(deck: Deck) -> str:
    """Return a string containing an ASCII rendering of every slide in ``deck``."""
    out: list[str] = []
    out.append(f"=== Final state: {len(deck.slides)} slide(s) ===")
    for i, slide in enumerate(deck.slides):
        marker = " (current)" if i == deck.current_index else ""
        out.append(f"\nSlide {i + 1}{marker}  [{len(slide.text_boxes)} text box(es)]")
        out.append("+" + "-" * CANVAS_W + "+")
        canvas = [[" "] * CANVAS_W for _ in range(CANVAS_H)]
        for item in slide.text_boxes:
            _draw_box(canvas, item)
        for row in canvas:
            out.append("|" + "".join(row) + "|")
        out.append("+" + "-" * CANVAS_W + "+")
    return "\n".join(out)
