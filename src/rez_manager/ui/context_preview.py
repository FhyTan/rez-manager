"""QML-facing controller for resolved context preview data."""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QAbstractTableModel,
    QByteArray,
    QModelIndex,
    QObject,
    QRunnable,
    Qt,
    QThreadPool,
    Signal,
    Slot,
)
from PySide6.QtQml import QmlElement

from rez_manager.adapter.context import EnvironmentSection, ResolveResult, resolve_context
from rez_manager.models.rez_context import RezContext
from rez_manager.models.settings import AppSettings
from rez_manager.ui.error_hub import clear_ui_error, report_ui_error

QML_IMPORT_NAME = "RezManager"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class ContextPreviewController(QObject):
    stateChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._project_name = ""
        self._context_name = ""
        self._is_loading = False
        self._result: ResolveResult | None = None
        self._environment_sections: list[dict[str, object]] = []
        self._environment_models: list[EnvironmentsTableModel] = []
        self._request_id = 0
        self._thread_pool = QThreadPool.globalInstance()
        self._active_workers: dict[int, _ContextPreviewWorker] = {}

    @Property(str, notify=stateChanged)
    def projectName(self) -> str:  # noqa: N802
        return self._project_name

    @Property(str, notify=stateChanged)
    def contextName(self) -> str:  # noqa: N802
        return self._context_name

    @Property(bool, notify=stateChanged)
    def hasData(self) -> bool:  # noqa: N802
        if self._result is None:
            return False
        return bool(self._result.environ_sections or self._result.packages)

    @Property(bool, notify=stateChanged)
    def isLoading(self) -> bool:  # noqa: N802
        return self._is_loading

    @Property(str, constant=True)
    def pathSeparator(self) -> str:  # noqa: N802
        from os import pathsep  # noqa: PLC0415

        return pathsep

    @Property("QVariantList", notify=stateChanged)
    def environmentSections(self) -> list[dict[str, object]]:  # noqa: N802
        return list(self._environment_sections)

    @Property("QVariantList", notify=stateChanged)
    def resolvedPackages(self) -> list[dict[str, str]]:  # noqa: N802
        if self._result is None:
            return []
        return [_package_entry(label) for label in self._result.packages]

    @Property("QVariantList", notify=stateChanged)
    def tools(self) -> list[str]:
        if self._result is None:
            return []
        return list(self._result.tools)

    @Slot(str, str, result=bool)
    def loadContext(self, project_name: str, context_name: str) -> bool:  # noqa: N802
        self._request_id += 1
        request_id = self._request_id
        try:
            context = RezContext.load(project_name, context_name)
            settings = AppSettings.load()
        except (KeyError, OSError, TypeError, ValueError) as exc:
            self._clear_state()
            report_ui_error(str(exc))
            return False

        self._project_name = project_name
        self._context_name = context_name
        self._result = None
        self._is_loading = True
        self.stateChanged.emit()
        clear_ui_error()
        self._start_preview_job(request_id, context.packages, settings.package_repositories)
        return True

    @Slot()
    def clear(self) -> None:
        self._request_id += 1
        self._clear_state()
        clear_ui_error()

    def _clear_state(self) -> None:
        self._project_name = ""
        self._context_name = ""
        self._is_loading = False
        self._result = None
        self._set_environment_sections([])
        self.stateChanged.emit()

    def _start_preview_job(
        self,
        request_id: int,
        package_requests: list[str],
        package_paths: list[str],
    ) -> None:
        worker = _ContextPreviewWorker(request_id, list(package_requests), list(package_paths))
        worker.signals.finished.connect(self._apply_preview_result)
        self._active_workers[request_id] = worker
        self._thread_pool.start(worker)

    @Slot(int, object)
    def _apply_preview_result(self, request_id: int, resolve_result: object) -> None:
        self._active_workers.pop(request_id, None)
        if request_id != self._request_id:
            return

        self._is_loading = False
        if not isinstance(resolve_result, ResolveResult):
            self._result = None
            self._set_environment_sections([])
            self.stateChanged.emit()
            report_ui_error("Failed to resolve preview data.")
            return

        if not resolve_result.success:
            self._result = None
            self._set_environment_sections([])
            self.stateChanged.emit()
            report_ui_error(resolve_result.error or "Failed to resolve preview data.")
            return

        self._result = resolve_result
        self._set_environment_sections(resolve_result.environ_sections)
        self.stateChanged.emit()
        clear_ui_error()

    def _set_environment_sections(self, sections: list[EnvironmentSection]) -> None:
        for model in self._environment_models:
            model.deleteLater()

        self._environment_models = []
        self._environment_sections = []

        for section in sections:
            rows = [{"name": name, "value": value} for name, value in section.variables.items()]
            table_model = EnvironmentsTableModel(rows, self)
            self._environment_models.append(table_model)
            self._environment_sections.append(
                {
                    "title": section.title,
                    "rows": rows,
                    "rowCount": len(rows),
                    "tableModel": table_model,
                }
            )


class _ContextPreviewWorkerSignals(QObject):
    finished = Signal(int, object)


class _ContextPreviewWorker(QRunnable):
    def __init__(
        self, request_id: int, package_requests: list[str], package_paths: list[str]
    ) -> None:
        super().__init__()
        self._request_id = request_id
        self._package_requests = package_requests
        self._package_paths = package_paths
        self.signals = _ContextPreviewWorkerSignals()

    @Slot()
    def run(self) -> None:
        self.signals.finished.emit(
            self._request_id,
            resolve_context(self._package_requests, package_paths=self._package_paths),
        )


def _package_entry(label: str) -> dict[str, str]:
    name, separator, version = str(label).rpartition("-")
    if not separator:
        name = str(label)
        version = ""
    return {
        "name": name,
        "version": version,
        "label": label,
    }


class EnvironmentsTableModel(QAbstractTableModel):
    NameRole = Qt.UserRole + 1
    ValueRole = Qt.UserRole + 2

    def __init__(self, rows: list[dict[str, str]], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._rows = [{"name": str(row["name"]), "value": str(row["value"])} for row in rows]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return 2

    def roleNames(self) -> dict[int, QByteArray]:  # noqa: N802
        return {
            self.NameRole: QByteArray(b"envName"),
            self.ValueRole: QByteArray(b"envValue"),
        }

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # noqa: ANN201
        if not index.isValid() or index.row() < 0 or index.row() >= len(self._rows):
            return None

        row_data = self._rows[index.row()]
        if role == self.NameRole:
            return row_data["name"]
        if role == self.ValueRole:
            return row_data["value"]
        if role == Qt.DisplayRole:
            return row_data["name"] if index.column() == 0 else row_data["value"]
        return None

    @Slot(int, result="QVariantMap")
    def rowData(self, row: int) -> dict[str, str]:  # noqa: N802
        if row < 0 or row >= len(self._rows):
            return {}
        return dict(self._rows[row])
