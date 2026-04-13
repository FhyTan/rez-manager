"""Filesystem persistence helpers for rez-manager."""

from .app_paths import app_config_dir, app_data_dir, settings_file_path
from .context_store import (
    delete_context,
    duplicate_context,
    list_contexts,
    load_context,
    save_context,
)
from .project_store import (
    create_project,
    delete_project,
    duplicate_project,
    get_project,
    list_projects,
    rename_project,
)
from .settings_store import current_settings, default_settings, load_settings, save_settings

__all__ = [
    "app_config_dir",
    "app_data_dir",
    "current_settings",
    "create_project",
    "default_settings",
    "delete_context",
    "delete_project",
    "duplicate_context",
    "duplicate_project",
    "get_project",
    "list_contexts",
    "list_projects",
    "load_context",
    "load_settings",
    "rename_project",
    "save_context",
    "save_settings",
    "settings_file_path",
]
