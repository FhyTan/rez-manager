"""Tests for application logging configuration and error severity routing."""

from __future__ import annotations


def test_configure_logging_writes_to_override_log_directory(tmp_path, monkeypatch):
    from loguru import logger

    from rez_manager.logging_config import configure_logging

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))

    log_path = configure_logging()
    logger.warning("test log message")

    assert log_path == tmp_path / "logs" / "rez-manager.log"
    assert log_path.exists()
    assert "test log message" in log_path.read_text(encoding="utf-8")


def test_error_hub_logs_warning_for_expected_errors_and_error_for_unexpected(monkeypatch):
    import rez_manager.ui.error_hub as error_hub

    events: list[tuple[str, str]] = []
    emitted: list[tuple[str, str]] = []

    class StubLogger:
        def warning(self, message: str, *args: object) -> None:
            events.append(("warning", message.format(*args)))

        def error(self, message: str, *args: object) -> None:
            events.append(("error", message.format(*args)))

    def capture(message: str, target: str) -> None:
        emitted.append((message, target))

    monkeypatch.setattr(error_hub, "logger", StubLogger())
    error_hub.app_error_hub.clear()
    error_hub.app_error_hub.errorOccurred.connect(capture)

    error_hub.report_ui_error("Package name is required.")
    error_hub.report_unexpected_exception("RuntimeError: boom")

    assert events == [
        ("warning", "UI-facing error [main]: Package name is required."),
        ("error", "Unexpected application error forwarded to UI: RuntimeError: boom"),
    ]
    assert emitted == [
        ("Package name is required.", "main"),
        ("Unexpected application error: RuntimeError: boom", "global"),
    ]
    assert error_hub.app_error_hub.message == "Unexpected application error: RuntimeError: boom"
    assert error_hub.app_error_hub.messageTarget == "global"
    error_hub.app_error_hub.errorOccurred.disconnect(capture)


def test_error_hub_skips_duplicate_error_log_when_exception_is_already_logged(monkeypatch):
    import rez_manager.ui.error_hub as error_hub

    events: list[tuple[str, str]] = []

    class StubLogger:
        def warning(self, message: str, *args: object) -> None:
            events.append(("warning", message.format(*args)))

        def error(self, message: str, *args: object) -> None:
            events.append(("error", message.format(*args)))

    monkeypatch.setattr(error_hub, "logger", StubLogger())
    error_hub.app_error_hub.clear()

    error_hub.report_unexpected_exception("RuntimeError: boom", already_logged=True)

    assert events == []
    assert error_hub.app_error_hub.message == "Unexpected application error: RuntimeError: boom"
    assert error_hub.app_error_hub.messageTarget == "global"


def test_error_hub_supports_targeted_messages(monkeypatch):
    import rez_manager.ui.error_hub as error_hub

    events: list[tuple[str, str]] = []

    class StubLogger:
        def warning(self, message: str, *args: object) -> None:
            events.append(("warning", message.format(*args)))

        def error(self, message: str, *args: object) -> None:
            events.append(("error", message.format(*args)))

    monkeypatch.setattr(error_hub, "logger", StubLogger())
    error_hub.app_error_hub.clear()

    error_hub.report_ui_error("Repository refresh failed.", target="package-manager")

    assert events == [("warning", "UI-facing error [package-manager]: Repository refresh failed.")]
    assert error_hub.app_error_hub.message == "Repository refresh failed."
    assert error_hub.app_error_hub.messageTarget == "package-manager"


def test_error_hub_resolves_attached_target_from_parent_chain(monkeypatch):
    from PySide6.QtCore import QObject

    import rez_manager.ui.error_hub as error_hub

    parent = QObject()
    child = QObject(parent)
    attached_objects: dict[int, error_hub.AppErrorHubAttached] = {}

    monkeypatch.setattr(
        error_hub,
        "qmlAttachedPropertiesObject",
        lambda cls, obj, create: attached_objects.setdefault(
            id(obj),
            error_hub.AppErrorHubAttached(obj),
        )
        if obj is parent
        else None,
    )

    attached = error_hub.qmlAttachedPropertiesObject(error_hub.AppErrorTarget, parent, False)
    attached.errorTarget = "package-manager"

    assert error_hub.resolve_error_target(child) == "package-manager"


def test_error_hub_falls_back_to_main_without_attached_target(monkeypatch):
    from PySide6.QtCore import QObject

    import rez_manager.ui.error_hub as error_hub

    monkeypatch.setattr(error_hub, "qmlAttachedPropertiesObject", lambda cls, obj, create: None)

    assert error_hub.resolve_error_target(QObject()) == "main"
