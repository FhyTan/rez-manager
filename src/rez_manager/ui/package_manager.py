"""QML-facing controller for the package manager window."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QByteArray,
    QModelIndex,
    QObject,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtQml import QmlElement

from rez_manager.adapter.packages import (
    PackageInfo,
    RepositoryInfo,
    get_package_info,
    get_package_versions,
    list_repositories,
)
from rez_manager.models.rez_context import ContextMeta, LaunchTarget, RezContext
from rez_manager.models.settings import AppSettings
from rez_manager.ui.error_hub import clear_ui_error, report_ui_error

QML_IMPORT_NAME = "RezManager"
QML_IMPORT_MAJOR_VERSION = 1

_PACKAGE_REQUEST_WITH_VERSION = re.compile(r"^(?P<name>.+?)(?:-(?P<version>\d.*))?$")


@dataclass(frozen=True)
class _PackageRequestItem:
    request: str
    name: str
    version: str


def _split_package_request(request: str) -> _PackageRequestItem:
    normalized_request = str(request).strip()
    match = _PACKAGE_REQUEST_WITH_VERSION.match(normalized_request)
    if match is None:
        return _PackageRequestItem(request=normalized_request, name=normalized_request, version="")

    name = match.group("name") or normalized_request
    version = match.group("version") or ""
    return _PackageRequestItem(request=normalized_request, name=name, version=version)


def _build_package_request(name: str, version: str) -> str:
    trimmed_name = str(name).strip()
    trimmed_version = str(version).strip()
    return f"{trimmed_name}-{trimmed_version}" if trimmed_version else trimmed_name


def _empty_package_detail() -> dict[str, object]:
    return {
        "name": "",
        "versions": [],
        "description": "",
        "requires": [],
        "variants": [],
        "tools": [],
        "code": "",
    }


class PackageRequestListModel(QAbstractListModel):
    requestsChanged = Signal()

    RequestRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    VersionRole = Qt.UserRole + 3

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._items: list[_PackageRequestItem] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._items)

    def roleNames(self) -> dict[int, QByteArray]:  # noqa: N802
        return {
            self.RequestRole: QByteArray(b"request"),
            self.NameRole: QByteArray(b"pkgName"),
            self.VersionRole: QByteArray(b"version"),
        }

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # noqa: ANN201
        if not index.isValid() or index.row() < 0 or index.row() >= len(self._items):
            return None

        item = self._items[index.row()]
        if role == self.RequestRole:
            return item.request
        if role == self.NameRole:
            return item.name
        if role == self.VersionRole:
            return item.version
        return None

    def reset_requests(self, requests: Sequence[str]) -> None:
        self.beginResetModel()
        self._items = [_split_package_request(request) for request in requests]
        self.endResetModel()
        self.requestsChanged.emit()

    def remove_request(self, row: int) -> bool:
        if row < 0 or row >= len(self._items):
            return False

        self.beginRemoveRows(QModelIndex(), row, row)
        self._items.pop(row)
        self.endRemoveRows()
        self.requestsChanged.emit()
        return True

    def upsert_request(self, name: str, version: str) -> None:
        request = _build_package_request(name, version)
        item = _split_package_request(request)

        for row, existing in enumerate(self._items):
            if existing.name != item.name:
                continue

            self._items[row] = item
            model_index = self.index(row, 0)
            self.dataChanged.emit(
                model_index, model_index, [self.RequestRole, self.NameRole, self.VersionRole]
            )
            self.requestsChanged.emit()
            return

        row = len(self._items)
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.append(item)
        self.endInsertRows()
        self.requestsChanged.emit()

    def requests(self) -> list[str]:
        return [item.request for item in self._items]


@QmlElement
class PackageManagerController(QObject):
    repositoryTreeChanged = Signal()
    packageDetailChanged = Signal()
    packageCountChanged = Signal()
    selectedDetailVersionChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._context: RezContext | None = None
        self._repo_paths: list[str] = []
        self._repository_tree: list[dict[str, object]] = []
        self._package_detail: dict[str, object] = _empty_package_detail()
        self._selected_package_name = ""
        self._selected_detail_version = -1
        self._package_requests_model = PackageRequestListModel(self)
        self._package_requests_model.requestsChanged.connect(self.packageCountChanged)

    @Property(QObject, constant=True)
    def packageRequestsModel(self) -> QObject:  # noqa: N802
        return self._package_requests_model

    @Property("QVariantList", notify=repositoryTreeChanged)
    def repositoryTree(self) -> list[dict[str, object]]:  # noqa: N802
        return list(self._repository_tree)

    @Property("QVariantMap", notify=packageDetailChanged)
    def packageDetail(self) -> dict[str, object]:  # noqa: N802
        return dict(self._package_detail)

    @Property(int, notify=packageCountChanged)
    def packageCount(self) -> int:  # noqa: N802
        return len(self._package_requests_model.requests())

    @Property(int, notify=selectedDetailVersionChanged)
    def selectedDetailVersion(self) -> int:  # noqa: N802
        return self._selected_detail_version

    @Slot(str, str, result=bool)
    def loadContext(self, project_name: str, context_name: str) -> bool:  # noqa: N802
        try:
            context = RezContext.load(project_name, context_name)
            settings = AppSettings.load()
            repositories = list_repositories(settings.package_repositories)
        except (OSError, TypeError, ValueError) as exc:
            self._context = None
            self._repo_paths = []
            self._package_requests_model.reset_requests([])
            self._set_repository_tree([])
            self._clear_selection()
            report_ui_error(str(exc))
            return False

        self._context = context
        self._repo_paths = list(settings.package_repositories)
        self._package_requests_model.reset_requests(context.packages)
        self._set_repository_tree(repositories)
        self._clear_selection()
        clear_ui_error()
        return True

    @Slot()
    def clearSelection(self) -> None:  # noqa: N802
        self._clear_selection()

    @Slot(int, result=bool)
    def removePackageRequest(self, row: int) -> bool:  # noqa: N802
        removed = self._package_requests_model.remove_request(row)
        if removed:
            clear_ui_error()
        return removed

    @Slot(str, str, result=bool)
    def addPackageRequest(self, name: str, version: str) -> bool:  # noqa: N802
        trimmed_name = str(name).strip()
        if not trimmed_name:
            report_ui_error("Package name is required.")
            return False

        self._package_requests_model.upsert_request(trimmed_name, version)
        clear_ui_error()
        return True

    @Slot(int, int, result=bool)
    def selectPackage(self, repo_index: int, package_index: int) -> bool:  # noqa: N802
        if repo_index < 0 or repo_index >= len(self._repository_tree):
            self._clear_selection()
            return False

        packages = self._repository_tree[repo_index]["packages"]
        if not isinstance(packages, list) or package_index < 0 or package_index >= len(packages):
            self._clear_selection()
            return False

        package_name = str(packages[package_index])
        self._refresh_package_detail(package_name)
        clear_ui_error()
        return True

    @Slot(int, result=bool)
    def selectDetailVersion(self, index: int) -> bool:  # noqa: N802
        versions = self._package_detail.get("versions", [])
        if not isinstance(versions, list) or index < 0 or index >= len(versions):
            return False
        if not self._selected_package_name:
            return False

        self._refresh_package_detail(self._selected_package_name, str(versions[index]))
        clear_ui_error()
        return True

    @Slot(result=bool)
    def save(self) -> bool:
        if self._context is None:
            report_ui_error("No context is loaded.")
            return False

        try:
            updated_meta = ContextMeta(
                name=self._context.name,
                description=self._context.description,
                launch_target=LaunchTarget(self._context.launch_target),
                custom_command=self._context.meta.custom_command,
                packages=self._package_requests_model.requests(),
            )
            self._context.update(self._context.project_name, updated_meta)
        except (OSError, TypeError, ValueError) as exc:
            report_ui_error(str(exc))
            return False

        clear_ui_error()
        return True

    def _set_repository_tree(self, repositories: Sequence[RepositoryInfo]) -> None:
        tree = [
            {
                "path": repository.path,
                "label": repository.label,
                "packages": list(repository.packages),
            }
            for repository in repositories
        ]
        if self._repository_tree != tree:
            self._repository_tree = tree
            self.repositoryTreeChanged.emit()

    def _clear_selection(self) -> None:
        self._selected_package_name = ""
        self._set_selected_detail_version(-1)
        self._set_package_detail(_empty_package_detail())

    def _refresh_package_detail(
        self, package_name: str, preferred_version: str | None = None
    ) -> None:
        versions = get_package_versions(package_name, self._repo_paths)
        version = preferred_version
        if version not in versions:
            version = versions[0] if versions else ""

        package_info = (
            get_package_info(package_name, version, self._repo_paths) if version else None
        )
        self._selected_package_name = package_name
        self._set_selected_detail_version(versions.index(version) if version in versions else -1)
        self._set_package_detail(_package_detail_payload(package_name, versions, package_info))

    def _set_selected_detail_version(self, index: int) -> None:
        if self._selected_detail_version != index:
            self._selected_detail_version = index
            self.selectedDetailVersionChanged.emit()

    def _set_package_detail(self, detail: dict[str, object]) -> None:
        if self._package_detail != detail:
            self._package_detail = detail
            self.packageDetailChanged.emit()


def _package_detail_payload(
    package_name: str,
    versions: Sequence[str],
    package_info: PackageInfo | None,
) -> dict[str, object]:
    if package_info is None:
        return {
            "name": package_name,
            "versions": list(versions),
            "description": "",
            "requires": [],
            "variants": [],
            "tools": [],
            "code": "",
        }

    return {
        "name": package_info.name,
        "versions": list(versions) if versions else list(package_info.versions),
        "description": package_info.description,
        "requires": list(package_info.requires),
        "variants": [" ".join(variant) for variant in package_info.variants],
        "tools": list(package_info.tools),
        "code": package_info.python_statements,
    }
