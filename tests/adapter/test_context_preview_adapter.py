"""Tests for Rez context adapter helpers."""

from __future__ import annotations

from pathlib import Path

import pytest


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
    temp_packages_dir: Path,
    rez_package_matrix: dict[str, object],
):
    from rez_manager.adapter.context import resolve_context

    result = resolve_context(
        [str(rez_package_matrix["app_request"])],
        package_paths=[str(temp_packages_dir)],
    )

    assert set(result.packages) == {"app-1.0.0", "python-3.11"}
    assert set(result.tools) == {"app", "python"}
    assert Path(result.environ["APP_HOME"]).samefile(Path(rez_package_matrix["app_dir"]))
    normalized_path = result.environ["PATH"].lower()
    assert r"c:\windows\system32" in normalized_path
    assert "c:/python311" in normalized_path


def test_resolve_context_wraps_missing_package_family(temp_packages_dir: Path, initialized_rez):
    from rez.exceptions import PackageFamilyNotFoundError

    from rez_manager.adapter.context import resolve_context
    from rez_manager.exceptions import RezResolveError

    with pytest.raises(RezResolveError) as exc_info:
        resolve_context(["missing-1"], package_paths=[str(temp_packages_dir)])

    assert isinstance(exc_info.value.__cause__, PackageFamilyNotFoundError)


def test_resolve_context_wraps_missing_transitive_dependency(
    temp_packages_dir: Path,
    rez_package_matrix: dict[str, object],
):
    from rez.exceptions import PackageFamilyNotFoundError

    from rez_manager.adapter.context import resolve_context
    from rez_manager.exceptions import RezResolveError

    with pytest.raises(RezResolveError) as exc_info:
        resolve_context(
            [str(rez_package_matrix["broken_dep_request"])],
            package_paths=[str(temp_packages_dir)],
        )

    assert isinstance(exc_info.value.__cause__, PackageFamilyNotFoundError)
    assert "missing_lib" in str(exc_info.value)


def test_save_context_serializes_real_rez_context(
    temp_context_dir: Path,
    temp_packages_dir: Path,
    rez_package_matrix: dict[str, object],
):
    from rez_manager.adapter.context import save_context

    context_path = temp_context_dir / "app.rxt"

    save_context(
        [str(rez_package_matrix["app_request"])],
        str(context_path),
        package_paths=[str(temp_packages_dir)],
    )

    assert context_path.exists()


def test_save_context_wraps_missing_dependency(
    temp_context_dir: Path,
    temp_packages_dir: Path,
    rez_package_matrix: dict[str, object],
):
    from rez.exceptions import PackageFamilyNotFoundError

    from rez_manager.adapter.context import save_context
    from rez_manager.exceptions import RezContextSaveError

    with pytest.raises(RezContextSaveError) as exc_info:
        save_context(
            [str(rez_package_matrix["broken_dep_request"])],
            str(temp_context_dir / "broken.rxt"),
            package_paths=[str(temp_packages_dir)],
        )

    assert isinstance(exc_info.value.__cause__, PackageFamilyNotFoundError)


def test_load_context_round_trips_saved_context(
    rez_host_environment,
    temp_context_dir: Path,
    temp_packages_dir: Path,
    rez_package_matrix: dict[str, object],
):
    from rez_manager.adapter.context import load_context, save_context

    context_path = temp_context_dir / "app.rxt"
    save_context(
        [str(rez_package_matrix["app_request"])],
        str(context_path),
        package_paths=[str(temp_packages_dir)],
    )

    result = load_context(str(context_path))

    assert set(result.packages) == {"app-1.0.0", "python-3.11"}
    assert set(result.tools) == {"app", "python"}
    assert Path(result.environ["APP_HOME"]).samefile(Path(rez_package_matrix["app_dir"]))


def test_load_context_wraps_invalid_serialized_context(temp_context_dir: Path, initialized_rez):
    from rez.exceptions import ResolvedContextError

    from rez_manager.adapter.context import load_context
    from rez_manager.exceptions import RezContextLoadError

    context_path = temp_context_dir / "invalid.rxt"
    context_path.write_text("not a rez context", encoding="utf-8")

    with pytest.raises(RezContextLoadError) as exc_info:
        load_context(str(context_path))

    assert isinstance(exc_info.value.__cause__, ResolvedContextError)
