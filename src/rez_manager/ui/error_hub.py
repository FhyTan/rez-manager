"""Application-wide error reporting for QML-visible failures."""

from __future__ import annotations

from loguru import logger
from PySide6.QtCore import Property, QObject, Signal, Slot


class AppErrorHub(QObject):
    """Shared front-end error state for expected and unexpected failures."""

    messageChanged = Signal()
    errorOccurred = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._message = ""

    @Property(str, notify=messageChanged)
    def message(self) -> str:
        return self._message

    @Property(bool, notify=messageChanged)
    def hasError(self) -> bool:  # noqa: N802
        return bool(self._message)

    @Slot(str)
    def publish(self, message: str) -> None:
        normalized = str(message).strip()
        if not normalized:
            self.clear()
            return
        logger.warning("UI-facing error: {}", normalized)
        self._publish_message(normalized)

    @Slot()
    def clear(self) -> None:
        self._set_message("")

    @Slot(str)
    def publishUnexpected(self, details: str) -> None:  # noqa: N802
        self.publish_unexpected(details)

    def publish_unexpected(self, details: str, *, already_logged: bool = False) -> None:
        summary = str(details).strip().splitlines()[-1] if str(details).strip() else "Unknown error"
        if not already_logged:
            logger.error("Unexpected application error forwarded to UI: {}", summary)
        self._publish_message(f"Unexpected application error: {summary}")

    def _set_message(self, message: str) -> None:
        if self._message != message:
            self._message = message
            self.messageChanged.emit()

    def _publish_message(self, message: str) -> None:
        self._set_message(message)
        self.errorOccurred.emit(message)


app_error_hub = AppErrorHub()


def report_ui_error(message: str) -> None:
    """Publish an application error intended for front-end display."""

    app_error_hub.publish(message)


def clear_ui_error() -> None:
    """Clear the current application error message."""

    app_error_hub.clear()


def report_unexpected_exception(details: str, *, already_logged: bool = False) -> None:
    """Publish an uncaught exception through the shared front-end error channel."""

    app_error_hub.publish_unexpected(details, already_logged=already_logged)
