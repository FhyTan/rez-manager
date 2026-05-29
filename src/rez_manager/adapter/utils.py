"""Rez initialization and runtime utilities."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from rez_manager.runtime import IS_WINDOWS


def initialize_rez():
    # Ignore the user's home Rez config so the app resolves contexts from its own explicit settings.
    os.environ["REZ_DISABLE_HOME_CONFIG"] = "1"

    # If running as a frozen Nuitka executable, prepend the dist directory to PATH
    # so that subprocess calls to ``rez-pkg-cache`` (spawned by Rez's package
    # caching machinery) resolve to our bundled executable.
    if getattr(sys, "frozen", False):
        dist_dir = os.path.dirname(sys.executable)
        path = os.environ.get("PATH", "")
        if dist_dir not in path:
            os.environ["PATH"] = dist_dir + os.pathsep + path

    # This app must launch Windows commands through cmd because ResolvedContext.execute_shell does
    # not work reliably with Rez's default PowerShell path here. The launch controller therefore
    # always applies cmd-specific command wrapping on Windows instead of relying on
    # rez.system.system.shell, which only reports the OS default shell and does not reflect this
    # config override.
    if IS_WINDOWS:
        from rez.config import config  # noqa: PLC0415

        config.override("default_shell", "cmd")


def apply_package_cache_settings(
    enabled: bool,
    cache_path: str | None,
    ttl_days: int,
) -> None:
    """Apply package cache configuration to Rez at runtime."""
    from rez.config import config  # noqa: PLC0415

    if enabled and cache_path:
        path = Path(cache_path)
        config.override("cache_packages_path", str(path))
        config.override("write_package_cache", True)
        config.override("read_package_cache", True)
        config.override("package_cache_max_variant_days", ttl_days)
    else:
        config.override("cache_packages_path", None)
        config.override("write_package_cache", False)
        config.override("read_package_cache", False)
