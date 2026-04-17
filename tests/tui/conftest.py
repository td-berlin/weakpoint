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
