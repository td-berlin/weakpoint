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


def test_grid_to_rich_text_handles_empty_row():
    from rich.text import Text
    grid = [[("a", "default")], [], [("b", "default")]]
    out = grid_to_rich_text(grid)
    assert isinstance(out, Text)
    assert out.plain == "a\n\nb"


def test_title_is_bold():
    slide = Slide(title="Hi")
    grid = compose_slide(slide, selected_id=None, deck_dir=None)
    # Title cells carry "bold" style.
    assert grid[0][49] == ("H", "bold")
    assert grid[0][50] == ("i", "bold")


def test_bold_textbox_border_and_text_carry_bold_style():
    box = TextBox(id="b", x=0, y=0, w=10, h=3, text="hello", bold=True, color="green")
    slide = Slide(text_boxes=[box])
    grid = compose_slide(slide, selected_id=None, deck_dir=None)
    # Border carries "bold green".
    assert grid[0][0] == ("+", "bold green")
    # Text inside carries "bold green".
    assert grid[1][1] == ("h", "bold green")


def test_bold_textbox_default_color_uses_bold_only():
    box = TextBox(id="b", x=0, y=0, w=10, h=3, text="hello", bold=True)
    slide = Slide(text_boxes=[box])
    grid = compose_slide(slide, selected_id=None, deck_dir=None)
    # color is "default" + bold -> just "bold"
    assert grid[0][0] == ("+", "bold")
    assert grid[1][1] == ("h", "bold")
