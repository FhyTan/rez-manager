"""QML-facing controller for asynchronous Rez context launches."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from PySide6.QtCore import Property, QObject, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtQml import QmlElement

from rez_manager.adapter.context import launch_context
from rez_manager.exceptions import RezContextLaunchError
from rez_manager.models.launch_target import LAUNCH_TARGETS
from rez_manager.models.rez_context import RezContext
from rez_manager.models.settings import AppSettings
from rez_manager.ui.error_hub import clear_ui_error, report_ui_error

QML_IMPORT_NAME = "RezManager"
QML_IMPORT_MAJOR_VERSION = 1


@dataclass(slots=True)
class LaunchResult:
    """Result payload emitted by the background launch worker."""

    success: bool
    error: str | None = None


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
        self._active_workers: dict[int, _ContextLaunchWorker] = {}

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
            settings = AppSettings.load()
            command = LAUNCH_TARGETS.launch_command_for(
                context.meta.launch_target,
                context.meta.custom_command,
            )
        except (KeyError, OSError, TypeError, ValueError) as exc:
            self._clear_state()
            report_ui_error(str(exc))
            return False

        return self._launch_package_requests(
            request_id,
            project_name,
            context_name,
            context.packages,
            settings.package_repositories,
            command,
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
        try:
            settings = AppSettings.load()
        except (OSError, TypeError, ValueError) as exc:
            self._clear_state()
            report_ui_error(str(exc))
            return False

        normalized_requests = [str(request).strip() for request in package_requests]
        return self._launch_package_requests(
            request_id,
            project_name,
            context_name,
            normalized_requests,
            settings.package_repositories,
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

    def _start_launch_job(
        self,
        request_id: int,
        package_requests: list[str],
        package_paths: list[str],
        command: str | None,
    ) -> None:
        worker = _ContextLaunchWorker(
            request_id,
            list(package_requests),
            list(package_paths),
            command,
        )
        worker.signals.finished.connect(self._apply_launch_result)
        self._active_workers[request_id] = worker
        self._thread_pool.start(worker)

    def _launch_package_requests(
        self,
        request_id: int,
        project_name: str,
        context_name: str,
        package_requests: Sequence[str],
        package_paths: Sequence[str],
        command: str | None,
    ) -> bool:
        self._project_name = project_name
        self._context_name = context_name
        self._is_launching = True
        self.stateChanged.emit()
        clear_ui_error()
        self._start_launch_job(
            request_id,
            list(package_requests),
            list(package_paths),
            command,
        )
        return True

    @Slot(int, object)
    def _apply_launch_result(self, request_id: int, launch_result: object) -> None:
        self._active_workers.pop(request_id, None)
        if request_id != self._request_id:
            return

        self._is_launching = False
        self.stateChanged.emit()
        if not isinstance(launch_result, LaunchResult):
            report_ui_error("Failed to launch context.")
            return

        if not launch_result.success:
            report_ui_error(launch_result.error or "Failed to launch context.")
            return

        clear_ui_error()
        self.launchSucceeded.emit(self._project_name, self._context_name)


class _ContextLaunchWorkerSignals(QObject):
    finished = Signal(int, object)


class _ContextLaunchWorker(QRunnable):
    def __init__(
        self,
        request_id: int,
        package_requests: list[str],
        package_paths: list[str],
        command: str | None,
    ) -> None:
        super().__init__()
        self._request_id = request_id
        self._package_requests = package_requests
        self._package_paths = package_paths
        self._command = command
        self.signals = _ContextLaunchWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            launch_context(
                self._package_requests,
                self._command,
                package_paths=self._package_paths,
            )
        except RezContextLaunchError as exc:
            self.signals.finished.emit(
                self._request_id,
                LaunchResult(success=False, error=str(exc)),
            )
            return

        self.signals.finished.emit(self._request_id, LaunchResult(success=True))
