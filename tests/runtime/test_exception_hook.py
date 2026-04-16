"""Tests for runtime-level error reporting."""

from __future__ import annotations


def test_uncaught_hook_reports_unexpected_exceptions_to_app_error_hub():
    from rez_manager.exception_hook import qt_exception_hook
    from rez_manager.ui.error_hub import app_error_hub

    app_error_hub.clear()

    try:
        raise RuntimeError("boom")
    except RuntimeError as exc:
        qt_exception_hook.exception_hook(type(exc), exc, exc.__traceback__)

    assert app_error_hub.message == "Unexpected application error: RuntimeError: boom"
