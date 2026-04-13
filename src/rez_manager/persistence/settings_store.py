"""Settings persistence helpers."""

from __future__ import annotations

import json
import warnings
from json import JSONDecodeError
from pathlib import Path

from rez_manager.models.settings import AppSettings

from .app_paths import app_data_dir, settings_file_path


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


def current_settings() -> AppSettings:
    return load_settings()


def save_settings(settings: AppSettings) -> Path:
    path = settings_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as handle:
        json.dump(settings.to_dict(), handle, indent=2, sort_keys=True)
        handle.write("\n")

    return path
