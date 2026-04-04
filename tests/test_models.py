"""Tests for the rez adapter layer."""

from __future__ import annotations

import pytest


def test_context_meta_roundtrip():
    from rez_manager.models.rez_context import ContextMeta, LaunchTarget

    meta = ContextMeta(
        name="test-env",
        description="A test environment",
        launch_target=LaunchTarget.MAYA,
        packages=["maya-2024", "python-3.11"],
    )
    data = meta.to_dict()
    restored = ContextMeta.from_dict(data)

    assert restored.name == meta.name
    assert restored.launch_target == LaunchTarget.MAYA
    assert restored.packages == ["maya-2024", "python-3.11"]


def test_project_display_name():
    from rez_manager.models.project import Project

    p = Project(name="my-project")
    assert p.display_name == "my-project"
