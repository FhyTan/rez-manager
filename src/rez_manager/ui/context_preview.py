"""QML-facing controller for resolved context preview data."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from os import environ, pathsep

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

from rez_manager.adapter.context import (
    ResolveResult,
    resolve_context,
    system_environment_variable_names,
)
from rez_manager.exceptions import RezResolveError
from rez_manager.models.rez_context import RezContext
from rez_manager.models.settings import AppSettings
from rez_manager.runtime import IS_WINDOWS
from rez_manager.ui.error_hub import clear_ui_error, report_object_ui_error

QML_IMPORT_NAME = "RezManager"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class ContextPreviewController(QObject):
    stateChanged = Signal()
    previewResolved = Signal()

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
        return bool(self._environment_sections or self._result.packages)

    @Property(bool, notify=stateChanged)
    def isLoading(self) -> bool:  # noqa: N802
        return self._is_loading

    @Property(str, constant=True)
    def pathSeparator(self) -> str:  # noqa: N802
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
            report_object_ui_error(self, str(exc))
            return False

        return self._load_package_requests(
            request_id,
            project_name,
            context_name,
            context.packages,
            settings.package_repositories,
        )

    @Slot(str, str, "QVariantList", result=bool)
    def loadPackageRequests(  # noqa: N802
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
            report_object_ui_error(self, str(exc))
            return False

        normalized_requests = [str(request).strip() for request in package_requests]
        return self._load_package_requests(
            request_id,
            project_name,
            context_name,
            normalized_requests,
            settings.package_repositories,
        )

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
        self._set_environment_sections(None)
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

    def _load_package_requests(
        self,
        request_id: int,
        project_name: str,
        context_name: str,
        package_requests: Sequence[str],
        package_paths: Sequence[str],
    ) -> bool:
        self._project_name = project_name
        self._context_name = context_name
        self._result = None
        self._is_loading = True
        self.stateChanged.emit()
        clear_ui_error()
        self._start_preview_job(request_id, list(package_requests), list(package_paths))
        return True

    @Slot(int, object)
    def _apply_preview_result(self, request_id: int, resolve_result: object) -> None:
        self._active_workers.pop(request_id, None)
        if request_id != self._request_id:
            return

        self._is_loading = False
        if isinstance(resolve_result, RezResolveError):
            self._result = None
            self._set_environment_sections(None)
            self.stateChanged.emit()
            report_object_ui_error(self, str(resolve_result))
            return

        if not isinstance(resolve_result, ResolveResult):
            self._result = None
            self._set_environment_sections(None)
            self.stateChanged.emit()
            report_object_ui_error(self, "Failed to resolve preview data.")
            return

        self._result = resolve_result
        self._set_environment_sections(resolve_result.environ)
        self.stateChanged.emit()
        clear_ui_error()
        self.previewResolved.emit()

    def _set_environment_sections(self, resolved_environ: Mapping[str, str] | None) -> None:
        if resolved_environ is None:
            resolved_environ = {}
        for model in self._environment_models:
            model.deleteLater()

        self._environment_models = []
        self._environment_sections = []
        if not resolved_environ:
            return

        section_rows = self._build_environment_sections(resolved_environ)

        for title, entries in section_rows:
            rows = [{"name": name, "value": value} for name, value in entries.items()]
            table_model = EnvironmentsTableModel(rows, self)
            self._environment_models.append(table_model)
            self._environment_sections.append(
                {
                    "title": title,
                    "rows": rows,
                    "rowCount": len(rows),
                    "tableModel": table_model,
                }
            )

    def _build_environment_sections(
        self, resolved_environ: Mapping[str, str]
    ) -> list[tuple[str, dict[str, str]]]:
        system_names = system_environment_variable_names()
        system_lookup = {name.upper() for name in system_names} if IS_WINDOWS else set(system_names)
        remaining_system_path_entries = Counter(_split_path_entries(environ.get("PATH", "")))
        user_entries: dict[str, str] = {}
        system_entries: dict[str, str] = {}
        rez_entries: dict[str, str] = {}

        # Classify variables into REZ_, system, and user sections.
        for raw_name, raw_value in resolved_environ.items():
            name = str(raw_name)
            value = str(raw_value)

            if name.startswith("REZ_"):
                rez_entries[name] = value
                continue

            lookup_name = name.upper() if IS_WINDOWS else name
            if lookup_name == "PATH":
                continue

            if lookup_name in system_lookup:
                system_entries[name] = value
                continue

            user_entries[name] = value

        # Special handling for PATH.
        system_path_entries: list[str] = []
        user_path_entries: list[str] = []
        for entry in _split_path_entries(resolved_environ.get("PATH", "")):
            if remaining_system_path_entries[entry] > 0:
                remaining_system_path_entries[entry] -= 1
                system_path_entries.append(entry)
            else:
                user_path_entries.append(entry)

        if user_path_entries:
            user_entries["PATH"] = pathsep.join(user_path_entries)
        if system_path_entries:
            system_entries["PATH"] = pathsep.join(system_path_entries)

        # Rez resolves against the preserved system environment, but the preview payload only
        # contains variables that Rez returns explicitly. Launch still inherits the preserved
        # system variables from the current process, so the preview must add them back here to
        # reflect the effective launch environment and avoid future regressions.
        for key, value in environ.items():
            for name in system_names:
                if IS_WINDOWS:
                    if (
                        key.upper() == name.upper()
                        and key not in system_entries
                        and key not in user_entries
                    ):
                        system_entries[key] = value
                        break
                else:
                    if key == name and key not in system_entries and key not in user_entries:
                        system_entries[key] = value
                        break

        def sort_dict(d: dict[str, str]) -> dict[str, str]:
            return dict(sorted(d.items(), key=lambda item: item[0].lower()))

        return [
            ("User Environment", sort_dict(user_entries)),
            ("System Environment", sort_dict(system_entries)),
            ("REZ_ Environment", sort_dict(rez_entries)),
        ]


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
        try:
            preview_result = resolve_context(
                self._package_requests,
                package_paths=self._package_paths,
            )
        except RezResolveError as exc:
            self.signals.finished.emit(self._request_id, exc)
            return

        self.signals.finished.emit(self._request_id, preview_result)


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


def _split_path_entries(path_value: str) -> list[str]:
    if not path_value:
        return []
    return [entry for entry in path_value.split(pathsep) if entry]


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
