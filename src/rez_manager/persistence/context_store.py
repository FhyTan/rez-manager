"""Context persistence helpers."""

from __future__ import annotations

import json
import shutil
import warnings
from json import JSONDecodeError
from pathlib import Path

from rez_manager.models.project import Project
from rez_manager.models.rez_context import ContextMeta, RezContext
from rez_manager.models.settings import AppSettings

from .filesystem import (
    META_FILE_NAME,
    contexts_root_path,
    is_same_location,
    normalize_entity_name,
    rename_path,
    require_context_path,
    require_project_path,
    write_context_meta,
)


def list_contexts(settings: AppSettings | None = None) -> list[RezContext]:
    try:
        contexts_root = contexts_root_path(settings)
    except ValueError:
        return []

    if not contexts_root.exists() or not contexts_root.is_dir():
        return []

    contexts: list[RezContext] = []
    for project_path in _sorted_directory_children(
        contexts_root,
        warning_prefix="Failed to list context projects",
    ):
        project = Project(name=project_path.name, path=project_path)
        contexts.extend(list_project_contexts(project.name, settings, project=project))
    return contexts


def list_project_contexts(
    project_name: str,
    settings: AppSettings | None = None,
    *,
    project: Project | None = None,
) -> list[RezContext]:
    project_path = _project_path_for_listing(project_name, settings, project)
    contexts: list[RezContext] = []

    for context_path in _sorted_directory_children(
        project_path,
        warning_prefix="Failed to list contexts",
    ):
        meta_path = context_path / META_FILE_NAME
        if not meta_path.exists():
            continue
        try:
            contexts.append(_load_context_from_path(project_name, context_path, project=project))
        except (JSONDecodeError, KeyError, OSError, TypeError, ValueError) as exc:
            warnings.warn(
                f"Skipping invalid context metadata at {meta_path}: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )

    return contexts


def load_context(
    project_name: str,
    context_name: str,
    settings: AppSettings | None = None,
) -> RezContext:
    context_path = require_context_path(project_name, context_name, settings)
    return _load_context_from_path(project_name, context_path)


def save_context(
    project_name: str,
    meta: ContextMeta,
    *,
    original_project_name: str | None = None,
    original_context_name: str | None = None,
    settings: AppSettings | None = None,
) -> RezContext:
    project_path = require_project_path(project_name, settings)
    context_name = normalize_entity_name(meta.name, "Context")
    target_path = project_path / context_name
    normalized_meta = ContextMeta(
        name=context_name,
        description=meta.description,
        launch_target=meta.launch_target,
        custom_command=meta.custom_command,
        packages=list(meta.packages),
    )

    if (original_project_name is None) != (original_context_name is None):
        raise ValueError(
            "Original project and context names must both be provided when editing a context"
        )

    if original_project_name is None and original_context_name is None:
        if target_path.exists():
            raise ValueError(f"Context '{context_name}' already exists in project '{project_name}'")
        target_path.mkdir(parents=True, exist_ok=False)
        write_context_meta(target_path, normalized_meta)
        return _load_context_from_path(project_name, target_path)

    source_path = require_context_path(original_project_name, original_context_name, settings)
    if str(source_path) != str(target_path):
        if target_path.exists() and not is_same_location(source_path, target_path):
            raise ValueError(f"Context '{context_name}' already exists in project '{project_name}'")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        rename_path(source_path, target_path)

    write_context_meta(target_path, normalized_meta)
    return _load_context_from_path(project_name, target_path)


def duplicate_context(
    source_project_name: str,
    source_context_name: str,
    target_project_name: str,
    target_context_name: str,
    settings: AppSettings | None = None,
) -> RezContext:
    source_path = require_context_path(source_project_name, source_context_name, settings)
    target_project_path = require_project_path(target_project_name, settings)
    target_name = normalize_entity_name(target_context_name, "Context")
    target_path = target_project_path / target_name

    if target_path.exists():
        raise ValueError(
            f"Context '{target_name}' already exists in project '{target_project_name}'"
        )

    shutil.copytree(source_path, target_path, ignore=shutil.ignore_patterns(META_FILE_NAME))
    duplicated_meta = _load_context_from_path(source_project_name, source_path).meta
    duplicated_meta.name = target_name
    write_context_meta(target_path, duplicated_meta)
    return _load_context_from_path(target_project_name, target_path)


def delete_context(
    project_name: str,
    context_name: str,
    settings: AppSettings | None = None,
) -> None:
    context_path = require_context_path(project_name, context_name, settings)
    shutil.rmtree(context_path)


def _project_path_for_listing(
    project_name: str,
    settings: AppSettings | None,
    project: Project | None,
) -> Path:
    if project is not None and project.path:
        return Path(project.path)
    return require_project_path(project_name, settings)


def _sorted_directory_children(path: Path, *, warning_prefix: str) -> list[Path]:
    try:
        return sorted(
            (child for child in path.iterdir() if child.is_dir()),
            key=lambda child: child.name.lower(),
        )
    except OSError as exc:
        warnings.warn(
            f"{warning_prefix} from {path}: {exc}",
            RuntimeWarning,
            stacklevel=2,
        )
        return []


def _load_context_from_path(
    project_name: str,
    context_path: Path,
    *,
    project: Project | None = None,
) -> RezContext:
    meta_path = context_path / META_FILE_NAME
    with meta_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise TypeError(f"{meta_path} must contain a JSON object")

    meta = ContextMeta.from_dict(data)
    context_project = project or Project(name=project_name, path=context_path.parent)
    return RezContext(project=context_project, meta=meta, path=context_path)
