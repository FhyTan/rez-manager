"""Filesystem-backed state loading."""

from __future__ import annotations

import json
import os
import shutil
import warnings
from json import JSONDecodeError
from pathlib import Path

from platformdirs import user_config_path, user_data_path

from rez_manager.models.project import Project
from rez_manager.models.rez_context import ContextInfo, ContextMeta
from rez_manager.models.settings import AppSettings

APP_NAME = "rez-manager"
SETTINGS_FILE_NAME = "settings.json"
META_FILE_NAME = "meta.json"
CONTEXT_FILE_NAME = "context.rxt"
THUMBNAIL_FILE_NAME = "thumbnail.png"


def app_config_dir() -> Path:
    configured_home = os.environ.get("REZ_MANAGER_HOME")
    if configured_home:
        return Path(configured_home).expanduser()
    return user_config_path(APP_NAME, appauthor=False)


def app_data_dir() -> Path:
    configured_home = os.environ.get("REZ_MANAGER_HOME")
    if configured_home:
        return Path(configured_home).expanduser()
    return user_data_path(APP_NAME, appauthor=False)


def settings_file_path() -> Path:
    return app_config_dir() / SETTINGS_FILE_NAME


def default_settings() -> AppSettings:
    return AppSettings(
        package_repositories=[],
        contexts_location=str(app_data_dir() / "contexts"),
    )


def load_settings() -> AppSettings:
    path = settings_file_path()
    if not path.exists():
        return default_settings()

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (JSONDecodeError, OSError) as exc:
        warnings.warn(
            f"Failed to load settings from {path}: {exc}",
            RuntimeWarning,
            stacklevel=2,
        )
        return default_settings()

    if not isinstance(data, dict):
        warnings.warn(
            f"Failed to load settings from {path}: settings.json must contain a JSON object",
            RuntimeWarning,
            stacklevel=2,
        )
        return default_settings()

    try:
        return AppSettings.from_dict(data)
    except (TypeError, ValueError) as exc:
        warnings.warn(
            f"Failed to validate settings from {path}: {exc}",
            RuntimeWarning,
            stacklevel=2,
        )
        return default_settings()


def save_settings(settings: AppSettings) -> Path:
    path = settings_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as handle:
        json.dump(settings.to_dict(), handle, indent=2, sort_keys=True)
        handle.write("\n")

    return path


def create_project(settings: AppSettings, name: str) -> Project:
    contexts_root = ensure_contexts_root(settings)
    project_name = normalize_entity_name(name, "Project")
    project_dir = contexts_root / project_name
    if project_dir.exists():
        raise ValueError(f"Project '{project_name}' already exists")
    project_dir.mkdir(parents=True, exist_ok=False)
    return Project(name=project_name, contexts_dir=str(project_dir))


def rename_project(settings: AppSettings, current_name: str, new_name: str) -> Project:
    contexts_root = ensure_contexts_root(settings)
    source_dir = contexts_root / normalize_entity_name(current_name, "Project")
    target_name = normalize_entity_name(new_name, "Project")
    target_dir = contexts_root / target_name

    if not source_dir.exists():
        raise ValueError(f"Project '{current_name}' does not exist")
    if str(source_dir) == str(target_dir):
        return Project(name=target_name, contexts_dir=str(target_dir))
    if target_dir.exists() and not _is_same_location(source_dir, target_dir):
        raise ValueError(f"Project '{target_name}' already exists")

    _rename_path(source_dir, target_dir)
    return Project(name=target_name, contexts_dir=str(target_dir))


def duplicate_project(settings: AppSettings, source_name: str, target_name: str) -> Project:
    contexts_root = ensure_contexts_root(settings)
    source_dir = contexts_root / normalize_entity_name(source_name, "Project")
    target_name = normalize_entity_name(target_name, "Project")
    target_dir = contexts_root / target_name

    if not source_dir.exists():
        raise ValueError(f"Project '{source_name}' does not exist")
    if target_dir.exists():
        raise ValueError(f"Project '{target_name}' already exists")

    shutil.copytree(source_dir, target_dir)
    return Project(name=target_name, contexts_dir=str(target_dir))


