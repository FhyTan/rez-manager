"""Python-backed QML list models for the main window."""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QByteArray,
    QModelIndex,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor
from PySide6.QtQml import QmlElement

from rez_manager.adapter.storage import list_contexts, list_projects, load_settings
from rez_manager.models.rez_context import ContextInfo

QML_IMPORT_NAME = "RezManager"
QML_IMPORT_MAJOR_VERSION = 1

_PROJECT_COLORS = (
    "#5F83FF",
    "#4DB880",
    "#D98A38",
    "#8A58D8",
    "#4CB9C4",
    "#E05D8F",
)


def _project_color(name: str) -> str:
    if not name:
        return _PROJECT_COLORS[0]
    return _PROJECT_COLORS[sum(ord(char) for char in name) % len(_PROJECT_COLORS)]


class _BaseListModel(QAbstractListModel):
    countChanged = Signal()
    revisionChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._items: list[object] = []
        self._revision = 0

    def _reset_items(self, items: Sequence[object]) -> None:
        self.beginResetModel()
        self._items = list(items)
        self._revision += 1
        self.endResetModel()
        self.countChanged.emit()
        self.revisionChanged.emit()

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return self.rowCount()

    @Property(int, notify=revisionChanged)
    def revision(self) -> int:
        return self._revision

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._items)


@QmlElement
class ProjectListModel(_BaseListModel):
    NameRole = Qt.UserRole + 1
    AvatarColorRole = Qt.UserRole + 2

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.reload()

    def roleNames(self) -> dict[int, QByteArray]:  # noqa: N802
        return {
            self.NameRole: QByteArray(b"name"),
            self.AvatarColorRole: QByteArray(b"avatarColor"),
        }

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # noqa: ANN201
        if not index.isValid() or index.row() < 0 or index.row() >= len(self._items):
            return None
        project = self._items[index.row()]
        if role == self.NameRole:
            return project.name
        if role == self.AvatarColorRole:
            return QColor(_project_color(project.name))
        return None

    @Slot()
    def reload(self) -> None:
        settings = load_settings()
        self._reset_items(list_projects(settings))

    @Slot(int, result="QVariantMap")
    def get(self, index: int) -> dict[str, object]:
        if index < 0 or index >= len(self._items):
            return {}
        project = self._items[index]
        return {
            "name": project.name,
            "avatarColor": _project_color(project.name),
        }

    @Property("QVariantList", notify=_BaseListModel.countChanged)
    def projectNames(self) -> list[str]:
        return [project.name for project in self._items]


@QmlElement
class RezContextListModel(_BaseListModel):
    ProjectRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    DescriptionRole = Qt.UserRole + 3
    LaunchTargetRole = Qt.UserRole + 4
    PackagesRole = Qt.UserRole + 5

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.reload()

    def roleNames(self) -> dict[int, QByteArray]:  # noqa: N802
        return {
            self.ProjectRole: QByteArray(b"project"),
            self.NameRole: QByteArray(b"name"),
            self.DescriptionRole: QByteArray(b"description"),
            self.LaunchTargetRole: QByteArray(b"launchTarget"),
            self.PackagesRole: QByteArray(b"packages"),
        }

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # noqa: ANN201
        if not index.isValid() or index.row() < 0 or index.row() >= len(self._items):
            return None
        context = self._items[index.row()]
        payload = self._context_payload(context)

        if role == self.ProjectRole:
            return payload["project"]
        if role == self.NameRole:
            return payload["name"]
        if role == self.DescriptionRole:
            return payload["description"]
        if role == self.LaunchTargetRole:
            return payload["launchTarget"]
        if role == self.PackagesRole:
            return payload["packages"]
        return None

    @Slot()
    def reload(self) -> None:
        settings = load_settings()
        self._reset_items(list_contexts(settings))

    @Slot(int, result="QVariantMap")
    def get(self, index: int) -> dict[str, object]:
        if index < 0 or index >= len(self._items):
            return {}
        return self._context_payload(self._items[index])

    @Slot(str, result="QVariantList")
    def filteredContexts(self, project_name: str) -> list[dict[str, object]]:  # noqa: N802
        return [
            self._context_payload(context)
            for context in self._items
            if context.project_name == project_name
        ]

    @Slot(str, result=int)
    def contextCountFor(self, project_name: str) -> int:  # noqa: N802
        return sum(1 for context in self._items if context.project_name == project_name)

    def _context_payload(self, context: ContextInfo) -> dict[str, object]:
        return {
            "project": context.project_name,
            "name": context.name,
            "description": context.description,
            "launchTarget": context.launch_target,
            "packages": ",".join(context.packages),
        }
