"""Tests for launch target registry behavior."""

from __future__ import annotations

import pytest


def test_launch_target_catalog_preserves_ui_order():
    from rez_manager.models.launch_target import LAUNCH_TARGETS

    assert [target.value.value for target in LAUNCH_TARGETS.all()] == [
        "Shell",
        "Maya",
        "Houdini",
        "Blender",
        "Nuke",
        "NukeX",
        "Custom",
    ]


def test_launch_target_catalog_resolves_commands():
    from rez_manager.models.launch_target import LAUNCH_TARGETS, LaunchTarget

    assert LAUNCH_TARGETS.command_for(LaunchTarget.MAYA) == "maya"
    assert LAUNCH_TARGETS.command_for("Shell") is None
    assert LAUNCH_TARGETS.command_for("Custom", custom_command="  nuke -x %f  ") == "nuke -x %f"


def test_launch_target_catalog_rejects_blank_custom_command():
    from rez_manager.models.launch_target import LAUNCH_TARGETS

    with pytest.raises(ValueError, match="Custom launch target requires a custom command"):
        LAUNCH_TARGETS.command_for("Custom", custom_command="   ")


def test_launch_target_catalog_wraps_windows_launch_commands(monkeypatch):
    from rez_manager.models.launch_target import LAUNCH_TARGETS

    monkeypatch.setattr("rez_manager.models.launch_target.IS_WINDOWS", True)

    assert LAUNCH_TARGETS.launch_command_for("Maya") == 'start "" maya'
    assert LAUNCH_TARGETS.launch_command_for("Shell") is None
