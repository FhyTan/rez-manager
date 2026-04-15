"""QML-facing controller for application settings."""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtQml import QmlElement

from rez_manager.models.settings import AppSettings
from rez_manager.ui.error_hub import clear_ui_error, report_ui_error

QML_IMPORT_NAME = "RezManager"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class AppSettingsController(QObject):
    packageRepositoriesChanged = Signal()
    contextsLocationChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._settings = AppSettings.default()
        self.reload()

    @Property("QVariantList", notify="packageRepositoriesChanged")
    def packageRepositories(self) -> list[str]:  # noqa: N802
        return list(self._settings.package_repositories)

    @Property(str, notify="contextsLocationChanged")
    def contextsLocation(self) -> str:  # noqa: N802
        return self._settings.contexts_location

    @Slot()
    def reload(self) -> None:
        self._apply_settings(AppSettings.load())
        clear_ui_error()

    @Slot("QVariantList", str, result=bool)
    def save(self, package_repositories: list[str], contexts_location: str) -> bool:
        repositories = [str(path).strip() for path in package_repositories if str(path).strip()]
        location = contexts_location.strip()

        if not location:
            report_ui_error("Contexts location is required.")
            return False

        try:
            settings = AppSettings(
                package_repositories=repositories,
                contexts_location=location,
            )
            settings.save()
        except (OSError, TypeError, ValueError) as exc:
            report_ui_error(str(exc))
            return False

        self._apply_settings(settings)
        clear_ui_error()
        return True

    @Slot(str, result=str)
    def pathFromUrl(self, value: str) -> str:  # noqa: N802
        url = QUrl(value)
        if url.isLocalFile():
            return url.toLocalFile()
        return value

    def _apply_settings(self, settings: AppSettings) -> None:
        repositories_changed = self._settings.package_repositories != settings.package_repositories
        location_changed = self._settings.contexts_location != settings.contexts_location
        self._settings = settings
        if repositories_changed:
            self.packageRepositoriesChanged.emit()
        if location_changed:
            self.contextsLocationChanged.emit()
