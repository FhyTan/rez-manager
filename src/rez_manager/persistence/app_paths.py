"""Application path helpers."""

from __future__ import annotations

import os
from pathlib import Path

from platformdirs import user_config_path, user_data_path

APP_NAME = "rez-manager"
SETTINGS_FILE_NAME = "settings.json"


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
