"""Smoke test: the tui subpackage imports cleanly."""


def test_tui_package_imports():
    import weakpoint  # noqa: F401
    import weakpoint.widgets  # noqa: F401
    import weakpoint.screens  # noqa: F401
