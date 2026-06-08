"""Tests for Rez context launch adapter helpers."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from tests.conftest import RezTestPackage


def test_launch_context_runs_short_lived_command(
    rez_host_environment,
    rez_settings,
    app_package: RezTestPackage,
    python_311_package: RezTestPackage,
):
    from rez_manager.adapter.context import launch_context

    process = launch_context([app_package.request], ["cmd.exe", "/c", "exit", "0"])

    assert process.wait(timeout=10) == 0


def test_launch_context_wraps_package_command_errors(
    rez_host_environment,
    rez_settings,
    bad_commands_package: RezTestPackage,
):
    from rez.exceptions import PackageCommandError

    from rez_manager.adapter.context import launch_context
    from rez_manager.exceptions import RezContextLaunchError

    with pytest.raises(RezContextLaunchError) as exc_info:
        launch_context([bad_commands_package.request], ["cmd.exe", "/c", "exit", "0"])

    assert isinstance(exc_info.value.__cause__, PackageCommandError)


def test_launch_context_reports_missing_dependency_after_package_removal(
    rez_host_environment,
    temp_context_dir: Path,
    rez_settings,
    app_package: RezTestPackage,
    python_311_package: RezTestPackage,
):
    from rez.exceptions import PackageFamilyNotFoundError

    from rez_manager.adapter.context import launch_context, save_context
    from rez_manager.adapter.packages import clear_package_cache
    from rez_manager.exceptions import RezContextLaunchError

    context_path = temp_context_dir / "app.rxt"
    save_context([app_package.request], str(context_path))

    shutil.rmtree(python_311_package.directory.parent)
    clear_package_cache()

    with pytest.raises(RezContextLaunchError) as exc_info:
        launch_context([app_package.request], ["cmd.exe", "/c", "exit", "0"])

    assert context_path.exists()
    assert isinstance(exc_info.value.__cause__, PackageFamilyNotFoundError)
    assert "python" in str(exc_info.value)
