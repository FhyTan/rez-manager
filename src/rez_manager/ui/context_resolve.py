"""Shared background worker for resolving and optionally launching Rez contexts."""

from __future__ import annotations

from loguru import logger
from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from rez_manager.adapter.context import (
    ContextInfo,
    launch_context,
    load_context,
    resolve_context,
    save_context,
)
from rez_manager.exceptions import (
    RezContextLaunchError,
    RezContextLoadError,
    RezContextSaveError,
    RezResolveError,
)


class ContextResolveWorkerSignals(QObject):
    finished = Signal(int, object)


class ContextResolveWorker(QRunnable):
    """Resolve a Rez context with optional .rxt cache and launch.

    Parameters:
        request_id: Monotonic request counter used by the controller to
            discard stale results.
        package_requests: Raw package request strings (e.g. ``["maya-2024"]``).
        rxt_path: Path to a cached ``context.rxt`` file.  When provided the
            worker attempts to load it first and, after a fresh resolve,
            saves back to this path so that subsequent runs are fast.
        command: Launch command.  Only used when ``mode`` is ``"launch"``.
        mode: ``"resolve"`` (preview — no subprocess) or ``"launch"``.
    """

    def __init__(
        self,
        request_id: int,
        package_requests: list[str],
        *,
        rxt_path: str | None = None,
        command: str | None = None,
        mode: str = "resolve",
    ) -> None:
        super().__init__()
        self._request_id = request_id
        self._package_requests = list(package_requests)
        self._rxt_path = rxt_path
        self._command = command
        self._mode = mode
        self.signals = ContextResolveWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            context = self._resolve_with_cache()
        except RezResolveError as exc:
            self.signals.finished.emit(self._request_id, exc)
            return

        if self._mode == "launch":
            try:
                launch_context(context, self._command)
            except RezContextLaunchError as exc:
                self.signals.finished.emit(self._request_id, exc)
                return

        self.signals.finished.emit(self._request_id, context)

    def _resolve_with_cache(self) -> ContextInfo:
        if self._rxt_path:
            try:
                return load_context(self._rxt_path)
            except RezContextLoadError:
                logger.warning(
                    "Context resolve worker failed to load context. "
                    "Fallback to resolve package requests."
                )
                pass

        context = resolve_context(self._package_requests)

        if self._rxt_path:
            try:
                save_context(context, self._rxt_path)
            except RezContextSaveError:
                pass

        return context
