"""QML-facing controller and model for the Package Cache Viewer."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import (
    Property,
    QAbstractItemModel,
    QByteArray,
    QModelIndex,
    QObject,
    QRunnable,
    Qt,
    QThreadPool,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QDesktopServices
from PySide6.QtQml import QmlElement

from rez_manager.adapter.packages import list_cached_variants, remove_cached_variant
from rez_manager.exceptions import RezCacheOperationError
from rez_manager.models.settings import AppSettings
from rez_manager.persistence.app_paths import default_rez_package_caches_dir

QML_IMPORT_NAME = "RezManager"
QML_IMPORT_MAJOR_VERSION = 1

STATUS_LABELS = {1: "Cached", 3: "Copying\u2026", 4: "Stalled", 5: "Pending"}
STATUS_COLORS = {1: "#4DB880", 3: "#D98A38", 4: "#D94F68", 5: "#4E4E72"}
_STATUS_SUMMARY_ORDER = [4, 3, 5, 1]


@dataclass
class _CacheTreeNode:
    node_type: str  # "package" | "variant"
    label: str
    package_name: str = ""
    variant_display: str = ""
    status_code: int = 0
    status_label: str = ""
    source_path: str = ""
    cache_path: str = ""
    handle_json: str = ""
    parent: _CacheTreeNode | None = None
    children: list[_CacheTreeNode] = field(default_factory=list)

    def child(self, row: int) -> _CacheTreeNode | None:
        if row < 0 or row >= len(self.children):
            return None
        return self.children[row]

    def row(self) -> int:
        if self.parent is None:
            return 0
        return self.parent.children.index(self)


def _compute_package_status_summary(children: list[_CacheTreeNode]) -> str:
    counts: dict[int, int] = defaultdict(int)
    for child in children:
        counts[child.status_code] += 1
    for code in _STATUS_SUMMARY_ORDER:
        if counts[code] > 0:
            label = STATUS_LABELS.get(code, f"status {code}")
            if code == 1 and counts[code] == len(children):
                return "all cached"
            return f"{counts[code]} {label.lower()}"
    return ""


def _build_variant_display(var: object) -> str:
    qualified = str(var.qualified_name)
    prefix = str(var.name) + "-"
    short = qualified[len(prefix) :] if qualified.startswith(prefix) else qualified
    variant_reqs = getattr(var, "variant_requires", None)
    if variant_reqs:
        reqs = [str(r) for r in variant_reqs]
        short += " (+" + ", ".join(reqs) + ")"
    return short


def _variant_handle_json(var: object) -> str:
    return json.dumps(var.resource.handle.to_dict())


class _CacheRefreshWorker(QRunnable):
    finished = Signal(object)  # list[tuple] or Exception

    def __init__(self, cache_path: str) -> None:
        super().__init__()
        self._cache_path = cache_path
        self.signals = _CacheRefreshWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            variants = list_cached_variants(self._cache_path)
            self.signals.finished.emit(variants)
        except Exception as exc:
            self.signals.finished.emit(exc)


class _CacheRefreshWorkerSignals(QObject):
    finished = Signal(object)


@QmlElement
class CachedVariantTreeModel(QAbstractItemModel):
    LabelRole = Qt.UserRole + 1
    NodeTypeRole = Qt.UserRole + 2
    PackageNameRole = Qt.UserRole + 3
    VariantDisplayRole = Qt.UserRole + 4
    StatusCodeRole = Qt.UserRole + 5
    StatusLabelRole = Qt.UserRole + 6
    SourcePathRole = Qt.UserRole + 7
    CachePathRole = Qt.UserRole + 8
    HandleJsonRole = Qt.UserRole + 9

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._root = _CacheTreeNode(node_type="root", label="")
        self._filter_text = ""

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 3

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid() and parent.column() != 0:
            return 0
        node = self._root if not parent.isValid() else parent.internalPointer()
        return len(node.children)

    def index(  # noqa: N802
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        if column < 0 or column >= 3 or row < 0:
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

        if role == Qt.DisplayRole:
            col = index.column()
            if col == 0:
                return node.label
            if node.node_type == "variant":
                if col == 1:
                    return node.status_label
                if col == 2:
                    return node.source_path
            return None

        if role == self.LabelRole:
            return node.label
        if role == self.NodeTypeRole:
            return node.node_type
        if role == self.PackageNameRole:
            return node.package_name
        if role == self.VariantDisplayRole:
            return node.variant_display
        if role == self.StatusCodeRole:
            return node.status_code
        if role == self.StatusLabelRole:
            return node.status_label
        if role == self.SourcePathRole:
            return node.source_path
        if role == self.CachePathRole:
            return node.cache_path
        if role == self.HandleJsonRole:
            return node.handle_json
        return None

    def roleNames(self) -> dict[int, QByteArray]:  # noqa: N802
        return {
            self.LabelRole: QByteArray(b"label"),
            self.NodeTypeRole: QByteArray(b"nodeType"),
            self.PackageNameRole: QByteArray(b"packageName"),
            self.VariantDisplayRole: QByteArray(b"variantDisplay"),
            self.StatusCodeRole: QByteArray(b"statusCode"),
            self.StatusLabelRole: QByteArray(b"statusLabel"),
            self.SourcePathRole: QByteArray(b"sourcePath"),
            self.CachePathRole: QByteArray(b"cachePath"),
            self.HandleJsonRole: QByteArray(b"handleJson"),
        }

    @Slot(str)
    def setFilter(self, text: str) -> None:  # noqa: N802
        self._filter_text = text.strip()
        self._rebuild_from_variants(self._cached_variants)

    def build_tree(self, variants: list[tuple[object, str, int]]) -> None:
        self._cached_variants = variants
        self._rebuild_from_variants(variants)

    def _rebuild_from_variants(self, variants: list[tuple[object, str, int]]) -> None:
        self.beginResetModel()

        kw = self._filter_text.lower()
        groups: dict[str, list[_CacheTreeNode]] = {}

        for var, cache_path, status in variants:
            pkg_name = str(var.name)
            if kw and kw not in pkg_name.lower():
                continue

            var_node = _CacheTreeNode(
                node_type="variant",
                label=_build_variant_display(var),
                package_name=pkg_name,
                variant_display=_build_variant_display(var),
                status_code=status,
                status_label=STATUS_LABELS.get(status, f"Unknown ({status})"),
                source_path=str(var.root),
                cache_path=cache_path,
                handle_json=_variant_handle_json(var),
            )
            groups.setdefault(pkg_name, []).append(var_node)

        root = _CacheTreeNode(node_type="root", label="")
        for pkg_name in sorted(groups.keys()):
            children = groups[pkg_name]
            summary = _compute_package_status_summary(children)
            pkg_node = _CacheTreeNode(
                node_type="package",
                label=f"{pkg_name} ({len(children)})",
                package_name=pkg_name,
                status_label=summary,
                parent=root,
                children=children,
            )
            for child in children:
                child.parent = pkg_node
            root.children.append(pkg_node)

        self._root = root
        self.endResetModel()

    def package_names(self) -> list[str]:
        return [child.package_name for child in self._root.children]

    def variants_for_package(self, package_name: str) -> list[_CacheTreeNode]:
        for child in self._root.children:
            if child.package_name == package_name:
                return child.children
        return []


@QmlElement
class PackageCacheController(QObject):
    cachePathChanged = Signal()
    cacheEnabledChanged = Signal()
    loadingChanged = Signal()
    totalVariantsChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._model = CachedVariantTreeModel(self)
        self._loading = False
        self._total_variants = 0
        self._thread_pool = QThreadPool.globalInstance()
        self._latest_variants: list[tuple[object, str, int]] = []

    @Property(QObject, constant=True)
    def variantModel(self) -> CachedVariantTreeModel:  # noqa: N802
        return self._model

    @Property(str, notify=cachePathChanged)
    def cachePath(self) -> str:  # noqa: N802
        return self._resolve_cache_path()

    @Property(bool, notify=cacheEnabledChanged)
    def cacheEnabled(self) -> bool:  # noqa: N802
        return AppSettings.current().package_cache.enabled

    @Property(bool, notify=loadingChanged)
    def isLoading(self) -> bool:  # noqa: N802
        return self._loading

    @Property(str, constant=True)
    def cachePathPlaceholder(self) -> str:  # noqa: N802
        return str(default_rez_package_caches_dir())

    @Property(int, notify=totalVariantsChanged)
    def totalVariants(self) -> int:  # noqa: N802
        return self._total_variants

    @Slot()
    def refresh(self) -> None:
        if self._loading:
            return
        self._loading = True
        self.loadingChanged.emit()

        cache_path = self._resolve_cache_path()
        worker = _CacheRefreshWorker(cache_path)
        worker.signals.finished.connect(self._on_refresh_finished)
        self._thread_pool.start(worker)

    @Slot(str, result=bool)
    def deleteVariant(self, handle_json: str) -> bool:  # noqa: N802
        cache_path = self._resolve_cache_path()
        try:
            handle_dict = json.loads(handle_json)
            remove_cached_variant(cache_path, handle_dict)
            self.refresh()
            return True
        except (json.JSONDecodeError, RezCacheOperationError):
            return False

    @Slot(str, result=bool)
    def deletePackage(self, package_name: str) -> bool:  # noqa: N802
        variants = self._model.variants_for_package(package_name)
        if not variants:
            return False

        cache_path = self._resolve_cache_path()
        errors = 0
        for var_node in variants:
            try:
                handle_dict = json.loads(var_node.handle_json)
                remove_cached_variant(cache_path, handle_dict)
            except (json.JSONDecodeError, RezCacheOperationError):
                errors += 1

        self.refresh()
        return errors == 0

    @Slot(str, result=bool)
    def revealInExplorer(self, path: str) -> bool:  # noqa: N802
        target = Path(path)
        if not target.exists():
            return False
        return QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    def _resolve_cache_path(self) -> str:
        settings = AppSettings.current()
        path_str = settings.package_cache.path.strip()
        if path_str:
            return str(Path(path_str).resolve())
        return str(default_rez_package_caches_dir())

    def _on_refresh_finished(self, result: object) -> None:
        self._loading = False
        self.loadingChanged.emit()

        if isinstance(result, Exception):
            self._model.build_tree([])
            return

        if isinstance(result, list):
            self._latest_variants = result
            self._model.build_tree(result)

        self._total_variants = sum(len(pkg.children) for pkg in self._model._root.children)
        self.totalVariantsChanged.emit()
        self.cachePathChanged.emit()
        self.cacheEnabledChanged.emit()
