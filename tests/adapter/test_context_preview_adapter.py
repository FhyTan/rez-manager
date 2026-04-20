"""Tests for context preview data helpers."""

from __future__ import annotations

import sys
import types
from types import SimpleNamespace


def test_system_environment_variable_names_include_supported_platforms():
    from rez_manager.adapter.context import system_environment_variable_names

    assert "SYSTEMROOT" in system_environment_variable_names("windows")
    assert "XDG_RUNTIME_DIR" in system_environment_variable_names("linux")
    assert "__CF_USER_TEXT_ENCODING" in system_environment_variable_names("macos")


def test_build_environment_sections_splits_user_system_and_rez_sections():
    from rez_manager.adapter.context import build_environment_sections

    sections = build_environment_sections(
        effective_environ={
            "MAYA_LOCATION": "D:\\packages\\maya\\2025.0",
            "PATH": "D:\\packages\\maya\\2025.0\\bin;C:\\Windows\\System32",
            "SYSTEMROOT": "C:\\Windows",
            "REZ_USED_RESOLVE": "maya-2025.0 python-3.11",
        },
        preserved_system_environ={
            "PATH": "C:\\Windows\\System32",
            "SYSTEMROOT": "C:\\Windows",
            "TEMP": "C:\\Temp",
        },
        platform_name="windows",
    )

    sections_by_title = {section.title: section.variables for section in sections}
    user_keys = list(sections_by_title["User Environment"].keys())
    system_keys = list(sections_by_title["System Environment"].keys())

    assert sections_by_title["User Environment"] == {
        "MAYA_LOCATION": "D:\\packages\\maya\\2025.0",
        "PATH": "D:\\packages\\maya\\2025.0\\bin;C:\\Windows\\System32",
    }
    assert sections_by_title["System Environment"] == {
        "SYSTEMROOT": "C:\\Windows",
        "TEMP": "C:\\Temp",
    }
    assert sections_by_title["REZ_ Environment"] == {
        "REZ_USED_RESOLVE": "maya-2025.0 python-3.11",
    }
    assert user_keys[-1] == "PATH"
    assert "PATH" not in system_keys


def test_preserved_system_environment_uses_case_insensitive_matching_on_windows():
    from rez_manager.adapter.context import preserved_system_environment

    preserved = preserved_system_environment(
        process_environ={
            "Path": "C:\\Windows\\System32",
            "SystemRoot": "C:\\Windows",
            "TEMP": "C:\\Temp",
            "UNRELATED": "ignored",
        },
        platform_name="windows",
    )

    assert preserved == {
        "Path": "C:\\Windows\\System32",
        "SystemRoot": "C:\\Windows",
        "TEMP": "C:\\Temp",
    }


def test_build_environment_sections_sorts_windows_path_last_and_hides_system_path():
    from rez_manager.adapter.context import build_environment_sections

    sections = build_environment_sections(
        effective_environ={
            "AAA": "1",
            "PATH": "D:\\packages\\maya\\bin;C:\\Windows\\System32",
        },
        preserved_system_environ={
            "Path": "C:\\Windows\\System32",
            "ComSpec": "C:\\Windows\\System32\\cmd.exe",
        },
        platform_name="windows",
    )

    sections_by_title = {section.title: section.variables for section in sections}

    assert list(sections_by_title["User Environment"].keys()) == ["AAA", "PATH"]
    assert list(sections_by_title["System Environment"].keys()) == ["ComSpec"]


def test_resolve_context_passes_package_paths_to_rez(monkeypatch):
    from rez_manager.adapter.context import resolve_context

    captured: dict[str, object] = {}

    class FakeResolvedContext:
        def __init__(self, package_requests, *, package_paths=None):
            captured["package_requests"] = list(package_requests)
            captured["package_paths"] = package_paths
            self.resolved_packages = [SimpleNamespace(qualified_package_name="maya-2025.0")]

        def get_environ(self, *, parent_environ=None):
            return {"PATH": "C:\\Windows\\System32", "REZ_USED_RESOLVE": "maya-2025.0"}

        def get_tools(self):
            return {"maya.exe": object()}

    rez_module = types.ModuleType("rez")
    resolved_context_module = types.ModuleType("rez.resolved_context")
    resolved_context_module.ResolvedContext = FakeResolvedContext
    monkeypatch.setitem(sys.modules, "rez", rez_module)
    monkeypatch.setitem(sys.modules, "rez.resolved_context", resolved_context_module)

    result = resolve_context(["maya-2025.0"], package_paths=["D:\\packages\\maya"])

    assert result.success is True
    assert captured["package_requests"] == ["maya-2025.0"]
    assert captured["package_paths"] == ["D:\\packages\\maya"]


def test_save_context_passes_package_paths_to_rez(monkeypatch, tmp_path):
    from rez_manager.adapter.context import save_context

    captured: dict[str, object] = {}

    class FakeResolvedContext:
        def __init__(self, package_requests, *, package_paths=None):
            captured["package_requests"] = list(package_requests)
            captured["package_paths"] = package_paths

        def save(self, path):
            captured["save_path"] = path

    rez_module = types.ModuleType("rez")
    resolved_context_module = types.ModuleType("rez.resolved_context")
    resolved_context_module.ResolvedContext = FakeResolvedContext
    monkeypatch.setitem(sys.modules, "rez", rez_module)
    monkeypatch.setitem(sys.modules, "rez.resolved_context", resolved_context_module)

    success, error = save_context(
        ["maya-2025.0"],
        str(tmp_path / "context.rxt"),
        package_paths=["D:\\packages\\maya"],
    )

    assert success is True
    assert error == ""
    assert captured["package_paths"] == ["D:\\packages\\maya"]
    assert captured["save_path"] == str(tmp_path / "context.rxt")


def test_launch_context_passes_package_paths_to_rez(monkeypatch):
    from rez_manager.adapter.context import launch_context

    captured: dict[str, object] = {}

    class FakeResolvedContext:
        def __init__(self, package_requests, *, package_paths=None):
            captured["package_requests"] = list(package_requests)
            captured["package_paths"] = package_paths

        def execute_shell(self, **kwargs):
            captured["execute_shell"] = kwargs
            return "process"

    rez_module = types.ModuleType("rez")
    resolved_context_module = types.ModuleType("rez.resolved_context")
    resolved_context_module.ResolvedContext = FakeResolvedContext
    monkeypatch.setitem(sys.modules, "rez", rez_module)
    monkeypatch.setitem(sys.modules, "rez.resolved_context", resolved_context_module)

    process = launch_context(
        ["maya-2025.0"],
        ["maya.exe"],
        package_paths=["D:\\packages\\maya"],
    )

    assert process == "process"
    assert captured["package_paths"] == ["D:\\packages\\maya"]
    assert captured["execute_shell"]["command"] == ["maya.exe"]
