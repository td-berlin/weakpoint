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
