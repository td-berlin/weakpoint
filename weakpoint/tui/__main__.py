"""CLI entry point: ``python -m weakpoint.tui [deck.json]``."""
from __future__ import annotations

import sys

from weakpoint.tui.app import WeakpointTuiApp


def main() -> None:
    """Launch the app, optionally opening a deck file from argv[1]."""
    path = sys.argv[1] if len(sys.argv) > 1 else None
    WeakpointTuiApp(initial_path=path).run()


if __name__ == "__main__":
    main()
