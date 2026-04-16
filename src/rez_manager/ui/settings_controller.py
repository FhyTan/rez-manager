"""QML-facing controller for application settings."""

from __future__ import annotations

import ntpath
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtQml import QmlElement

from rez_manager.models.settings import AppSettings
from rez_manager.persistence.settings_store import read_settings_file, write_settings_file
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
        try:
            settings = self._build_settings(package_repositories, contexts_location)
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

    @Slot(str, result=str)
    def normalizeRepositoryPath(self, value: str) -> str:  # noqa: N802
        return _normalize_repository_path(value)

    @Slot(str, result=str)
    def repositoryIdentity(self, value: str) -> str:  # noqa: N802
        normalized = _normalize_repository_path(value)
        return ntpath.normcase(normalized) if normalized else ""

    @Slot(str, result=bool)
    def importFromFile(self, path: str) -> bool:  # noqa: N802
        file_path = self.pathFromUrl(path).strip()
        if not file_path:
            report_ui_error("Settings file path is required.")
            return False

        try:
            loaded_settings = read_settings_file(file_path)
            settings = self._build_settings(
                loaded_settings.package_repositories,
                loaded_settings.contexts_location,
            )
            settings.save()
        except (OSError, TypeError, ValueError) as exc:
            report_ui_error(str(exc))
            return False

        self._apply_settings(settings)
        clear_ui_error()
        return True

    @Slot("QVariantList", str, str, result=bool)
    def exportToFile(
        self,
        package_repositories: list[str],
        contexts_location: str,
        path: str,
    ) -> bool:  # noqa: N802
        file_path = self.pathFromUrl(path).strip()
        if not file_path:
            report_ui_error("Settings file path is required.")
            return False

        try:
            settings = self._build_settings(package_repositories, contexts_location)
            settings.save()
            self._apply_settings(settings)
            write_settings_file(settings, file_path)
        except (OSError, TypeError, ValueError) as exc:
            report_ui_error(str(exc))
            return False

        clear_ui_error()
        return True

    @Slot(str, result=bool)
    def revealInFileExplorer(self, path: str) -> bool:  # noqa: N802
        normalized_path = _normalize_repository_path(self.pathFromUrl(path))
        if not normalized_path:
            report_ui_error("Repository path is required.")
            return False

        target_path = Path(normalized_path)
        if not target_path.exists():
            report_ui_error(f"Path does not exist: {target_path}")
            return False

        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(target_path))):
            report_ui_error(f"Failed to reveal path in File Explorer: {target_path}")
            return False

        clear_ui_error()
        return True

    def _apply_settings(self, settings: AppSettings) -> None:
        repositories_changed = self._settings.package_repositories != settings.package_repositories
        location_changed = self._settings.contexts_location != settings.contexts_location
        self._settings = settings
        if repositories_changed:
            self.packageRepositoriesChanged.emit()
        if location_changed:
            self.contextsLocationChanged.emit()

    def _build_settings(
        self,
        package_repositories: list[str],
        contexts_location: str,
    ) -> AppSettings:
        location = str(contexts_location).strip()
        if not location:
            raise ValueError("Contexts location is required.")

        return AppSettings(
            package_repositories=_normalize_repository_paths(package_repositories),
            contexts_location=location,
        )


def _normalize_repository_path(value: str) -> str:
    trimmed = str(value).strip()
    if not trimmed:
        return ""
    return ntpath.normpath(trimmed)


def _normalize_repository_paths(values: list[str]) -> list[str]:
    normalized_paths: list[str] = []
    seen_keys: set[str] = set()

    for value in values:
        normalized = _normalize_repository_path(value)
        if not normalized:
            continue

        key = ntpath.normcase(normalized)
        if key in seen_keys:
            continue

        seen_keys.add(key)
        normalized_paths.append(normalized)

    return normalized_paths
