"""Shared pytest fixtures."""
import sys

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session", autouse=True)
def qapp() -> QApplication:
    """Provide a session-wide QApplication so QGraphicsScene can be constructed headlessly."""
    app = QApplication.instance() or QApplication(sys.argv)
    yield app