def delete_project(settings: AppSettings, name: str) -> None:
    contexts_root = ensure_contexts_root(settings)
    project_name = normalize_entity_name(name, "Project")
    project_dir = contexts_root / project_name
    if not project_dir.exists():
        raise ValueError(f"Project '{project_name}' does not exist")
    shutil.rmtree(project_dir)


def save_context(
    settings: AppSettings,
    project_name: str,
    meta: ContextMeta,
    *,
    original_project_name: str | None = None,
    original_context_name: str | None = None,
) -> ContextInfo:
    project_dir = require_project_dir(settings, project_name)
    context_name = normalize_entity_name(meta.name, "Context")
    target_dir = project_dir / context_name
    normalized_meta = ContextMeta(
        name=context_name,
        description=meta.description,
        launch_target=meta.launch_target,
        custom_command=meta.custom_command,
        packages=list(meta.packages),
        thumbnail_path=meta.thumbnail_path,
    )

    if (original_project_name is None) != (original_context_name is None):
        raise ValueError(
            "Original project and context names must both be provided when editing a context"
        )

    if original_project_name is None and original_context_name is None:
        if target_dir.exists():
            raise ValueError(f"Context '{context_name}' already exists in project '{project_name}'")
        target_dir.mkdir(parents=True, exist_ok=False)
        write_context_meta(target_dir, normalized_meta)
        return load_context_info(project_name, target_dir)

    source_dir = require_context_dir(settings, original_project_name, original_context_name)
    if str(source_dir) != str(target_dir):
        if target_dir.exists() and not _is_same_location(source_dir, target_dir):
            raise ValueError(f"Context '{context_name}' already exists in project '{project_name}'")
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        _rename_path(source_dir, target_dir)

    write_context_meta(target_dir, normalized_meta)
    return load_context_info(project_name, target_dir)


def duplicate_context(
    settings: AppSettings,
    source_project_name: str,
    source_context_name: str,
    target_project_name: str,
    target_context_name: str,
) -> ContextInfo:
    source_dir = require_context_dir(settings, source_project_name, source_context_name)
    target_project_dir = require_project_dir(settings, target_project_name)
    target_name = normalize_entity_name(target_context_name, "Context")
    target_dir = target_project_dir / target_name

    if target_dir.exists():
        raise ValueError(
            f"Context '{target_name}' already exists in project '{target_project_name}'"
        )

    shutil.copytree(source_dir, target_dir, ignore=shutil.ignore_patterns(META_FILE_NAME))
    duplicated_meta = load_context_info(source_project_name, source_dir).meta
    duplicated_meta.name = target_name
    write_context_meta(target_dir, duplicated_meta)
    return load_context_info(target_project_name, target_dir)


def delete_context(settings: AppSettings, project_name: str, context_name: str) -> None:
    context_dir = require_context_dir(settings, project_name, context_name)
    shutil.rmtree(context_dir)


def list_projects(settings: AppSettings) -> list[Project]:
    if not settings.contexts_location:
        return []

    contexts_root = Path(settings.contexts_location)
    if not contexts_root.exists() or not contexts_root.is_dir():
        return []

    try:
        project_dirs = sorted(
            (path for path in contexts_root.iterdir() if path.is_dir()),
            key=lambda path: path.name.lower(),
        )
    except OSError as exc:
        warnings.warn(
            f"Failed to list projects from {contexts_root}: {exc}",
            RuntimeWarning,
            stacklevel=2,
        )
        return []

    return [
        Project(name=project_dir.name, contexts_dir=str(project_dir))
        for project_dir in project_dirs
    ]


