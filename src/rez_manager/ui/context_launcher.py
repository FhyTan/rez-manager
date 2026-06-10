"""QML-facing controller for asynchronous Rez context launches."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import Property, QObject, QThreadPool, Signal, Slot
from PySide6.QtQml import QmlElement

from rez_manager.adapter.context import ContextInfo
from rez_manager.exceptions import RezAdapterError
from rez_manager.models.launch_target import LAUNCH_TARGETS
from rez_manager.models.rez_context import RezContext
from rez_manager.persistence.filesystem import CONTEXT_FILE_NAME
from rez_manager.ui.context_resolve import ContextResolveWorker
from rez_manager.ui.error_hub import clear_ui_error, report_object_ui_error

QML_IMPORT_NAME = "RezManager"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class ContextLauncherController(QObject):
    """Launch a saved Rez context on a worker thread."""

    stateChanged = Signal()
    launchSucceeded = Signal(str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._project_name = ""
        self._context_name = ""
        self._is_launching = False
        self._request_id = 0
        self._thread_pool = QThreadPool.globalInstance()
        self._active_workers: dict[int, ContextResolveWorker] = {}

    @Property(str, notify=stateChanged)
    def projectName(self) -> str:  # noqa: N802
        return self._project_name

    @Property(str, notify=stateChanged)
    def contextName(self) -> str:  # noqa: N802
        return self._context_name

    @Property(bool, notify=stateChanged)
    def isLaunching(self) -> bool:  # noqa: N802
        return self._is_launching

    @Slot(str, str, result=bool)
    def launchContext(self, project_name: str, context_name: str) -> bool:  # noqa: N802
        self._request_id += 1
        request_id = self._request_id

        try:
            context = RezContext.load(project_name, context_name)
            command = LAUNCH_TARGETS.launch_command_for(
                context.meta.launch_target,
                context.meta.custom_command,
            )
        except (KeyError, OSError, TypeError, ValueError) as exc:
            self._clear_state()
            report_object_ui_error(self, str(exc))
            return False

        rxt_path = str(Path(context.path) / CONTEXT_FILE_NAME)

        return self._launch(
            request_id,
            project_name,
            context_name,
            context.packages,
            command,
            rxt_path=rxt_path,
        )

    @Slot(str, str, "QVariantList", result=bool)
    def launchPackageRequests(  # noqa: N802
        self,
        project_name: str,
        context_name: str,
        package_requests: Sequence[str],
    ) -> bool:
        self._request_id += 1
        request_id = self._request_id

        normalized_requests = [str(request).strip() for request in package_requests]
        return self._launch(
            request_id,
            project_name,
            context_name,
            normalized_requests,
            None,
        )

    @Slot()
    def clear(self) -> None:
        self._request_id += 1
        self._clear_state()
        clear_ui_error()

    def _clear_state(self) -> None:
        self._project_name = ""
        self._context_name = ""
        self._is_launching = False
        self.stateChanged.emit()

    def _start_resolve_job(
        self,
        request_id: int,
        package_requests: list[str],
        command: str | None,
        *,
        rxt_path: str | None = None,
    ) -> None:
        worker = ContextResolveWorker(
            request_id,
            list(package_requests),
            rxt_path=rxt_path,
            command=command,
            mode="launch",
        )
        worker.signals.finished.connect(self._apply_launch_result)
        self._active_workers[request_id] = worker
        self._thread_pool.start(worker)

    def _launch(
        self,
        request_id: int,
        project_name: str,
        context_name: str,
        package_requests: Sequence[str],
        command: str | None,
        *,
        rxt_path: str | None = None,
    ) -> bool:
        self._project_name = project_name
        self._context_name = context_name
        self._is_launching = True
        self.stateChanged.emit()
        clear_ui_error()
        self._start_resolve_job(
            request_id,
            list(package_requests),
            command,
            rxt_path=rxt_path,
        )
        return True

    @Slot(int, object)
    def _apply_launch_result(self, request_id: int, resolve_result: object) -> None:
        self._active_workers.pop(request_id, None)
        if request_id != self._request_id:
            return

        self._is_launching = False
        self.stateChanged.emit()
        if isinstance(resolve_result, ContextInfo):
            clear_ui_error()
            self.launchSucceeded.emit(self._project_name, self._context_name)
            return

        if isinstance(resolve_result, RezAdapterError):
            report_object_ui_error(self, str(resolve_result))
        else:
            report_object_ui_error(self, "Failed to launch context.")
