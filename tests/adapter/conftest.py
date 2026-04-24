"""Shared real-Rez fixtures for adapter tests."""

from __future__ import annotations

import textwrap
from collections.abc import Sequence
from pathlib import Path

import pytest


@pytest.fixture
def initialized_rez() -> None:
    """Initialize Rez test state and clear repository caches around each real-Rez test."""
    from rez_manager.adapter.packages import clear_package_cache
    from rez_manager.adapter.utils import initialize_rez

    initialize_rez()
    clear_package_cache()
    yield
    clear_package_cache()


@pytest.fixture
def temp_packages_dir(tmp_path: Path) -> Path:
    """Create a temporary Rez package repository root."""
    repository_root = tmp_path / "packages"
    repository_root.mkdir()
    return repository_root


@pytest.fixture
def temp_context_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for saved context files and launch probes."""
    context_root = tmp_path / "contexts"
    context_root.mkdir()
    return context_root


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


@pytest.fixture
def rez_package_matrix(
    initialized_rez,
    rez_package_writer,
    temp_packages_dir: Path,
) -> dict[str, object]:
    """Populate the temporary repository with healthy and failing Rez package scenarios."""
    python_310_dir = rez_package_writer(
        "python",
        "3.10",
        description="Test Python 3.10",
        tools=["python310"],
        commands=['env.PATH.append("C:/Python310")'],
    )
    python_311_dir = rez_package_writer(
        "python",
        "3.11",
        description="Test Python 3.11",
        tools=["python"],
        commands=['env.PATH.append("C:/Python311")'],
    )
    app_dir = rez_package_writer(
        "app",
        "1.0.0",
        description="Test application package",
        requires=["python-3.11"],
        tools=["app"],
        commands=['env.APP_HOME = "{root}"'],
    )
    rez_package_writer(
        "broken_dep",
        "1.0.0",
        description="Broken dependency package",
        requires=["missing_lib-1"],
    )
    rez_package_writer(
        "bad_commands",
        "1.0.0",
        description="Package with broken commands",
        tools=["badcmd"],
        commands=["undefined_name()"],
    )
    rez_package_writer(
        "bad_requires",
        "1.0.0",
        raw_source="""
        name = "bad_requires"
        version = "1.0.0"
        requires = 123
        """,
    )
    rez_package_writer(
        "syntax_pkg",
        "1.0.0",
        raw_source="""
        name = "syntax_pkg"
        version = "1.0.0"
        this is not python
        """,
    )

    return {
        "repository": temp_packages_dir,
        "app_request": "app-1.0.0",
        "broken_dep_request": "broken_dep-1.0.0",
        "bad_commands_request": "bad_commands-1.0.0",
        "bad_requires_request": "bad_requires-1.0.0",
        "syntax_pkg_request": "syntax_pkg-1.0.0",
        "app_dir": app_dir,
        "python_family_dir": temp_packages_dir / "python",
        "python_310_dir": python_310_dir,
        "python_311_dir": python_311_dir,
    }
