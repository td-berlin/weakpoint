"""Entry point: ``python -m weakpoint``."""
from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from weakpoint.app import MainWindow


def main() -> int:
    """Launch the GUI and return the exit code."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
