"""Tests for data-oriented models."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_context_meta_roundtrip():
    from rez_manager.models.rez_context import ContextMeta, LaunchTarget

    meta = ContextMeta(
        name="test-env",
        description="A test environment",
        launch_target=LaunchTarget.MAYA,
        builtin_thumbnail_source="qrc:/icons/dcc/Maya",
        packages=["maya-2024", "python-3.11"],
    )
    data = meta.to_dict()
    restored = ContextMeta.from_dict(data)

    assert restored.name == meta.name
    assert restored.launch_target == LaunchTarget.MAYA
    assert restored.builtin_thumbnail_source == "qrc:/icons/dcc/Maya"
    assert restored.packages == ["maya-2024", "python-3.11"]


def test_context_meta_accepts_new_launch_targets():
    from rez_manager.models.rez_context import ContextMeta, LaunchTarget

    restored = ContextMeta.from_dict(
        {
            "name": "comp-env",
            "description": "NukeX comp environment",
            "launch_target": "nukex",
            "custom_command": None,
            "packages": ["nukex-15.0"],
        }
    )

    assert restored.launch_target == LaunchTarget.NUKE_X


def test_project_display_name():
    from rez_manager.models.project import Project

    project = Project(name="my-project")
    assert project.display_name == "my-project"


def test_app_settings_roundtrip():
    from rez_manager.models.settings import AppSettings

    settings = AppSettings(
        package_repositories=["D:\\packages\\maya", "D:\\packages\\base"],
        contexts_location="D:\\contexts",
    )

    restored = AppSettings.from_dict(settings.to_dict())

    assert restored.package_repositories == settings.package_repositories
    assert restored.contexts_location == settings.contexts_location


def test_app_settings_normalize_pathlike_inputs():
    from rez_manager.models.settings import AppSettings

    settings = AppSettings(
        package_repositories=[Path("D:\\packages\\maya"), Path("D:\\packages\\base")],
        contexts_location=Path("D:\\contexts"),
    )

    assert settings.to_dict() == {
        "package_repositories": ["D:\\packages\\maya", "D:\\packages\\base"],
        "contexts_location": "D:\\contexts",
    }


def test_context_meta_rejects_invalid_package_types():
    from rez_manager.models.rez_context import ContextMeta

    with pytest.raises(TypeError, match="packages must be a list of strings"):
        ContextMeta.from_dict(
            {
                "name": "Broken Context",
                "description": "Invalid packages payload",
                "launch_target": "shell",
                "custom_command": None,
                "packages": "python-3.11",
            }
        )


def test_context_meta_rejects_invalid_builtin_thumbnail_source():
    from rez_manager.models.rez_context import ContextMeta

    with pytest.raises(TypeError, match="builtin_thumbnail_source must be a string or null"):
        ContextMeta.from_dict(
            {
                "name": "Broken Context",
                "description": "Invalid thumbnail metadata",
                "launch_target": "shell",
                "custom_command": None,
                "builtin_thumbnail_source": ["qrc:/icons/dcc/Shell"],
                "packages": [],
            }
        )
