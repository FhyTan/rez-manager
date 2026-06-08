"""Top-level pytest fixtures for rez-manager tests."""

from __future__ import annotations

import os
import sys
import textwrap
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from shutil import which

import pytest

from rez_manager.models.settings import AppSettings
from rez_manager.runtime import IS_COMPILED, IS_WINDOWS


@dataclass
class RezTestPackage:
    """Metadata for a test Rez package created in the temporary repository."""

    name: str
    version: str
    request: str  # "name-version"
    directory: Path  # package variant directory


# ---------------------------------------------------------------------------
# Session-scoped Rez initialization — runs once before any test
# ---------------------------------------------------------------------------

_DEFAULT_TEST_SETTINGS = AppSettings()
_DEFAULT_TEST_SETTINGS.package_cache.enabled = False


def _clear_rez_env_vars() -> None:
    """Remove all REZ_* environment variables except REZ_BIN_PATH."""
    rez_bin_path = os.environ.get("REZ_BIN_PATH")
    keys_to_remove = [k for k in os.environ if k.startswith("REZ_") and k != "REZ_BIN_PATH"]
    for key in keys_to_remove:
        del os.environ[key]
    if rez_bin_path is not None:
        os.environ.setdefault("REZ_BIN_PATH", rez_bin_path)


def _setup_rez_bin_path() -> None:
    from rez.system import system  # noqa: PLC0415

    if IS_COMPILED:
        system.rez_bin_path = os.path.dirname(sys.executable)
    else:
        if rez_bin_path := os.environ.get("REZ_BIN_PATH"):
            system.rez_bin_path = rez_bin_path
        elif pkg_cache := which("rez-pkg-cache"):
            system.rez_bin_path = os.path.dirname(pkg_cache)
            os.environ.setdefault("REZ_BIN_PATH", system.rez_bin_path)


@pytest.fixture(scope="session", autouse=True)
def _rez_session_init() -> None:
    """One-time Rez initialization for the entire test session."""
    _clear_rez_env_vars()
    os.environ["REZ_DISABLE_HOME_CONFIG"] = "1"

    from rez.config import config  # noqa: PLC0415

    _setup_rez_bin_path()

    if IS_WINDOWS:
        config.override("default_shell", "cmd")

    from rez_manager.adapter.utils import apply_settings_to_rez  # noqa: PLC0415

    apply_settings_to_rez(_DEFAULT_TEST_SETTINGS)


@pytest.fixture(autouse=True)
def _rez_clear_cache() -> None:
    """Clear the in-memory Rez package repository cache between tests."""
    from rez_manager.adapter.packages import clear_package_cache  # noqa: PLC0415

    clear_package_cache()
    yield
    clear_package_cache()


# ---------------------------------------------------------------------------
# Temporary directories
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_packages_dir(tmp_path: Path) -> Path:
    """Create a temporary Rez package repository root."""
    repository_root = tmp_path / "packages"
    repository_root.mkdir()
    return repository_root


@pytest.fixture
def temp_context_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for saved context files."""
    context_root = tmp_path / "contexts"
    context_root.mkdir()
    return context_root


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for Rez package cache (isolated from production)."""
    cache_dir = tmp_path / "rez_cache"
    cache_dir.mkdir()
    return cache_dir


# ---------------------------------------------------------------------------
# Host environment (Windows-specific minimal env for launch tests)
# ---------------------------------------------------------------------------


