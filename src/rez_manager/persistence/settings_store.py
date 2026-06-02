"""Settings persistence helpers."""

from __future__ import annotations

import json
from os import PathLike
from pathlib import Path

from rez_manager.models.settings import AppSettings

from .app_paths import settings_file_path


def read_settings_file(path: str | PathLike[str]) -> AppSettings:
    settings_path = Path(path)

    with settings_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise TypeError(f"{settings_path} must contain a JSON object")

    return AppSettings.from_dict(data)


def write_settings_file(settings: AppSettings, path: str | PathLike[str]) -> Path:
    settings_path = Path(path)
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    with settings_path.open("w", encoding="utf-8") as handle:
        json.dump(settings.to_dict(), handle, indent=2, sort_keys=False)
        handle.write("\n")

    return settings_path


def load_settings() -> AppSettings:
    path = settings_file_path()
    if not path.exists():
        return AppSettings()
    return read_settings_file(path)


def save_settings(settings: AppSettings) -> Path:
    return write_settings_file(settings, settings_file_path())


def current_settings() -> AppSettings:
    return load_settings()
