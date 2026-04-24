"""Tests for Rez context launch adapter helpers."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest


def test_launch_context_runs_short_lived_command(
    rez_host_environment,
    temp_packages_dir: Path,
    rez_package_matrix: dict[str, object],
):
    from rez_manager.adapter.context import launch_context

    process = launch_context(
        [str(rez_package_matrix["app_request"])],
        ["cmd.exe", "/c", "exit", "0"],
        package_paths=[str(temp_packages_dir)],
    )

    assert process.wait(timeout=10) == 0


def test_launch_context_wraps_package_command_errors(
    rez_host_environment,
    temp_packages_dir: Path,
    rez_package_matrix: dict[str, object],
):
    from rez.exceptions import PackageCommandError

    from rez_manager.adapter.context import launch_context
    from rez_manager.exceptions import RezContextLaunchError

    with pytest.raises(RezContextLaunchError) as exc_info:
        launch_context(
            [str(rez_package_matrix["bad_commands_request"])],
            ["cmd.exe", "/c", "exit", "0"],
            package_paths=[str(temp_packages_dir)],
        )

    assert isinstance(exc_info.value.__cause__, PackageCommandError)


def test_launch_context_reports_missing_dependency_after_package_removal(
    rez_host_environment,
    temp_context_dir: Path,
    temp_packages_dir: Path,
    rez_package_matrix: dict[str, object],
):
    from rez.exceptions import PackageFamilyNotFoundError

    from rez_manager.adapter.context import launch_context, save_context
    from rez_manager.adapter.packages import clear_package_cache
    from rez_manager.exceptions import RezContextLaunchError

    context_path = temp_context_dir / "app.rxt"
    save_context(
        [str(rez_package_matrix["app_request"])],
        str(context_path),
        package_paths=[str(temp_packages_dir)],
    )

    shutil.rmtree(Path(rez_package_matrix["python_family_dir"]))
    clear_package_cache()

    with pytest.raises(RezContextLaunchError) as exc_info:
        launch_context(
            [str(rez_package_matrix["app_request"])],
            ["cmd.exe", "/c", "exit", "0"],
            package_paths=[str(temp_packages_dir)],
        )

    assert context_path.exists()
    assert isinstance(exc_info.value.__cause__, PackageFamilyNotFoundError)
    assert "python" in str(exc_info.value)