@pytest.fixture
def rez_host_environment(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Provide the minimal host environment required by the adapter's launch helpers."""
    values = {
        "PATH": r"C:\Windows\System32",
        "SystemRoot": r"C:\Windows",
        "COMSPEC": r"C:\Windows\System32\cmd.exe",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    return values


# ---------------------------------------------------------------------------
# Package writer factory — writes a package.py into temp_packages_dir
# ---------------------------------------------------------------------------


@pytest.fixture
def rez_package_writer(temp_packages_dir: Path):
    """Write a package.py definition into the temporary Rez repository."""

    def write_package(
        name: str,
        version: str,
        *,
        description: str | None = None,
        requires: Sequence[str] | None = None,
        tools: Sequence[str] | None = None,
        commands: Sequence[str] | None = None,
        raw_source: str | None = None,
    ) -> Path:
        package_directory = temp_packages_dir / name / version
        package_directory.mkdir(parents=True)
        package_file = package_directory / "package.py"

        if raw_source is not None:
            package_file.write_text(textwrap.dedent(raw_source).strip() + "\n", encoding="utf-8")
            return package_directory

        lines = [
            f'name = "{name}"',
            f'version = "{version}"',
        ]
        if description is not None:
            lines.append(f'description = "{description}"')
        if requires is not None:
            lines.append(f"requires = {list(requires)!r}")
        if tools is not None:
            lines.append(f"tools = {list(tools)!r}")
        if commands is not None:
            lines.extend(
                [
                    "",
                    "def commands():",
                    *[f"    {line}" for line in commands],
                ]
            )

        package_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return package_directory

    return write_package


# ---------------------------------------------------------------------------
# Rez settings fixtures — apply AppSettings to rez.config, restore on teardown
# ---------------------------------------------------------------------------


def _apply_settings_to_rez(settings: AppSettings) -> AppSettings:
    from rez_manager.adapter.utils import apply_settings_to_rez  # noqa: PLC0415

    apply_settings_to_rez(settings)
    return settings


@pytest.fixture
def rez_settings(temp_packages_dir: Path) -> AppSettings:
    """Apply test Rez settings (package cache disabled) and restore defaults on teardown."""
    settings = AppSettings()
    settings.package_cache.enabled = False
    settings.general.package_repositories = [str(temp_packages_dir)]
    _apply_settings_to_rez(settings)
    yield settings
    _apply_settings_to_rez(_DEFAULT_TEST_SETTINGS)


@pytest.fixture
def rez_cache_settings(temp_packages_dir: Path, temp_cache_dir: Path) -> AppSettings:
    """Apply test Rez settings with package cache enabled. Restore defaults on teardown."""
    settings = AppSettings()
    settings.package_cache.enabled = True
    settings.package_cache.path = str(temp_cache_dir)
    settings.package_cache.async_mode = False
    settings.general.package_repositories = [str(temp_packages_dir)]
    _apply_settings_to_rez(settings)
    yield settings
    _apply_settings_to_rez(_DEFAULT_TEST_SETTINGS)


# ---------------------------------------------------------------------------
# Per-package fixtures — each writes a single package to temp_packages_dir
# ---------------------------------------------------------------------------


@pytest.fixture
def python_310_package(rez_package_writer) -> RezTestPackage:
    directory = rez_package_writer(
        "python",
        "3.10",
        description="Test Python 3.10",
        tools=["python310"],
        commands=['env.PATH.append("C:/Python310")'],
    )
    return RezTestPackage(
        name="python", version="3.10", request="python-3.10", directory=directory
    )


@pytest.fixture
def python_311_package(rez_package_writer) -> RezTestPackage:
    directory = rez_package_writer(
        "python",
        "3.11",
        description="Test Python 3.11",
        tools=["python"],
        commands=['env.PATH.append("C:/Python311")'],
    )
    return RezTestPackage(
        name="python", version="3.11", request="python-3.11", directory=directory
    )


@pytest.fixture
def app_package(rez_package_writer) -> RezTestPackage:
    directory = rez_package_writer(
        "app",
        "1.0.0",
        description="Test application package",
        requires=["python-3.11"],
        tools=["app"],
        commands=['env.APP_HOME = "{root}"'],
    )
    return RezTestPackage(
        name="app", version="1.0.0", request="app-1.0.0", directory=directory
    )


@pytest.fixture
def broken_dep_package(rez_package_writer) -> RezTestPackage:
    directory = rez_package_writer(
        "broken_dep",
        "1.0.0",
        description="Broken dependency package",
        requires=["missing_lib-1"],
    )
    return RezTestPackage(
        name="broken_dep", version="1.0.0", request="broken_dep-1.0.0", directory=directory
    )


@pytest.fixture
def bad_commands_package(rez_package_writer) -> RezTestPackage:
    directory = rez_package_writer(
        "bad_commands",
        "1.0.0",
        description="Package with broken commands",
        tools=["badcmd"],
        commands=["undefined_name()"],
    )
    return RezTestPackage(
        name="bad_commands",
        version="1.0.0",
        request="bad_commands-1.0.0",
        directory=directory,
    )


@pytest.fixture
def bad_requires_package(rez_package_writer) -> RezTestPackage:
    directory = rez_package_writer(
        "bad_requires",
        "1.0.0",
        raw_source="""
        name = "bad_requires"
        version = "1.0.0"
        requires = 123
        """,
    )
    return RezTestPackage(
        name="bad_requires",
        version="1.0.0",
        request="bad_requires-1.0.0",
        directory=directory,
    )


@pytest.fixture
def syntax_pkg_package(rez_package_writer) -> RezTestPackage:
    directory = rez_package_writer(
        "syntax_pkg",
        "1.0.0",
        raw_source="""
        name = "syntax_pkg"
        version = "1.0.0"
        this is not python
        """,
    )
    return RezTestPackage(
        name="syntax_pkg",
        version="1.0.0",
        request="syntax_pkg-1.0.0",
        directory=directory,
    )


@pytest.fixture
def cachable_pkg(rez_package_writer) -> RezTestPackage:
    """A cachable Rez package containing a 1 KiB data file."""
    directory = rez_package_writer(
        "cachable_pkg",
        "1.0.0",
        raw_source="""
        name = "cachable_pkg"
        version = "1.0.0"
        description = "A cachable test package"
        cachable = True
        """,
    )
    data_file = directory / "data.bin"
    data_file.write_bytes(b"\x00" * 1024)
    return RezTestPackage(
        name="cachable_pkg",
        version="1.0.0",
        request="cachable_pkg-1.0.0",
        directory=directory,
    )


# ---------------------------------------------------------------------------
# Cache test helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def rez_pkg_cache_binary() -> None:
    """Skip the test if the rez-pkg-cache binary is not available."""
    from rez.system import system  # noqa: PLC0415

    if system.rez_bin_path:
        candidate = Path(system.rez_bin_path) / "rez-pkg-cache"
        if candidate.is_file():
            return
    if which("rez-pkg-cache"):
        return
    pytest.skip("rez-pkg-cache binary not available; set REZ_BIN_PATH")
