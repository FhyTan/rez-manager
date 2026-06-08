"""QML-facing controller for application settings."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtQml import QmlElement

from rez_manager.adapter.utils import apply_settings_to_rez
from rez_manager.models.settings import AppSettings, GeneralSettings
from rez_manager.persistence.app_paths import (
    default_rez_contexts_dir,
    default_rez_package_caches_dir,
)
from rez_manager.persistence.settings_store import read_settings_file, write_settings_file
from rez_manager.ui.error_hub import clear_ui_error, report_ui_error

QML_IMPORT_NAME = "RezManager"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class AppSettingsController(QObject):
    packageRepositoriesChanged = Signal()
    contextsLocationChanged = Signal()
    packageCacheEnabledChanged = Signal()
    packageCachePathChanged = Signal()
    packageCacheSpaceBufferChanged = Signal()
    packageCacheMaxVariantDaysChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._settings = AppSettings()
        self.reload()

    # ── Contexts Location ────────────────────────────────────

    @Property(str, notify=contextsLocationChanged)
    def contextsLocation(self) -> str:  # noqa: N802
        return self._settings.general.contexts_location

    @contextsLocation.setter
    def contextsLocation(self, value: str) -> None:  # noqa: N802
        if self._settings.general.contexts_location != value:
            self._settings.general.contexts_location = str(value)
            self.contextsLocationChanged.emit()

    @Property(str, constant=True)
    def contextsLocationPlaceholder(self) -> str:  # noqa: N802
        return str(default_rez_contexts_dir())

    # ── Package Repositories ──────────────────────────────────

    @Property("QVariantList", notify=packageRepositoriesChanged)
    def packageRepositories(self) -> list[str]:  # noqa: N802
        return list(self._settings.general.package_repositories)

    # ── Package Cache ────────────────────────────────────────

    @Property(bool, notify=packageCacheEnabledChanged)
    def packageCacheEnabled(self) -> bool:  # noqa: N802
        return self._settings.package_cache.enabled

    @packageCacheEnabled.setter
    def packageCacheEnabled(self, value: bool) -> None:  # noqa: N802
        if self._settings.package_cache.enabled != value:
            self._settings.package_cache.enabled = value
            self.packageCacheEnabledChanged.emit()

    @Property(str, notify=packageCachePathChanged)
    def packageCachePath(self) -> str:  # noqa: N802
        return self._settings.package_cache.path

    @packageCachePath.setter
    def packageCachePath(self, value: str) -> None:  # noqa: N802
        normalized = value.strip()
        if self._settings.package_cache.path != normalized:
            self._settings.package_cache.path = normalized
            self.packageCachePathChanged.emit()

    @Property(str, constant=True)
    def packageCachePathPlaceholder(self) -> str:  # noqa: N802
        return str(default_rez_package_caches_dir())

    @Property(int, notify=packageCacheSpaceBufferChanged)
    def packageCacheSpaceBufferMb(self) -> int:  # noqa: N802
        return self._settings.package_cache.space_buffer_mb

    @packageCacheSpaceBufferMb.setter
    def packageCacheSpaceBufferMb(self, value: int) -> None:  # noqa: N802
        if self._settings.package_cache.space_buffer_mb != value:
            self._settings.package_cache.space_buffer_mb = value
            self.packageCacheSpaceBufferChanged.emit()

    @Property(int, notify=packageCacheMaxVariantDaysChanged)
    def packageCacheMaxVariantDays(self) -> int:  # noqa: N802
        return self._settings.package_cache.max_variant_days

    @packageCacheMaxVariantDays.setter
    def packageCacheMaxVariantDays(self, value: int) -> None:  # noqa: N802
        if self._settings.package_cache.max_variant_days != value:
            self._settings.package_cache.max_variant_days = value
            self.packageCacheMaxVariantDaysChanged.emit()

    # ── Public slots ─────────────────────────────────────────

    @Slot()
    def reload(self) -> None:
        self._apply_settings(AppSettings.load())
        clear_ui_error()

    @Slot("QVariantList")
    def setPackageRepositories(self, repos: list[str]) -> None:  # noqa: N802
        self._settings.general.package_repositories = [str(r) for r in repos]
        self.packageRepositoriesChanged.emit()

    @Slot(result=bool)
    def save(self) -> bool:
        try:
            self._normalize_repositories()
            self._settings.save()
        except (OSError, TypeError, ValueError) as exc:
            report_ui_error(str(exc))
            return False

        apply_settings_to_rez(self._settings)
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
        return _normcase(normalized) if normalized else ""

    @Slot(str, result=bool)
    def importFromFile(self, path: str) -> bool:  # noqa: N802
        file_path = self.pathFromUrl(path).strip()
        if not file_path:
            report_ui_error("Settings file path is required.")
            return False

        try:
            loaded_settings = read_settings_file(file_path)
            self._apply_settings(loaded_settings)
            self._normalize_repositories()
            self._settings.save()
        except (OSError, TypeError, ValueError) as exc:
            report_ui_error(str(exc))
            return False

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
            location = str(contexts_location).strip()
            settings = AppSettings(
                general=GeneralSettings(
                    package_repositories=_normalize_repository_paths(package_repositories),
                    contexts_location=location,
                ),
                package_cache=self._settings.package_cache,
            )
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

    # ── Internal helpers ─────────────────────────────────────

    def _apply_settings(self, settings: AppSettings) -> None:
        repos_changed = (
            self._settings.general.package_repositories != settings.general.package_repositories
        )
        loc_changed = self._settings.general.contexts_location != settings.general.contexts_location
        prev_cache = self._settings.package_cache
        next_cache = settings.package_cache
        cache_enabled_changed = prev_cache.enabled != next_cache.enabled
        cache_path_changed = prev_cache.path != next_cache.path
        cache_buffer_changed = prev_cache.space_buffer_mb != next_cache.space_buffer_mb
        cache_variant_changed = prev_cache.max_variant_days != next_cache.max_variant_days

        self._settings = settings

        apply_settings_to_rez(self._settings)

        if repos_changed:
            self.packageRepositoriesChanged.emit()
        if loc_changed:
            self.contextsLocationChanged.emit()
        if cache_enabled_changed:
            self.packageCacheEnabledChanged.emit()
        if cache_path_changed:
            self.packageCachePathChanged.emit()
        if cache_buffer_changed:
            self.packageCacheSpaceBufferChanged.emit()
        if cache_variant_changed:
            self.packageCacheMaxVariantDaysChanged.emit()

    def _normalize_repositories(self) -> None:
        self._settings.general.package_repositories = _normalize_repository_paths(
            self._settings.general.package_repositories
        )


def _normcase(value: str) -> str:
    """Normalize path case for cross-platform deduplication."""
    import ntpath  # noqa: PLC0415

    return ntpath.normcase(value)


def _normalize_repository_path(value: str) -> str:
    trimmed = str(value).strip()
    if not trimmed:
        return ""
    return str(Path(trimmed))


def _normalize_repository_paths(values: list[str]) -> list[str]:
    normalized_paths: list[str] = []
    seen_keys: set[str] = set()

    for value in values:
        normalized = _normalize_repository_path(value)
        if not normalized:
            continue

        key = _normcase(normalized)
        if key in seen_keys:
            continue

        seen_keys.add(key)
        normalized_paths.append(normalized)

    return normalized_paths
