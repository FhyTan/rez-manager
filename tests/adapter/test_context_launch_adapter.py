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
    from rez_manager.adapter.context import launch_context, resolve_context

    ctx = resolve_context([app_package.request])
    process = launch_context(ctx, ["cmd.exe", "/c", "exit", "0"])

    assert process.wait(timeout=10) == 0


def test_launch_context_wraps_package_command_errors(
    rez_host_environment,
    rez_settings,
    bad_commands_package: RezTestPackage,
):
    from rez.exceptions import PackageCommandError

    from rez_manager.adapter.context import resolve_context
    from rez_manager.exceptions import RezResolveError

    with pytest.raises(RezResolveError) as exc_info:
        resolve_context([bad_commands_package.request])

    assert isinstance(exc_info.value.__cause__, PackageCommandError)


def test_launch_context_reports_missing_dependency_after_package_removal(
    rez_host_environment,
    temp_context_dir: Path,
    rez_settings,
    app_package: RezTestPackage,
    python_311_package: RezTestPackage,
):
    from rez.exceptions import PackageFamilyNotFoundError

    from rez_manager.adapter.context import resolve_context, save_context
    from rez_manager.adapter.packages import clear_package_cache
    from rez_manager.exceptions import RezResolveError

    context_path = temp_context_dir / "app.rxt"
    ctx = resolve_context([app_package.request])
    save_context(ctx, str(context_path))

    shutil.rmtree(python_311_package.directory.parent)
    clear_package_cache()

    with pytest.raises(RezResolveError) as exc_info:
        resolve_context([app_package.request])

    assert context_path.exists()
    assert isinstance(exc_info.value.__cause__, PackageFamilyNotFoundError)
    assert "python" in str(exc_info.value)


def test_launch_from_rxt_after_load_and_resolve(
    rez_host_environment,
    temp_context_dir: Path,
    rez_settings,
    app_package: RezTestPackage,
    python_311_package: RezTestPackage,
):
    from rez_manager.adapter.context import (
        launch_context,
        load_context,
        resolve_context,
        save_context,
    )

    context_path = temp_context_dir / "app.rxt"
    ctx = resolve_context([app_package.request])
    save_context(ctx, str(context_path))

    loaded = load_context(str(context_path))
    process = launch_context(loaded, ["cmd.exe", "/c", "exit", "0"])

    assert process.wait(timeout=10) == 0


def test_load_context_wraps_invalid_rxt_file(temp_context_dir: Path):
    from rez_manager.adapter.context import load_context
    from rez_manager.exceptions import RezContextLoadError

    context_path = temp_context_dir / "invalid.rxt"
    context_path.write_text("not a rez context", encoding="utf-8")

    with pytest.raises(RezContextLoadError) as exc_info:
        load_context(str(context_path))

    assert "invalid.rxt" in str(exc_info.value)
