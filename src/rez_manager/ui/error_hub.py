"""Application-wide error reporting for QML-visible failures."""

from __future__ import annotations

from loguru import logger
from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtQml import (
    QmlAnonymous,
    QmlAttached,
    QmlElement,
    QmlSingleton,
    qmlAttachedPropertiesObject,
)

DEFAULT_ERROR_TARGET = "main"
GLOBAL_ERROR_TARGET = "global"
QML_IMPORT_NAME = "RezManager"
QML_IMPORT_MAJOR_VERSION = 1


@QmlAnonymous
class AppErrorHubAttached(QObject):
    """Attached QML metadata describing which host should surface UI errors."""

    errorTargetChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._error_target = ""

    @Property(str, notify=errorTargetChanged)
    def errorTarget(self) -> str:  # noqa: N802
        return self._error_target

    @errorTarget.setter
    def errorTarget(self, value: str) -> None:  # noqa: N802
        normalized = _normalize_target(value)
        if self._error_target != normalized:
            self._error_target = normalized
            self.errorTargetChanged.emit()


@QmlElement
@QmlAttached(AppErrorHubAttached)
class AppErrorTarget(QObject):
    """Attached-property host that declares which window owns expected UI errors."""

    @staticmethod
    def qmlAttachedProperties(cls, target: QObject) -> AppErrorHubAttached:  # noqa: N802
        return AppErrorHubAttached(target)


@QmlElement
@QmlSingleton
class AppErrorHub(QObject):
    """Shared front-end error state for expected and unexpected failures."""

    messageChanged = Signal()
    errorOccurred = Signal(str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._message = ""
        self._message_target = DEFAULT_ERROR_TARGET

    @Property(str, notify=messageChanged)
    def message(self) -> str:
        return self._message

    @Property(str, notify=messageChanged)
    def messageTarget(self) -> str:  # noqa: N802
        return self._message_target

    @Property(bool, notify=messageChanged)
    def hasError(self) -> bool:  # noqa: N802
        return bool(self._message)

    @Slot(str)
    def publish(self, message: str) -> None:
        self.publish_for_target(message, DEFAULT_ERROR_TARGET)

    @Slot(str, str)
    def publishForTarget(self, message: str, target: str) -> None:  # noqa: N802
        self.publish_for_target(message, target)

    def publish_for_target(self, message: str, target: str) -> None:
        normalized = str(message).strip()
        if not normalized:
            self.clear()
            return
        normalized_target = _normalize_target(target)
        logger.warning("UI-facing error [{}]: {}", normalized_target, normalized)
        self._publish_message(normalized, normalized_target)

    @Slot()
    def clear(self) -> None:
        self._set_message("", DEFAULT_ERROR_TARGET)

    @Slot(str)
    def publishUnexpected(self, details: str) -> None:  # noqa: N802
        self.publish_unexpected(details)

    def publish_unexpected(self, details: str, *, already_logged: bool = False) -> None:
        summary = str(details).strip().splitlines()[-1] if str(details).strip() else "Unknown error"
        if not already_logged:
            logger.error("Unexpected application error forwarded to UI: {}", summary)
        self._publish_message(
            f"Unexpected application error: {summary}",
            GLOBAL_ERROR_TARGET,
        )

    def _set_message(self, message: str, target: str) -> None:
        normalized_target = _normalize_target(target)
        if self._message != message or self._message_target != normalized_target:
            self._message = message
            self._message_target = normalized_target
            self.messageChanged.emit()

    def _publish_message(self, message: str, target: str) -> None:
        self._set_message(message, target)
        self.errorOccurred.emit(message, self._message_target)


app_error_hub = AppErrorHub()


def report_ui_error(message: str, *, target: str = DEFAULT_ERROR_TARGET) -> None:
    """Publish an application error intended for front-end display."""

    app_error_hub.publish_for_target(message, target)


def resolve_error_target(owner: QObject | None, *, default: str = DEFAULT_ERROR_TARGET) -> str:
    """Resolve a QML-declared error target from the object or its parent chain."""

    current = owner
    while current is not None:
        attached = qmlAttachedPropertiesObject(AppErrorTarget, current, False)
        if isinstance(attached, AppErrorHubAttached) and attached.errorTarget:
            return attached.errorTarget
        current = current.parent()
    return _normalize_target(default)


def report_object_ui_error(owner: QObject | None, message: str) -> None:
    """Publish an application error using the effective target for an object."""

    report_ui_error(message, target=resolve_error_target(owner))


def clear_ui_error() -> None:
    """Clear the current application error message."""

    app_error_hub.clear()


def report_unexpected_exception(details: str, *, already_logged: bool = False) -> None:
    """Publish an uncaught exception through the shared front-end error channel."""

    app_error_hub.publish_unexpected(details, already_logged=already_logged)


def _normalize_target(target: str) -> str:
    normalized = str(target).strip()
    return normalized or DEFAULT_ERROR_TARGET
