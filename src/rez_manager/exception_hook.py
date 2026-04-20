from __future__ import annotations

import sys
import traceback
from types import TracebackType

from loguru import logger
from PySide6.QtCore import QObject, Signal

from rez_manager.ui.error_hub import report_unexpected_exception


class UncaughtHook(QObject):
    _exception_caught = Signal(str)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        sys.excepthook = self.exception_hook

        self._exception_caught.connect(
            lambda details: report_unexpected_exception(details, already_logged=True)
        )

    def exception_hook(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        """Handle uncaught exceptions raised by the application."""

        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        log_msg = "\n".join(
            [
                "".join(traceback.format_tb(exc_traceback)),
                f"{exc_type.__name__}: {exc_value}",
            ]
        )
        logger.critical("Uncaught exception:\n{}", log_msg)
        self._exception_caught.emit(log_msg)


qt_exception_hook = UncaughtHook()
