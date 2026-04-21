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
from rez_manager.ui.error_hub import clear_ui_error, report_ui_error

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


def _sorted_row(items: Sequence[Project] | Sequence[RezContext], name: str) -> int:
    normalized_name = name.lower()
    for index, item in enumerate(items):
        if item.name.lower() > normalized_name:
            return index
    return len(items)


@QmlElement
class ProjectListModel(QAbstractListModel):
    projectNamesChanged = Signal()
    NameRole = Qt.ItemDataRole.UserRole + 1
    AvatarColorRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._items: list[Project] = []
        self.reload()

    def _reset_items(self, items: Sequence[Project]) -> None:
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()
        self.projectNamesChanged.emit()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._items)

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
        clear_ui_error()

    @Slot(int, result="QVariantMap")
    def get(self, index: int) -> dict[str, object]:
        if index < 0 or index >= len(self._items):
            return {}
        project = self._items[index]
        return {
            "name": project.name,
            "avatarColor": _project_color(project.name),
        }

    @Property("QVariantList", notify=projectNamesChanged)
    def projectNames(self) -> list[str]:
        return [project.name for project in self._items]

    def get_project(self, name: str) -> Project | None:
        for project in self._items:
            if project.name == name:
                return project
        return None

    def _find_project_row(self, name: str) -> int:
        for index, project in enumerate(self._items):
            if project.name == name:
                return index
        return -1

    def _insert_project(self, project: Project) -> None:
        row = _sorted_row(self._items, project.name)
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.insert(row, project)
        self.endInsertRows()
        self.projectNamesChanged.emit()

    def _remove_project(self, row: int) -> Project:
        self.beginRemoveRows(QModelIndex(), row, row)
        project = self._items.pop(row)
        self.endRemoveRows()
        self.projectNamesChanged.emit()
        return project

    def _project_missing_message(self, name: str) -> str:
        return f"Project '{name}' is no longer available. Refresh the list and try again."

    def _load_project_for_action(self, name: str) -> Project | None:
        try:
            loaded_project = Project.load(name)
        except (OSError, ValueError):
            report_ui_error(self._project_missing_message(name))
            return None
        return self.get_project(name) or loaded_project

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
    def ensureProjectExists(self, name: str) -> bool:  # noqa: N802
        if self._load_project_for_action(name) is None:
            return False
        clear_ui_error()
        return True

    @Slot(str, result=bool)
    def createProject(self, name: str) -> bool:  # noqa: N802
        try:
            project = Project.create(name)
        except (OSError, ValueError) as exc:
            report_ui_error(str(exc))
            return False
        self._insert_project(project)
        clear_ui_error()
        return True

    @Slot(str, str, result=bool)
    def renameProject(self, current_name: str, new_name: str) -> bool:  # noqa: N802
        project = self._load_project_for_action(current_name)
        if project is None:
            return False
        row = self._find_project_row(current_name)
        try:
            project.rename(new_name)
        except (OSError, ValueError) as exc:
            report_ui_error(str(exc))
            return False
        if row >= 0:
            self._remove_project(row)
        self._insert_project(project)
        clear_ui_error()
        return True

    @Slot(str, str, result=bool)
    def duplicateProject(self, source_name: str, target_name: str) -> bool:  # noqa: N802
        project = self._load_project_for_action(source_name)
        if project is None:
            return False
        try:
            duplicated = project.duplicate(target_name)
        except (OSError, ValueError) as exc:
            report_ui_error(str(exc))
            return False
        self._insert_project(duplicated)
        clear_ui_error()
        return True

    @Slot(str, result=bool)
    def deleteProject(self, name: str) -> bool:  # noqa: N802
        project = self._load_project_for_action(name)
        if project is None:
            return False
        try:
            project.delete()
        except (OSError, ValueError) as exc:
            report_ui_error(str(exc))
            return False
        row = self._find_project_row(name)
        if row >= 0:
            self._remove_project(row)
        clear_ui_error()
        return True


