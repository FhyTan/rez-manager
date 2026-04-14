"""Python-backed QML list models for the main window."""

from __future__ import annotations

from collections.abc import Sequence

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
from PySide6.QtGui import QColor
from PySide6.QtQml import QmlElement

from rez_manager.models.project import Project
from rez_manager.models.rez_context import ContextMeta, LaunchTarget, RezContext

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
    errorChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._items: list[object] = []
        self._revision = 0
        self._last_error = ""

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

    @Property(str, notify=errorChanged)
    def lastError(self) -> str:  # noqa: N802
        return self._last_error

    def _set_error(self, message: str) -> None:
        if self._last_error != message:
            self._last_error = message
            self.errorChanged.emit()

    def _clear_error(self) -> None:
        self._set_error("")

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._items)


@QmlElement
class ProjectListModel(_BaseListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    AvatarColorRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.reload()

    def roleNames(self) -> dict[int, QByteArray]:  # noqa: N802
        return {
            self.NameRole: QByteArray(b"name"),
            self.AvatarColorRole: QByteArray(b"avatarColor"),
        }

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: ANN201
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
        self._reset_items(Project.all())
        self._clear_error()

    @Slot(int, result="QVariantMap")
    def get(self, index: int) -> dict[str, object]:
        if index < 0 or index >= len(self._items):
            return {}
        project = self._items[index]
        return {
            "name": project.name,
            "avatarColor": _project_color(project.name),
        }

    @Property("QVariantList", notify="countChanged")
    def projectNames(self) -> list[str]:
        return [project.name for project in self._items]

    def get_project(self, name: str) -> Project | None:
        for project in self._items:
            if project.name == name:
                return project
        return None

    def reload_project_contexts(self, name: str) -> None:
        project = self.get_project(name)
        if project is not None and project.contexts is not None:
            project.load_contexts()

    @Slot(str, result=int)
    def indexOfProject(self, name: str) -> int:  # noqa: N802
        for index, project in enumerate(self._items):
            if project.name == name:
                return index
        return -1

    @Slot(str, result=bool)
    def createProject(self, name: str) -> bool:  # noqa: N802
        try:
            Project.create(name)
        except (OSError, ValueError) as exc:
            self._set_error(str(exc))
            return False
        self.reload()
        return True

    @Slot(str, str, result=bool)
    def renameProject(self, current_name: str, new_name: str) -> bool:  # noqa: N802
        try:
            Project.load(current_name).rename(new_name)
        except (OSError, ValueError) as exc:
            self._set_error(str(exc))
            return False
        self.reload()
        return True

    @Slot(str, str, result=bool)
    def duplicateProject(self, source_name: str, target_name: str) -> bool:  # noqa: N802
        try:
            Project.load(source_name).duplicate(target_name)
        except (OSError, ValueError) as exc:
            self._set_error(str(exc))
            return False
        self.reload()
        return True

    @Slot(str, result=bool)
    def deleteProject(self, name: str) -> bool:  # noqa: N802
        try:
            Project.load(name).delete()
        except (OSError, ValueError) as exc:
            self._set_error(str(exc))
            return False
        self.reload()
        return True


@QmlElement
class RezContextListModel(_BaseListModel):
    projectModelChanged = Signal()
    ProjectRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    DescriptionRole = Qt.UserRole + 3
    LaunchTargetRole = Qt.UserRole + 4
    PackagesRole = Qt.UserRole + 5

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._project_model: ProjectListModel | None = None
        self._current_project_name = ""
        self.reload()

    @Property(QObject, notify=projectModelChanged)
    def projectModel(self) -> QObject | None:  # noqa: N802
        return self._project_model

    @projectModel.setter
    def projectModel(self, model: QObject | None) -> None:  # noqa: N802
        typed_model = model if isinstance(model, ProjectListModel) else None
        if self._project_model is typed_model:
            return
        self._project_model = typed_model
        self.projectModelChanged.emit()
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
        self._load_project(self._current_project_name, refresh=True)

    @Slot(str, result=bool)
    def loadProject(self, project_name: str) -> bool:  # noqa: N802
        return self._load_project(project_name)

    @Slot(int, result="QVariantMap")
    def get(self, index: int) -> dict[str, object]:
        if index < 0 or index >= len(self._items):
            return {}
        return self._context_payload(self._items[index])

    @Slot(str, result="QVariantList")
    def filteredContexts(self, project_name: str) -> list[dict[str, object]]:  # noqa: N802
        if project_name != self._current_project_name:
            return []
        return [
            self._context_payload(context)
            for context in self._items
        ]

    def _context_payload(self, context: RezContext) -> dict[str, object]:
        return {
            "project": context.project_name,
            "name": context.name,
            "description": context.description,
            "launchTarget": context.launch_target,
            "packages": ",".join(context.packages),
            "packageRequests": list(context.packages),
            "customCommand": context.meta.custom_command or "",
        }

    @Slot(str, str, str, str, str, str, str, "QVariantList", result=bool)
    def saveContext(  # noqa: N802
        self,
        original_project_name: str,
        original_context_name: str,
        project_name: str,
        name: str,
        description: str,
        launch_target: str,
        custom_command: str,
        packages: list[str],
    ) -> bool:
        try:
            if bool(original_project_name) != bool(original_context_name):
                raise ValueError(
                    "Original project and context names must both be provided "
                    "when editing a context"
                )
            meta = ContextMeta(
                name=name,
                description=description.strip(),
                launch_target=LaunchTarget(launch_target),
                custom_command=custom_command.strip() or None,
                packages=[str(package) for package in packages],
            )
            if original_project_name and original_context_name:
                RezContext.load(
                    original_project_name,
                    original_context_name,
                ).update(project_name, meta)
            else:
                RezContext.create(project_name, meta)
        except (OSError, TypeError, ValueError) as exc:
            self._set_error(str(exc))
            return False
        self._reload_project_contexts(original_project_name, project_name)
        self.reload()
        return True

    @Slot(str, str, str, str, result=bool)
    def duplicateContext(  # noqa: N802
        self,
        source_project_name: str,
        source_context_name: str,
        target_project_name: str,
        target_context_name: str,
    ) -> bool:
        try:
            RezContext.load(source_project_name, source_context_name).duplicate(
                target_project_name,
                target_context_name,
            )
        except (OSError, ValueError) as exc:
            self._set_error(str(exc))
            return False
        self._reload_project_contexts(source_project_name, target_project_name)
        self.reload()
        return True

    @Slot(str, str, result=bool)
    def deleteContext(self, project_name: str, context_name: str) -> bool:  # noqa: N802
        try:
            RezContext.load(project_name, context_name).delete()
        except (OSError, ValueError) as exc:
            self._set_error(str(exc))
            return False
        self._reload_project_contexts(project_name)
        self.reload()
        return True

    def _load_project(self, project_name: str, *, refresh: bool = False) -> bool:
        self._current_project_name = project_name
        if not project_name:
            self._reset_items([])
            self._clear_error()
            return True

        project = self._resolve_project(project_name)
        if project is None:
            self._reset_items([])
            self._clear_error()
            return False

        try:
            if refresh or project.contexts is None:
                project.load_contexts()
            self._reset_items(project.contexts or [])
        except (OSError, TypeError, ValueError) as exc:
            self._reset_items([])
            self._set_error(str(exc))
            return False

        self._clear_error()
        return True

    def _resolve_project(self, project_name: str) -> Project | None:
        if not project_name:
            return None
        if self._project_model is not None:
            project = self._project_model.get_project(project_name)
            if project is not None:
                return project
        try:
            return Project.load(project_name)
        except (OSError, ValueError):
            return None

    def _reload_project_contexts(self, *project_names: str) -> None:
        if self._project_model is None:
            return
        for project_name in project_names:
            if project_name:
                self._project_model.reload_project_contexts(project_name)