def list_contexts(settings: AppSettings) -> list[ContextInfo]:
    if not settings.contexts_location:
        return []

    contexts_root = Path(settings.contexts_location)
    if not contexts_root.exists() or not contexts_root.is_dir():
        return []

    contexts: list[ContextInfo] = []
    try:
        project_dirs = sorted(
            (path for path in contexts_root.iterdir() if path.is_dir()),
            key=lambda path: path.name.lower(),
        )
    except OSError as exc:
        warnings.warn(
            f"Failed to list context projects from {contexts_root}: {exc}",
            RuntimeWarning,
            stacklevel=2,
        )
        return []

    for project_dir in project_dirs:
        try:
            context_dirs = sorted(
                (path for path in project_dir.iterdir() if path.is_dir()),
                key=lambda path: path.name.lower(),
            )
        except OSError as exc:
            warnings.warn(
                f"Failed to list contexts from {project_dir}: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
            continue

        for context_dir in context_dirs:
            meta_path = context_dir / META_FILE_NAME
            if not meta_path.exists():
                continue
            try:
                contexts.append(load_context_info(project_dir.name, context_dir))
            except (JSONDecodeError, KeyError, OSError, TypeError, ValueError) as exc:
                warnings.warn(
                    f"Skipping invalid context metadata at {meta_path}: {exc}",
                    RuntimeWarning,
                    stacklevel=2,
                )

    return contexts


def load_context_info(project_name: str, context_dir: Path) -> ContextInfo:
    meta_path = context_dir / META_FILE_NAME
    with meta_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise TypeError(f"{meta_path} must contain a JSON object")

    meta = ContextMeta.from_dict(data)
    thumbnail_path = context_dir / THUMBNAIL_FILE_NAME
    if thumbnail_path.exists():
        meta.thumbnail_path = str(thumbnail_path)

    rxt_path = context_dir / CONTEXT_FILE_NAME
    return ContextInfo(
        project_name=project_name,
        meta=meta,
        context_dir=str(context_dir),
        rxt_path=str(rxt_path) if rxt_path.exists() else "",
    )


def ensure_contexts_root(settings: AppSettings) -> Path:
    if not settings.contexts_location:
        raise ValueError("Contexts location is not configured")

    contexts_root = Path(settings.contexts_location)
    if contexts_root.exists() and not contexts_root.is_dir():
        raise ValueError(f"Contexts location '{contexts_root}' is not a directory")

    contexts_root.mkdir(parents=True, exist_ok=True)
    return contexts_root


def require_project_dir(settings: AppSettings, project_name: str) -> Path:
    contexts_root = ensure_contexts_root(settings)
    normalized_name = normalize_entity_name(project_name, "Project")
    project_dir = contexts_root / normalized_name
    if not project_dir.exists() or not project_dir.is_dir():
        raise ValueError(f"Project '{normalized_name}' does not exist")
    return project_dir


def require_context_dir(settings: AppSettings, project_name: str, context_name: str) -> Path:
    project_dir = require_project_dir(settings, project_name)
    normalized_name = normalize_entity_name(context_name, "Context")
    context_dir = project_dir / normalized_name
    if not context_dir.exists() or not context_dir.is_dir():
        raise ValueError(f"Context '{normalized_name}' does not exist in project '{project_name}'")
    return context_dir


def write_context_meta(context_dir: Path, meta: ContextMeta) -> Path:
    context_dir.mkdir(parents=True, exist_ok=True)
    meta_path = context_dir / META_FILE_NAME
    with meta_path.open("w", encoding="utf-8") as handle:
        json.dump(meta.to_dict(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return meta_path


def normalize_entity_name(value: str, entity_label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{entity_label} name cannot be empty")
    if normalized in {".", ".."} or any(separator in normalized for separator in ("/", "\\")):
        raise ValueError(f"{entity_label} name contains invalid path characters")
    return normalized


def _is_same_location(source_path: Path, target_path: Path) -> bool:
    return os.path.normcase(str(source_path)) == os.path.normcase(str(target_path))


def _rename_path(source_path: Path, target_path: Path) -> None:
    if _is_same_location(source_path, target_path) and str(source_path) != str(target_path):
        temp_path = _temporary_rename_path(source_path)
        source_path.rename(temp_path)
        temp_path.rename(target_path)
        return

    source_path.rename(target_path)


def _temporary_rename_path(source_path: Path) -> Path:
    candidate = source_path.with_name(f"{source_path.name}.__rez_manager_tmp__")
    suffix = 1
    while candidate.exists():
        candidate = source_path.with_name(f"{source_path.name}.__rez_manager_tmp__{suffix}")
        suffix += 1
    return candidate
