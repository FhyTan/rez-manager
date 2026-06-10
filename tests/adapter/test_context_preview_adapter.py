"""Tests for Rez context adapter helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.conftest import RezTestPackage


def test_system_environment_variable_names_include_supported_platforms():
    from rez_manager.adapter.context import system_environment_variable_names

    assert "SYSTEMROOT" in system_environment_variable_names("windows")
    assert "XDG_RUNTIME_DIR" in system_environment_variable_names("linux")
    assert "__CF_USER_TEXT_ENCODING" in system_environment_variable_names("macos")


def test_preserved_system_environment_uses_case_insensitive_matching_on_windows():
    from rez_manager.adapter.context import preserved_system_environment

    preserved = preserved_system_environment(
        process_environ={
            "Path": r"C:\Windows\System32",
            "SystemRoot": r"C:\Windows",
            "TEMP": r"C:\Temp",
            "UNRELATED": "ignored",
        },
        platform_name="windows",
    )

    assert preserved == {
        "Path": r"C:\Windows\System32",
        "SystemRoot": r"C:\Windows",
        "TEMP": r"C:\Temp",
    }


def test_resolve_context_reads_real_rez_repository(
    rez_host_environment,
    rez_settings,
    app_package: RezTestPackage,
    python_311_package: RezTestPackage,
):
    from rez_manager.adapter.context import resolve_context

    result = resolve_context([app_package.request])

    assert set(result.packages) == {"app-1.0.0", "python-3.11"}
    assert set(result.tools) == {"app", "python"}
    assert Path(result.environ["APP_HOME"]).samefile(app_package.directory)
    normalized_path = result.environ["PATH"].lower()
    assert r"c:\windows\system32" in normalized_path
    assert "c:/python311" in normalized_path


def test_resolve_context_wraps_missing_package_family(rez_settings):
    from rez.exceptions import PackageFamilyNotFoundError

    from rez_manager.adapter.context import resolve_context
    from rez_manager.exceptions import RezResolveError

    with pytest.raises(RezResolveError) as exc_info:
        resolve_context(["missing-1"])

    assert isinstance(exc_info.value.__cause__, PackageFamilyNotFoundError)


def test_resolve_context_wraps_missing_transitive_dependency(
    rez_settings,
    broken_dep_package: RezTestPackage,
):
    from rez.exceptions import PackageFamilyNotFoundError

    from rez_manager.adapter.context import resolve_context
    from rez_manager.exceptions import RezResolveError

    with pytest.raises(RezResolveError) as exc_info:
        resolve_context([broken_dep_package.request])

    assert isinstance(exc_info.value.__cause__, PackageFamilyNotFoundError)
    assert "missing_lib" in str(exc_info.value)


def test_save_context_serializes_real_rez_context(
    temp_context_dir: Path,
    rez_settings,
    app_package: RezTestPackage,
    python_311_package: RezTestPackage,
):
    from rez_manager.adapter.context import resolve_context, save_context

    context_path = temp_context_dir / "app.rxt"
    ctx = resolve_context([app_package.request])

    save_context(ctx, str(context_path))

    assert context_path.exists()


def test_save_context_wraps_os_error(temp_context_dir: Path):
    from rez_manager.adapter.context import ContextInfo, save_context
    from rez_manager.exceptions import RezContextSaveError

    class _FakeCtx:
        def save(self, _path):
            raise OSError("disk full")

    ctx = ContextInfo(
        packages=[],
        environ={},
        tools=[],
        _resolved_context=_FakeCtx(),
    )
    with pytest.raises(RezContextSaveError) as exc_info:
        save_context(ctx, str(temp_context_dir / "should_fail.rxt"))

    assert "disk full" in str(exc_info.value)


def test_load_context_round_trips_saved_context(
    rez_host_environment,
    temp_context_dir: Path,
    rez_settings,
    app_package: RezTestPackage,
    python_311_package: RezTestPackage,
):
    from rez_manager.adapter.context import load_context, resolve_context, save_context

    context_path = temp_context_dir / "app.rxt"
    ctx = resolve_context([app_package.request])
    save_context(ctx, str(context_path))

    result = load_context(str(context_path))

    assert set(result.packages) == {"app-1.0.0", "python-3.11"}
    assert set(result.tools) == {"app", "python"}
    assert Path(result.environ["APP_HOME"]).samefile(app_package.directory)


def test_load_context_wraps_invalid_serialized_context(rez_settings, temp_context_dir: Path):
    from rez.exceptions import ResolvedContextError

    from rez_manager.adapter.context import load_context
    from rez_manager.exceptions import RezContextLoadError

    context_path = temp_context_dir / "invalid.rxt"
    context_path.write_text("not a rez context", encoding="utf-8")

    with pytest.raises(RezContextLoadError) as exc_info:
        load_context(str(context_path))

    assert isinstance(exc_info.value.__cause__, ResolvedContextError)
