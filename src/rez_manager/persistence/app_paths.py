"""Application path helpers."""

from __future__ import annotations

from os import environ
from pathlib import Path

from platformdirs import user_cache_path, user_config_path, user_data_path, user_log_path

APP_NAME = "rez-manager"
SETTINGS_FILE_NAME = "settings.json"
LOG_FILE_NAME = "rez-manager.log"


def _app_home_override() -> Path | None:
    raw_value = environ.get("REZ_MANAGER_HOME")
    if not raw_value:
        return None
    return Path(raw_value).expanduser()


def app_config_dir() -> Path:
    override = _app_home_override()
    if override is not None:
        return override
    return user_config_path(APP_NAME, appauthor=False)


def app_data_dir() -> Path:
    override = _app_home_override()
    if override is not None:
        return override
    return user_data_path(APP_NAME, appauthor=False)


def app_cache_dir() -> Path:
    override = _app_home_override()
    if override is not None:
        return override / "cache"
    return user_cache_path(APP_NAME, appauthor=False)


def app_log_dir() -> Path:
    override = _app_home_override()
    if override is not None:
        return override / "logs"
    return user_log_path(APP_NAME, appauthor=False)


def settings_file_path() -> Path:
    return app_config_dir() / SETTINGS_FILE_NAME


def log_file_path() -> Path:
    return app_log_dir() / LOG_FILE_NAME