@QmlElement
class RezContextListModel(QAbstractListModel):
    contextsChanged = Signal()
    projectModelChanged = Signal()
    ProjectRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    DescriptionRole = Qt.UserRole + 3
    LaunchTargetRole = Qt.UserRole + 4
    PackagesRole = Qt.UserRole + 5
    PackageRequestsRole = Qt.UserRole + 6
    CustomCommandRole = Qt.UserRole + 7

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._items: list[RezContext] = []
        self._project_model: ProjectListModel | None = None
        self._current_project_name = ""
        self.reload()

    def _reset_items(self, items: Sequence[RezContext]) -> None:
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()
        self.contextsChanged.emit()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._items)

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
            self.PackageRequestsRole: QByteArray(b"packageRequests"),
            self.CustomCommandRole: QByteArray(b"customCommand"),
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
        if role == self.PackageRequestsRole:
            return payload["packageRequests"]
        if role == self.CustomCommandRole:
            return payload["customCommand"]
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

    @Property("QVariantList", notify=contextsChanged)
    def contexts(self) -> list[dict[str, object]]:
        return [self._context_payload(context) for context in self._items]

    @Property(int, notify=contextsChanged)
    def contextCount(self) -> int:  # noqa: N802
        return len(self._items)

    @Slot(str, result="QVariantList")
    def filteredContexts(self, project_name: str) -> list[dict[str, object]]:  # noqa: N802
        if project_name != self._current_project_name:
            return []
        return self.contexts

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

    def _context_roles(self) -> list[int]:
        return [
            self.ProjectRole,
            self.NameRole,
            self.DescriptionRole,
            self.LaunchTargetRole,
            self.PackagesRole,
            self.PackageRequestsRole,
            self.CustomCommandRole,
        ]

    def _bind_context_project(self, context: RezContext) -> RezContext:
        if self._project_model is None:
            return context
        project = self._project_model.get_project(context.project_name)
        if project is not None:
            context.project = project
        return context

    def _find_context_row(self, project_name: str, context_name: str) -> int:
        for index, context in enumerate(self._items):
            if context.project_name == project_name and context.name == context_name:
                return index
        return -1

    def _insert_context(self, context: RezContext) -> None:
        row = _sorted_row(self._items, context.name)
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.insert(row, context)
        self.endInsertRows()
        self.contextsChanged.emit()

    def _remove_context(self, row: int) -> RezContext:
        self.beginRemoveRows(QModelIndex(), row, row)
        context = self._items.pop(row)
        self.endRemoveRows()
        self.contextsChanged.emit()
        return context

    def _update_context(self, row: int, context: RezContext) -> None:
        self._items[row] = context
        model_index = self.index(row, 0)
        self.dataChanged.emit(model_index, model_index, self._context_roles())
        self.contextsChanged.emit()

    def _context_missing_message(self, project_name: str, context_name: str) -> str:
        return (
            f"Context '{context_name}' in project '{project_name}' is no longer available. "
            "Refresh the list and try again."
        )

    def _load_context_for_action(self, project_name: str, context_name: str) -> RezContext | None:
        try:
            loaded_context = RezContext.load(project_name, context_name)
        except (OSError, ValueError):
            report_ui_error(self._context_missing_message(project_name, context_name))
            return None

        row = self._find_context_row(project_name, context_name)
        if row >= 0:
            return self._items[row]
        return self._bind_context_project(loaded_context)

    def _cached_project(self, project_name: str) -> Project | None:
        if self._project_model is None:
            return None
        return self._project_model.get_project(project_name)

    def _insert_cached_context(self, context: RezContext) -> None:
        project = self._cached_project(context.project_name)
        if project is None or project.contexts is None:
            return
        context.project = project
        row = _sorted_row(project.contexts, context.name)
        project.contexts.insert(row, context)

    def _find_cached_context_row(self, project_name: str, context_name: str) -> int:
        project = self._cached_project(project_name)
        if project is None or project.contexts is None:
            return -1

        for index, cached_context in enumerate(project.contexts):
            if cached_context.name == context_name:
                return index
        return -1

    def _replace_cached_context(
        self,
        project_name: str,
        original_context_name: str,
        context: RezContext,
    ) -> None:
        project = self._cached_project(project_name)
        if project is None or project.contexts is None:
            return

        for index, cached_context in enumerate(project.contexts):
            if cached_context.name == original_context_name:
                context.project = project
                project.contexts[index] = context
                return

    def _remove_cached_context(self, project_name: str, context_name: str) -> None:
        row = self._find_cached_context_row(project_name, context_name)
        if row >= 0:
            self._remove_cached_context_row(project_name, row)

    def _remove_cached_context_row(self, project_name: str, row: int) -> None:
        project = self._cached_project(project_name)
        if project is None or project.contexts is None:
            return
        if 0 <= row < len(project.contexts):
            project.contexts.pop(row)

    @Slot(str, str, result=bool)
    def ensureContextExists(self, project_name: str, context_name: str) -> bool:  # noqa: N802
        if self._load_context_for_action(project_name, context_name) is None:
            return False
        clear_ui_error()
        return True

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
                current_row = self._find_context_row(original_project_name, original_context_name)
                cached_row = self._find_cached_context_row(
                    original_project_name,
                    original_context_name,
                )
                context = self._load_context_for_action(
                    original_project_name,
                    original_context_name,
                )
                if context is None:
                    return False
                updated_context = self._bind_context_project(context.update(project_name, meta))
            else:
                current_row = -1
                cached_row = -1
                if self._project_model is not None and not self._project_model.ensureProjectExists(
                    project_name
                ):
                    return False
                updated_context = self._bind_context_project(RezContext.create(project_name, meta))
        except (OSError, TypeError, ValueError) as exc:
            report_ui_error(str(exc))
            return False

        if original_project_name and original_context_name:
            if original_project_name == updated_context.project_name and (
                original_context_name == updated_context.name
            ):
                self._replace_cached_context(project_name, original_context_name, updated_context)
                if self._current_project_name == project_name:
                    if current_row >= 0:
                        self._update_context(current_row, updated_context)
            else:
                if cached_row >= 0:
                    self._remove_cached_context_row(original_project_name, cached_row)
                self._insert_cached_context(updated_context)
                if self._current_project_name == original_project_name:
                    if current_row >= 0:
                        self._remove_context(current_row)
                if self._current_project_name == updated_context.project_name:
                    self._insert_context(updated_context)
        else:
            self._insert_cached_context(updated_context)
            if self._current_project_name == updated_context.project_name:
                self._insert_context(updated_context)

        clear_ui_error()
        return True

    @Slot(str, str, str, str, result=bool)
    def duplicateContext(  # noqa: N802
        self,
        source_project_name: str,
        source_context_name: str,
        target_project_name: str,
        target_context_name: str,
    ) -> bool:
        source_context = self._load_context_for_action(source_project_name, source_context_name)
        if source_context is None:
            return False
        if self._project_model is not None and not self._project_model.ensureProjectExists(
            target_project_name
        ):
            return False
        try:
            duplicated_context = self._bind_context_project(
                source_context.duplicate(
                    target_project_name,
                    target_context_name,
                )
            )
        except (OSError, ValueError) as exc:
            report_ui_error(str(exc))
            return False
        self._insert_cached_context(duplicated_context)
        if self._current_project_name == duplicated_context.project_name:
            self._insert_context(duplicated_context)
        clear_ui_error()
        return True

    @Slot(str, str, result=bool)
    def deleteContext(self, project_name: str, context_name: str) -> bool:  # noqa: N802
        context = self._load_context_for_action(project_name, context_name)
        if context is None:
            return False
        try:
            context.delete()
        except (OSError, ValueError) as exc:
            report_ui_error(str(exc))
            return False
        self._remove_cached_context(project_name, context_name)
        if self._current_project_name == project_name:
            row = self._find_context_row(project_name, context_name)
            if row >= 0:
                self._remove_context(row)
        clear_ui_error()
        return True

    def _load_project(self, project_name: str, *, refresh: bool = False) -> bool:
        self._current_project_name = project_name
        if not project_name:
            self._reset_items([])
            clear_ui_error()
            return True

        project = self._resolve_project(project_name)
        if project is None:
            self._reset_items([])
            clear_ui_error()
            return False

        try:
            if refresh or project.contexts is None:
                project.load_contexts()
            self._reset_items(project.contexts or [])
        except (OSError, TypeError, ValueError) as exc:
            self._reset_items([])
            report_ui_error(str(exc))
            return False

        clear_ui_error()
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
