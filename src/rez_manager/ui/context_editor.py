"""QML-facing controller for the context editor dialog — name validation only."""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtQml import QmlElement

from rez_manager.persistence.filesystem import contexts_root_path, normalize_entity_name

QML_IMPORT_NAME = "RezManager"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class ContextEditorController(QObject):
    """Validates context-name availability and invalid characters."""

    nameErrorChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._name_error = ""

    @Property(str, notify=nameErrorChanged)
    def nameError(self) -> str:
        return self._name_error

    @Property(bool, notify=nameErrorChanged)
    def nameAvailable(self) -> bool:
        return self._name_error == ""

    @Slot(str, str, str, str)
    def checkNameAvailability(
        self,
        project_name: str,
        context_name: str,
        original_project_name: str,
        original_context_name: str,
    ) -> None:
        trimmed = context_name.strip()
        if not trimmed:
            self._set_error("Name cannot be empty")
            return

        try:
            normalized = normalize_entity_name(context_name, "Context")
        except ValueError:
            self._set_error("Name contains invalid path characters")
            return

        if (
            original_project_name
            and original_context_name
            and project_name.strip() == original_project_name.strip()
            and normalized == original_context_name.strip()
        ):
            self._set_error("")
            return

        try:
            root = contexts_root_path()
        except ValueError:
            self._set_error("")
            return

        project_path = root / project_name.strip()
        if not project_path.exists():
            self._set_error("")
            return

        context_path = project_path / normalized
        if context_path.exists():
            self._set_error(
                f"A context named '{normalized}' already exists in project '{project_name}'"
            )
        else:
            self._set_error("")

    def _set_error(self, message: str) -> None:
        if self._name_error != message:
            self._name_error = message
            self.nameErrorChanged.emit()
