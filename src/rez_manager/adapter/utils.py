"""Rez initialization and runtime utilities."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from loguru import logger

from rez_manager.models.settings import AppSettings
from rez_manager.persistence.app_paths import default_rez_package_caches_dir
from rez_manager.runtime import IS_COMPILED, IS_WINDOWS


def initialize_rez():
    # Ignore the user's home Rez config so the app resolves contexts from its own explicit settings.
    os.environ["REZ_DISABLE_HOME_CONFIG"] = "1"

    from rez.system import system  # noqa: PLC0415

    # Point rez to its own executables so it can spawn ``rez-pkg-cache`` as a subprocess.
    # In a frozen (Nuitka) build both exes live in the same dist directory;
    # In development, you have to set REZ_BIN_PATH in your environment to point to
    # your Rez install's bin directory. Otherwise the package caching will be disabled.
    if IS_COMPILED:
        rez_bin_path = os.path.dirname(sys.executable)
        system.rez_bin_path = rez_bin_path
        logger.info(f"Running in productive state, setting Rez bin path to: {rez_bin_path}")
    else:
        if rez_bin_path := os.environ.get("REZ_BIN_PATH"):
            system.rez_bin_path = rez_bin_path
            logger.info(f"Running in development state, setting Rez bin path to: {rez_bin_path}")

    # This app must launch Windows commands through cmd because ResolvedContext.execute_shell does
    # not work reliably with Rez's default PowerShell path here. The launch controller therefore
    # always applies cmd-specific command wrapping on Windows instead of relying on
    # rez.system.system.shell, which only reports the OS default shell and does not reflect this
    # config override.
    if IS_WINDOWS:
        from rez.config import config  # noqa: PLC0415

        config.override("default_shell", "cmd")

    # Load and apply settings to Rez at startup so that the package cache and package paths
    # are configured before any package queries or context resolutions happen.
    apply_settings_to_rez(AppSettings.load())


def apply_settings_to_rez(settings: AppSettings) -> None:
    """Apply application settings (package cache, package paths) to Rez at runtime."""
    from rez.config import config  # noqa: PLC0415

    pkg_cache = settings.package_cache
    if pkg_cache.enabled:
        if pkg_cache.path.strip():
            pkg_cache_path = Path(pkg_cache.path.strip())
        else:
            pkg_cache_path = default_rez_package_caches_dir()

        config.override("cache_packages_path", str(pkg_cache_path))
        config.override("write_package_cache", True)
        config.override("read_package_cache", True)
        config.override("package_cache_async", pkg_cache.async_mode)
        config.override("package_cache_max_variant_days", pkg_cache.ttl_days)
        config.override("package_cache_space_buffer ", pkg_cache.max_size_gb * 1024**3)
    else:
        config.override("cache_packages_path", None)
        config.override("write_package_cache", False)
        config.override("read_package_cache", False)

    repos = settings.general.package_repositories
    config.override("packages_path", list(repos))
