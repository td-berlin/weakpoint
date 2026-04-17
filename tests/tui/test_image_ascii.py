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
