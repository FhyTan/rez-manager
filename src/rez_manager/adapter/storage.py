"""Filesystem-backed state loading."""

from __future__ import annotations

import json
import os
import warnings
from json import JSONDecodeError
from pathlib import Path

from rez_manager.models.project import Project
from rez_manager.models.rez_context import ContextInfo, ContextMeta
from rez_manager.models.settings import AppSettings

SETTINGS_FILE_NAME = "settings.json"
META_FILE_NAME = "meta.json"
CONTEXT_FILE_NAME = "context.rxt"
THUMBNAIL_FILE_NAME = "thumbnail.png"


def app_home_dir() -> Path:
    configured_home = os.environ.get("REZ_MANAGER_HOME")
    if configured_home:
        return Path(configured_home).expanduser()
    return Path.home() / ".rez-manager"


def settings_file_path() -> Path:
    return app_home_dir() / SETTINGS_FILE_NAME


def default_settings() -> AppSettings:
    return AppSettings(
        package_repositories=[],
        contexts_location=str(app_home_dir() / "contexts"),
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
