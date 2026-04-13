"""Project persistence helpers."""

from __future__ import annotations

import shutil
import warnings
from pathlib import Path

from rez_manager.models.project import Project
from rez_manager.models.settings import AppSettings

from .filesystem import (
    contexts_root_path,
    ensure_contexts_root,
    is_same_location,
    normalize_entity_name,
    rename_path,
    require_project_path,
)


def list_projects(settings: AppSettings | None = None) -> list[Project]:
    try:
        contexts_root = contexts_root_path(settings)
    except ValueError:
        return []

    if not contexts_root.exists() or not contexts_root.is_dir():
        return []

    try:
        project_paths = sorted(
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

    return [_project_from_path(project_path) for project_path in project_paths]


def get_project(name: str, settings: AppSettings | None = None) -> Project:
    return _project_from_path(require_project_path(name, settings))


def create_project(name: str, settings: AppSettings | None = None) -> Project:
    contexts_root = ensure_contexts_root(settings)
    project_name = normalize_entity_name(name, "Project")
    project_path = contexts_root / project_name
    if project_path.exists():
        raise ValueError(f"Project '{project_name}' already exists")
    project_path.mkdir(parents=True, exist_ok=False)
    return _project_from_path(project_path)


def rename_project(
    current_name: str,
    new_name: str,
    settings: AppSettings | None = None,
) -> Project:
    source_path = require_project_path(current_name, settings)
    target_name = normalize_entity_name(new_name, "Project")
    target_path = source_path.parent / target_name

    if str(source_path) == str(target_path):
        return Project(name=target_name, path=target_path)
    if target_path.exists() and not is_same_location(source_path, target_path):
        raise ValueError(f"Project '{target_name}' already exists")

    rename_path(source_path, target_path)
    return Project(name=target_name, path=target_path)


def duplicate_project(
    source_name: str,
    target_name: str,
    settings: AppSettings | None = None,
) -> Project:
    source_path = require_project_path(source_name, settings)
    target_name = normalize_entity_name(target_name, "Project")
    target_path = source_path.parent / target_name

    if target_path.exists():
        raise ValueError(f"Project '{target_name}' already exists")

    shutil.copytree(source_path, target_path)
    return _project_from_path(target_path)


def delete_project(name: str, settings: AppSettings | None = None) -> None:
    project_path = require_project_path(name, settings)
    shutil.rmtree(project_path)


def _project_from_path(project_path: Path) -> Project:
    return Project(name=project_path.name, path=project_path)
