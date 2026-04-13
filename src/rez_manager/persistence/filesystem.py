"""Shared filesystem helpers for persistence modules."""

from __future__ import annotations

import json
import os
from pathlib import Path

from rez_manager.models.rez_context import ContextMeta
from rez_manager.models.settings import AppSettings

META_FILE_NAME = "meta.json"
CONTEXT_FILE_NAME = "context.rxt"
THUMBNAIL_FILE_NAME = "thumbnail.png"


def resolve_settings(settings: AppSettings | None = None) -> AppSettings:
    if settings is not None:
        return settings

    from .settings_store import current_settings

    return current_settings()


def contexts_root_path(settings: AppSettings | None = None) -> Path:
    resolved_settings = resolve_settings(settings)
    if not resolved_settings.contexts_location:
        raise ValueError("Contexts location is not configured")

    contexts_root = Path(resolved_settings.contexts_location)
    if contexts_root.exists() and not contexts_root.is_dir():
        raise ValueError(f"Contexts location '{contexts_root}' is not a directory")
    return contexts_root


def ensure_contexts_root(settings: AppSettings | None = None) -> Path:
    contexts_root = contexts_root_path(settings)
    contexts_root.mkdir(parents=True, exist_ok=True)
    return contexts_root


def require_project_path(project_name: str, settings: AppSettings | None = None) -> Path:
    contexts_root = ensure_contexts_root(settings)
    normalized_name = normalize_entity_name(project_name, "Project")
    project_path = contexts_root / normalized_name
    if not project_path.exists() or not project_path.is_dir():
        raise ValueError(f"Project '{normalized_name}' does not exist")
    return project_path


def require_context_path(
    project_name: str,
    context_name: str,
    settings: AppSettings | None = None,
) -> Path:
    project_path = require_project_path(project_name, settings)
    normalized_name = normalize_entity_name(context_name, "Context")
    context_path = project_path / normalized_name
    if not context_path.exists() or not context_path.is_dir():
        raise ValueError(f"Context '{normalized_name}' does not exist in project '{project_name}'")
    return context_path


def write_context_meta(context_path: Path, meta: ContextMeta) -> Path:
    context_path.mkdir(parents=True, exist_ok=True)
    meta_path = context_path / META_FILE_NAME
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


def is_same_location(source_path: Path, target_path: Path) -> bool:
    return os.path.normcase(str(source_path)) == os.path.normcase(str(target_path))


def rename_path(source_path: Path, target_path: Path) -> None:
    if is_same_location(source_path, target_path) and str(source_path) != str(target_path):
        temp_path = temporary_rename_path(source_path)
        source_path.rename(temp_path)
        temp_path.rename(target_path)
        return

    source_path.rename(target_path)


def temporary_rename_path(source_path: Path) -> Path:
    candidate = source_path.with_name(f"{source_path.name}.__rez_manager_tmp__")
    suffix = 1
    while candidate.exists():
        candidate = source_path.with_name(f"{source_path.name}.__rez_manager_tmp__{suffix}")
        suffix += 1
    return candidate
