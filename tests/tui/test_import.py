"""Smoke test: the tui subpackage imports cleanly."""


def test_tui_package_imports():
    import weakpoint.tui  # noqa: F401
    import weakpoint.tui.widgets  # noqa: F401
    import weakpoint.tui.screens  # noqa: F401
