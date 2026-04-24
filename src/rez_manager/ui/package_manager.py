"""QML-facing controller and models for the package manager window."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from PySide6.QtCore import (
    Property,
    QAbstractItemModel,
    QAbstractListModel,
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

from rez_manager.adapter.packages import (
    PackageInfo,
    RepositoryInfo,
    clear_package_cache,
    get_package_info,
    get_package_versions,
    list_repositories,
)
from rez_manager.exceptions import RezAdapterError
from rez_manager.models.launch_target import parse_launch_target
from rez_manager.models.rez_context import ContextMeta, RezContext
from rez_manager.models.settings import AppSettings
from rez_manager.ui.error_hub import clear_ui_error, report_ui_error

QML_IMPORT_NAME = "RezManager"
QML_IMPORT_MAJOR_VERSION = 1

_AUTO_VERSION = "auto"
_PACKAGE_REQUEST_WITH_VERSION = re.compile(r"^(?P<name>.+?)(?:-(?P<version>.*))?$")


@dataclass(frozen=True)
class _PackageRequestItem:
    request: str
    name: str
    version: str

    @property
    def display_version(self) -> str:
        return self.version or _AUTO_VERSION


@dataclass
class _RepositoryTreeNode:
    label: str
    node_type: str
    repo_index: int = -1
    package_index: int = -1
    package_name: str = ""
    path: str = ""
    parent: _RepositoryTreeNode | None = None
    children: list[_RepositoryTreeNode] = field(default_factory=list)

    def child(self, row: int) -> _RepositoryTreeNode | None:
        if row < 0 or row >= len(self.children):
            return None
        return self.children[row]

    def row(self) -> int:
        if self.parent is None:
            return 0
        return self.parent.children.index(self)


def _split_package_request(request: str) -> _PackageRequestItem:
    """Parse a package request string into its name and version components.

    >>> _split_package_request("foo-1.2.3")
    _PackageRequestItem(request='foo-1.2.3', name='foo', version='1.2.3')
    >>> _split_package_request("foo-auto")
    _PackageRequestItem(request='foo-auto', name='foo', version='auto')
    """

    normalized_request = str(request).strip()
    match = _PACKAGE_REQUEST_WITH_VERSION.match(normalized_request)
    if match is None:
        return _PackageRequestItem(request=normalized_request, name=normalized_request, version="")

    name = match.group("name") or normalized_request
    version = match.group("version") or ""
    return _PackageRequestItem(request=normalized_request, name=name, version=version)


def _build_package_request(name: str, version: str) -> str:
    """Construct a package request string from its name and version components.

    >>> _build_package_request("foo", "1.2.3")
    'foo-1.2.3'
    >>> _build_package_request("foo", "auto")
    'foo'
    """

    trimmed_name = str(name).strip()
    normalized_version = _normalize_version(version)
    return f"{trimmed_name}-{normalized_version}" if normalized_version else trimmed_name


def _normalize_version(version: str) -> str:
    """Normalize a version string by trimming whitespace and converting 'auto' to an empty string.

    >>> _normalize_version(" 1.2.3 ")
    '1.2.3'
    >>> _normalize_version("auto")
    ''
    """
    trimmed_version = str(version).strip()
    return "" if trimmed_version == _AUTO_VERSION else trimmed_version


def _detail_versions(versions: Sequence[str], preferred_version: str) -> list[str]:
    """Return a list of versions to show in the package detail view,
    ensuring the preferred version is included.

    >>> _detail_versions(["1.0", "2.0"], "1.2.3")
    ['auto', '1.0', '2.0', '1.2.3']
    """
    detail_versions = [_AUTO_VERSION, *versions]
    normalized_preferred_version = _normalize_version(preferred_version)
    if normalized_preferred_version and normalized_preferred_version not in detail_versions:
        detail_versions.append(normalized_preferred_version)
    return detail_versions


def _load_package_detail(
    package_name: str,
    preferred_version: str,
    repo_paths: Sequence[str],
) -> tuple[list[str], int, PackageInfo | None]:
    """Load package detail data for the requested package/version selection."""
    versions = get_package_versions(package_name, list(repo_paths))
    detail_versions = _detail_versions(versions, preferred_version)
    normalized_preferred_version = _normalize_version(preferred_version)
    selected_version = normalized_preferred_version or _AUTO_VERSION
    if selected_version not in detail_versions:
        selected_version = _AUTO_VERSION
    selected_version_index = detail_versions.index(selected_version)

    info_version = normalized_preferred_version or (versions[0] if versions else "")
    package_info = (
        get_package_info(package_name, info_version, list(repo_paths)) if info_version else None
    )
    return detail_versions, selected_version_index, package_info


@dataclass(frozen=True, slots=True)
class _PackageSelectionSnapshot:
    selection_type: str = "none"
    package_name: str = ""
    preferred_version: str = ""


@dataclass(slots=True)
class _RepositoryRefreshResult:
    success: bool
    repositories: list[RepositoryInfo] = field(default_factory=list)
    selection_type: str = "none"
    detail_package_name: str = ""
    detail_versions: list[str] = field(default_factory=list)
    detail_selected_version_index: int = -1
    detail_package_info: PackageInfo | None = None
    error: str | None = None


class PackageRequestListModel(QAbstractListModel):
    requestsChanged = Signal()

    RequestRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    VersionRole = Qt.UserRole + 3
    DisplayVersionRole = Qt.UserRole + 4

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
            self.DisplayVersionRole: QByteArray(b"displayVersion"),
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
        if role == self.DisplayVersionRole:
            return item.display_version
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

    def upsert_request(self, name: str, version: str) -> int:
        request = _build_package_request(name, version)
        item = _split_package_request(request)

        for row, existing in enumerate(self._items):
            if existing.name != item.name:
                continue

            self._items[row] = item
            model_index = self.index(row, 0)
            self.dataChanged.emit(
                model_index,
                model_index,
                [
                    self.RequestRole,
                    self.NameRole,
                    self.VersionRole,
                    self.DisplayVersionRole,
                ],
            )
            self.requestsChanged.emit()
            return row

        row = len(self._items)
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.append(item)
        self.endInsertRows()
        self.requestsChanged.emit()
        return row

    def requests(self) -> list[str]:
        return [item.request for item in self._items]

    def item_at(self, row: int) -> _PackageRequestItem | None:
        if row < 0 or row >= len(self._items):
            return None
        return self._items[row]


class RepositoryTreeModel(QAbstractItemModel):
    LabelRole = Qt.UserRole + 1
    NodeTypeRole = Qt.UserRole + 2
    RepoIndexRole = Qt.UserRole + 3
    PackageIndexRole = Qt.UserRole + 4
    PackageNameRole = Qt.UserRole + 5
    PathRole = Qt.UserRole + 6

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._root = _RepositoryTreeNode(label="", node_type="root")
        self._repositories: list[RepositoryInfo] = []

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 1

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid() and parent.column() != 0:
            return 0
        node = self._root if not parent.isValid() else parent.internalPointer()
        return len(node.children)

    def index(  # noqa: N802
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        if column != 0 or row < 0:
            return QModelIndex()

        parent_node = self._root if not parent.isValid() else parent.internalPointer()
        child_node = parent_node.child(row)
        if child_node is None:
            return QModelIndex()
        return self.createIndex(row, column, child_node)

    def parent(self, index: QModelIndex) -> QModelIndex:  # noqa: N802
        if not index.isValid():
            return QModelIndex()

        node = index.internalPointer()
        parent_node = node.parent
        if parent_node is None or parent_node is self._root:
            return QModelIndex()
        return self.createIndex(parent_node.row(), 0, parent_node)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # noqa: ANN201
        if not index.isValid():
            return None

        node = index.internalPointer()
        if role in (Qt.DisplayRole, self.LabelRole):
            return node.label
        if role == self.NodeTypeRole:
            return node.node_type
        if role == self.RepoIndexRole:
            return node.repo_index
        if role == self.PackageIndexRole:
            return node.package_index
        if role == self.PackageNameRole:
            return node.package_name
        if role == self.PathRole:
            return node.path
        return None

    def roleNames(self) -> dict[int, QByteArray]:  # noqa: N802
        return {
            self.LabelRole: QByteArray(b"label"),
            self.NodeTypeRole: QByteArray(b"nodeType"),
            self.RepoIndexRole: QByteArray(b"repoIndex"),
            self.PackageIndexRole: QByteArray(b"packageIndex"),
            self.PackageNameRole: QByteArray(b"packageName"),
            self.PathRole: QByteArray(b"path"),
        }

    def reset_repositories(self, repositories: Sequence[RepositoryInfo]) -> None:
        self.beginResetModel()
        self._repositories = list(repositories)
        self._root = _RepositoryTreeNode(label="", node_type="root")
        for repo_index, repository in enumerate(self._repositories):
            repository_node = _RepositoryTreeNode(
                label=repository.label,
                node_type="repository",
                repo_index=repo_index,
                path=repository.path,
                parent=self._root,
            )
            repository_node.children = [
                _RepositoryTreeNode(
                    label=package_name,
                    node_type="package",
                    repo_index=repo_index,
                    package_index=package_index,
                    package_name=package_name,
                    path=repository.path,
                    parent=repository_node,
                )
                for package_index, package_name in enumerate(repository.packages)
            ]
            self._root.children.append(repository_node)
        self.endResetModel()

    def package_name_at(self, repo_index: int, package_index: int) -> str | None:
        if repo_index < 0 or repo_index >= len(self._repositories):
            return None

        packages = self._repositories[repo_index].packages
        if package_index < 0 or package_index >= len(packages):
            return None
        return packages[package_index]

    def find_package(self, package_name: str) -> tuple[int, int] | None:
        for repo_index, repository in enumerate(self._repositories):
            for package_index, candidate in enumerate(repository.packages):
                if candidate == package_name:
                    return repo_index, package_index
        return None


class PackageDetailObject(QObject):
    stateChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._name = ""
        self._versions: list[str] = []
        self._selected_version_index = -1
        self._description = ""
        self._requires: list[str] = []
        self._variants: list[str] = []
        self._tools: list[str] = []
        self._code = ""

    @Property(bool, notify=stateChanged)
    def hasSelection(self) -> bool:  # noqa: N802
        return bool(self._name)

    @Property(str, notify=stateChanged)
    def name(self) -> str:
        return self._name

    @Property("QVariantList", notify=stateChanged)
    def versions(self) -> list[str]:
        return list(self._versions)

    @Property(int, notify=stateChanged)
    def selectedVersionIndex(self) -> int:  # noqa: N802
        return self._selected_version_index

    @Property(str, notify=stateChanged)
    def selectedVersion(self) -> str:  # noqa: N802
        if 0 <= self._selected_version_index < len(self._versions):
            return self._versions[self._selected_version_index]
        return ""

    @Property(str, notify=stateChanged)
    def description(self) -> str:
        return self._description

    @Property("QVariantList", notify=stateChanged)
    def requires(self) -> list[str]:
        return list(self._requires)

    @Property("QVariantList", notify=stateChanged)
    def variants(self) -> list[str]:
        return list(self._variants)

    @Property("QVariantList", notify=stateChanged)
    def tools(self) -> list[str]:
        return list(self._tools)

    @Property(str, notify=stateChanged)
    def code(self) -> str:
        return self._code

    def reset(self) -> None:
        self.apply(
            name="",
            versions=[],
            selected_version_index=-1,
            description="",
            requires=[],
            variants=[],
            tools=[],
            code="",
        )

    def setPackageWithSelectedVersion(  # noqa: N802
        self,
        package_name: str,
        versions: Sequence[str],
        selected_version_index: int,
        package_info: PackageInfo | None,
    ) -> None:
        if package_info is None:
            self.apply(
                name=package_name,
                versions=list(versions),
                selected_version_index=selected_version_index,
                description="",
                requires=[],
                variants=[],
                tools=[],
                code="",
            )
        else:
            self.apply(
                name=package_info.name,
                versions=list(versions),
                selected_version_index=selected_version_index,
                description=package_info.description,
                requires=list(package_info.requires),
                variants=[" ".join(variant) for variant in package_info.variants],
                tools=list(package_info.tools),
                code=package_info.python_statements,
            )

    def apply(
        self,
        *,
        name: str,
        versions: Sequence[str],
        selected_version_index: int,
        description: str,
        requires: Sequence[str],
        variants: Sequence[str],
        tools: Sequence[str],
        code: str,
    ) -> None:
        next_state = (
            name,
            list(versions),
            selected_version_index,
            description,
            list(requires),
            list(variants),
            list(tools),
            code,
        )
        current_state = (
            self._name,
            self._versions,
            self._selected_version_index,
            self._description,
            self._requires,
            self._variants,
            self._tools,
            self._code,
        )
        if next_state == current_state:
            return

        (
            self._name,
            self._versions,
            self._selected_version_index,
            self._description,
            self._requires,
            self._variants,
            self._tools,
            self._code,
        ) = next_state
        self.stateChanged.emit()


@QmlElement
class PackageManagerController(QObject):
    stateChanged = Signal()
    packageCountChanged = Signal()
    selectedRequestRowChanged = Signal()
    selectedRepositoryIndexChanged = Signal()
    selectedRepositoryPackageIndexChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._context: RezContext | None = None
        self._repo_paths: list[str] = []
        self._is_loading_repositories = False
        self._repository_refresh_request_id = 0
        self._thread_pool = QThreadPool.globalInstance()
        self._active_repository_refresh_workers: dict[int, _RepositoryRefreshWorker] = {}
        self._selected_request_row = -1
        self._selected_repository_index = -1
        self._selected_repository_package_index = -1
        self._package_requests_model = PackageRequestListModel(self)
        self._repository_model = RepositoryTreeModel(self)
        self._package_detail = PackageDetailObject(self)
        self._package_requests_model.requestsChanged.connect(self.packageCountChanged)

    @Property(QObject, constant=True)
    def packageRequestsModel(self) -> QObject:  # noqa: N802
        return self._package_requests_model

    @Property(QObject, constant=True)
    def repositoryModel(self) -> QObject:  # noqa: N802
        return self._repository_model

    @Property(QObject, constant=True)
    def packageDetail(self) -> QObject:  # noqa: N802
        return self._package_detail

    @Property(bool, notify=stateChanged)
    def isLoadingRepositories(self) -> bool:  # noqa: N802
        return self._is_loading_repositories

    @Property(int, notify=packageCountChanged)
    def packageCount(self) -> int:  # noqa: N802
        return len(self._package_requests_model.requests())

    @Property("QVariantList", notify=packageCountChanged)
    def packageRequests(self) -> list[str]:  # noqa: N802
        return self._package_requests_model.requests()

    @Property(int, notify=selectedRequestRowChanged)
    def selectedRequestRow(self) -> int:  # noqa: N802
        return self._selected_request_row

    @Property(int, notify=selectedRepositoryIndexChanged)
    def selectedRepositoryIndex(self) -> int:  # noqa: N802
        return self._selected_repository_index

    @Property(int, notify=selectedRepositoryPackageIndexChanged)
    def selectedRepositoryPackageIndex(self) -> int:  # noqa: N802
        return self._selected_repository_package_index

    @Slot(str, str, result=bool)
    def loadContext(self, project_name: str, context_name: str) -> bool:  # noqa: N802
        try:
            context = RezContext.load(project_name, context_name)
            settings = AppSettings.load()
        except (KeyError, OSError, TypeError, ValueError) as exc:
            self._context = None
            self._repo_paths = []
            self._set_loading_repositories(False)
            self._package_requests_model.reset_requests([])
            self._repository_model.reset_repositories([])
            self._clear_selection()
            report_ui_error(str(exc))
            return False

        self._context = context
        self._repo_paths = list(settings.package_repositories)
        self._package_requests_model.reset_requests(context.packages)
        self._repository_model.reset_repositories([])
        self._clear_selection()
        clear_ui_error()
        self._start_repository_refresh(clear_cache=False)
        return True

    @Slot(result=bool)
    def refresh(self) -> bool:
        if self._context is None:
            report_ui_error("No context is loaded.")
            return False

        self._start_repository_refresh(
            clear_cache=True,
            selection_snapshot=self._current_selection_snapshot(),
        )
        clear_ui_error()
        return True

    @Slot()
    def clearSelection(self) -> None:  # noqa: N802
        self._clear_selection()

    @Slot(int, result=bool)
    def removePackageRequest(self, row: int) -> bool:  # noqa: N802
        removed = self._package_requests_model.remove_request(row)
        if not removed:
            return False

        if self._selected_request_row == row:
            self._clear_selection()
        elif self._selected_request_row > row:
            self._set_selected_request_row(self._selected_request_row - 1)
        clear_ui_error()
        return True

    @Slot(int, result=bool)
    def selectRequiredPackage(self, row: int) -> bool:  # noqa: N802
        item = self._package_requests_model.item_at(row)
        if item is None:
            self._clear_selection()
            return False

        self._set_selected_request_row(row)
        self._set_selected_repository_index(-1)
        self._set_selected_repository_package_index(-1)
        if self._refresh_package_detail(item.name, item.version):
            clear_ui_error()
        return True

    @Slot(str, str, result=bool)
    def addPackageRequest(self, name: str, version: str) -> bool:  # noqa: N802
        trimmed_name = str(name).strip()
        if not trimmed_name:
            report_ui_error("Package name is required.")
            return False

        row = self._package_requests_model.upsert_request(trimmed_name, version)
        self._set_selected_request_row(row)
        self._set_selected_repository_index(-1)
        self._set_selected_repository_package_index(-1)
        if self._refresh_package_detail(trimmed_name, _normalize_version(version)):
            clear_ui_error()
        return True

    @Slot(int, int, result=bool)
    def selectRepositoryPackage(self, repo_index: int, package_index: int) -> bool:  # noqa: N802
        package_name = self._repository_model.package_name_at(repo_index, package_index)
        if package_name is None:
            self._clear_selection()
            return False

        self._set_selected_request_row(-1)
        self._set_selected_repository_index(repo_index)
        self._set_selected_repository_package_index(package_index)
        if self._refresh_package_detail(package_name, ""):
            clear_ui_error()
        return True

    @Slot(int, result=bool)
    def selectDetailVersion(self, index: int) -> bool:  # noqa: N802
        versions = self._package_detail.versions
        if index < 0 or index >= len(versions):
            return False
        if not self._package_detail.hasSelection:
            return False

        selected_version = versions[index]
        if self._refresh_package_detail(
            self._package_detail.name,
            _normalize_version(selected_version),
        ):
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
                launch_target=parse_launch_target(self._context.launch_target),
                custom_command=self._context.meta.custom_command,
                packages=self._package_requests_model.requests(),
            )
            self._context.update(self._context.project_name, updated_meta)
        except (OSError, TypeError, ValueError) as exc:
            report_ui_error(str(exc))
            return False

        clear_ui_error()
        return True

    def _clear_selection(self) -> None:
        self._set_selected_request_row(-1)
        self._set_selected_repository_index(-1)
        self._set_selected_repository_package_index(-1)
        self._package_detail.reset()

    def _current_selection_snapshot(self) -> _PackageSelectionSnapshot:
        if not self._package_detail.hasSelection:
            return _PackageSelectionSnapshot()
        if self._selected_request_row >= 0:
            return _PackageSelectionSnapshot(
                selection_type="request",
                package_name=self._package_detail.name,
                preferred_version=self._package_detail.selectedVersion,
            )
        if (
            self._selected_repository_index >= 0
            and self._selected_repository_package_index >= 0
        ):
            return _PackageSelectionSnapshot(
                selection_type="repository",
                package_name=self._package_detail.name,
                preferred_version=self._package_detail.selectedVersion,
            )
        return _PackageSelectionSnapshot()

    def _refresh_package_detail(self, package_name: str, preferred_version: str) -> bool:
        try:
            detail_versions, selected_version_index, package_info = _load_package_detail(
                package_name,
                preferred_version,
                self._repo_paths,
            )
        except RezAdapterError as exc:
            self._package_detail.reset()
            report_ui_error(str(exc))
            return False

        self._package_detail.setPackageWithSelectedVersion(
            package_name,
            detail_versions,
            selected_version_index,
            package_info,
        )
        return True

    def _restore_refresh_selection(self, refresh_result: _RepositoryRefreshResult) -> None:
        if refresh_result.selection_type == "request":
            self._set_selected_repository_index(-1)
            self._set_selected_repository_package_index(-1)
        elif refresh_result.selection_type == "repository":
            package_location = self._repository_model.find_package(
                refresh_result.detail_package_name
            )
            if package_location is None:
                self._set_selected_repository_index(-1)
                self._set_selected_repository_package_index(-1)
                self._package_detail.reset()
                return
            repo_index, package_index = package_location
            self._set_selected_request_row(-1)
            self._set_selected_repository_index(repo_index)
            self._set_selected_repository_package_index(package_index)
        else:
            self._package_detail.reset()
            return

        self._package_detail.setPackageWithSelectedVersion(
            refresh_result.detail_package_name,
            refresh_result.detail_versions,
            refresh_result.detail_selected_version_index,
            refresh_result.detail_package_info,
        )

    def _set_loading_repositories(self, is_loading: bool) -> None:
        if self._is_loading_repositories != is_loading:
            self._is_loading_repositories = is_loading
            self.stateChanged.emit()

    def _start_repository_refresh(
        self,
        *,
        clear_cache: bool,
        selection_snapshot: _PackageSelectionSnapshot | None = None,
    ) -> None:
        self._repository_refresh_request_id += 1
        request_id = self._repository_refresh_request_id
        self._set_loading_repositories(True)
        worker = _RepositoryRefreshWorker(
            request_id=request_id,
            repo_paths=list(self._repo_paths),
            clear_cache_requested=clear_cache,
            selection_snapshot=selection_snapshot or _PackageSelectionSnapshot(),
        )
        worker.signals.finished.connect(self._apply_repository_refresh_result)
        self._active_repository_refresh_workers[request_id] = worker
        self._thread_pool.start(worker)

    @Slot(int, object)
    def _apply_repository_refresh_result(self, request_id: int, refresh_result: object) -> None:
        self._active_repository_refresh_workers.pop(request_id, None)
        if request_id != self._repository_refresh_request_id:
            return

        self._set_loading_repositories(False)
        if not isinstance(refresh_result, _RepositoryRefreshResult):
            report_ui_error("Failed to load repositories.")
            return
        if not refresh_result.success:
            report_ui_error(refresh_result.error or "Failed to load repositories.")
            return

        self._repository_model.reset_repositories(refresh_result.repositories)
        self._restore_refresh_selection(refresh_result)
        clear_ui_error()

    def _set_selected_request_row(self, row: int) -> None:
        if self._selected_request_row != row:
            self._selected_request_row = row
            self.selectedRequestRowChanged.emit()

    def _set_selected_repository_index(self, repo_index: int) -> None:
        if self._selected_repository_index != repo_index:
            self._selected_repository_index = repo_index
            self.selectedRepositoryIndexChanged.emit()

    def _set_selected_repository_package_index(self, package_index: int) -> None:
        if self._selected_repository_package_index != package_index:
            self._selected_repository_package_index = package_index
            self.selectedRepositoryPackageIndexChanged.emit()


class _RepositoryRefreshWorkerSignals(QObject):
    finished = Signal(int, object)


class _RepositoryRefreshWorker(QRunnable):
    def __init__(
        self,
        *,
        request_id: int,
        repo_paths: list[str],
        clear_cache_requested: bool,
        selection_snapshot: _PackageSelectionSnapshot,
    ) -> None:
        super().__init__()
        self._request_id = request_id
        self._repo_paths = repo_paths
        self._clear_cache_requested = clear_cache_requested
        self._selection_snapshot = selection_snapshot
        self.signals = _RepositoryRefreshWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            if self._clear_cache_requested:
                clear_package_cache()
            repositories = list_repositories(self._repo_paths)
            refresh_result = _RepositoryRefreshResult(
                success=True,
                repositories=repositories,
                selection_type=self._selection_snapshot.selection_type,
            )
            if (
                self._selection_snapshot.selection_type != "none"
                and self._selection_snapshot.package_name
            ):
                detail_versions, selected_version_index, package_info = _load_package_detail(
                    self._selection_snapshot.package_name,
                    self._selection_snapshot.preferred_version,
                    self._repo_paths,
                )
                refresh_result.detail_package_name = self._selection_snapshot.package_name
                refresh_result.detail_versions = detail_versions
                refresh_result.detail_selected_version_index = selected_version_index
                refresh_result.detail_package_info = package_info
        except RezAdapterError as exc:
            self.signals.finished.emit(
                self._request_id,
                _RepositoryRefreshResult(success=False, error=str(exc)),
            )
            return

        self.signals.finished.emit(self._request_id, refresh_result)
