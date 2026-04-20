"""Tests for context preview data helpers."""

from __future__ import annotations


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

    assert sections_by_title["User Environment"] == {
        "MAYA_LOCATION": "D:\\packages\\maya\\2025.0",
        "PATH": "D:\\packages\\maya\\2025.0\\bin;C:\\Windows\\System32",
    }
    assert sections_by_title["System Environment"] == {
        "PATH": "C:\\Windows\\System32",
        "SYSTEMROOT": "C:\\Windows",
        "TEMP": "C:\\Temp",
    }
    assert sections_by_title["REZ_ Environment"] == {
        "REZ_USED_RESOLVE": "maya-2025.0 python-3.11",
    }


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
