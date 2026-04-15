"""Entry point: ``python -m weakpoint``."""
from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from weakpoint.app import MainWindow
from weakpoint.ascii_view import render_deck


def main() -> int:
    """Launch the GUI and print the final deck state as ASCII on exit."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    exit_code = app.exec()
    print(render_deck(window._deck))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
