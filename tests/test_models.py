"""Tests for models and lightweight backend storage."""

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


def test_app_settings_roundtrip():
    from rez_manager.models.settings import AppSettings

    settings = AppSettings(
        package_repositories=["D:\\packages\\maya", "D:\\packages\\base"],
        contexts_location="D:\\contexts",
    )

    restored = AppSettings.from_dict(settings.to_dict())

    assert restored.package_repositories == settings.package_repositories
    assert restored.contexts_location == settings.contexts_location


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


def test_storage_discovers_projects_and_contexts(tmp_path, monkeypatch):
    from rez_manager.adapter.storage import (
        list_contexts,
        list_projects,
        load_settings,
        save_settings,
    )
    from rez_manager.models.settings import AppSettings

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    contexts_root = tmp_path / "contexts"
    context_dir = contexts_root / "Pipeline" / "Maya Base"
    context_dir.mkdir(parents=True)
    (context_dir / "meta.json").write_text(
        (
            "{\n"
            '  "name": "Maya Base",\n'
            '  "description": "Primary Maya context",\n'
            '  "launch_target": "maya",\n'
            '  "custom_command": null,\n'
            '  "packages": ["maya-2024", "python-3.11"]\n'
            "}\n"
        ),
        encoding="utf-8",
    )

    save_settings(
        AppSettings(
            package_repositories=["D:\\packages\\maya"],
            contexts_location=str(contexts_root),
        )
    )

    settings = load_settings()
    projects = list_projects(settings)
    contexts = list_contexts(settings)

    assert [project.name for project in projects] == ["Pipeline"]
    assert len(contexts) == 1
    assert contexts[0].project_name == "Pipeline"
    assert contexts[0].name == "Maya Base"
    assert contexts[0].packages == ["maya-2024", "python-3.11"]


def test_load_settings_falls_back_to_default_on_invalid_json(tmp_path, monkeypatch):
    from rez_manager.adapter.storage import load_settings

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    (tmp_path / "settings.json").write_text("{invalid json", encoding="utf-8")

    with pytest.warns(RuntimeWarning, match="Failed to load settings"):
        settings = load_settings()

    assert settings.package_repositories == []
    assert settings.contexts_location == str(tmp_path / "contexts")


def test_list_contexts_skips_invalid_metadata(tmp_path):
    from rez_manager.adapter.storage import list_contexts
    from rez_manager.models.settings import AppSettings

    contexts_root = tmp_path / "contexts"
    valid_context_dir = contexts_root / "Pipeline" / "Valid Context"
    invalid_context_dir = contexts_root / "Pipeline" / "Broken Context"
    valid_context_dir.mkdir(parents=True)
    invalid_context_dir.mkdir(parents=True)

    (valid_context_dir / "meta.json").write_text(
        (
            "{\n"
            '  "name": "Valid Context",\n'
            '  "description": "Works",\n'
            '  "launch_target": "shell",\n'
            '  "custom_command": null,\n'
            '  "packages": ["python-3.11"]\n'
            "}\n"
        ),
        encoding="utf-8",
    )
    (invalid_context_dir / "meta.json").write_text(
        (
            "{\n"
            '  "description": "Missing name",\n'
            '  "launch_target": "bad-target",\n'
            '  "custom_command": null,\n'
            '  "packages": []\n'
            "}\n"
        ),
        encoding="utf-8",
    )

    with pytest.warns(RuntimeWarning, match="Skipping invalid context metadata"):
        contexts = list_contexts(AppSettings(contexts_location=str(contexts_root)))

    assert [context.name for context in contexts] == ["Valid Context"]


def test_list_projects_ignores_file_contexts_location(tmp_path):
    from rez_manager.adapter.storage import list_projects
    from rez_manager.models.settings import AppSettings

    file_path = tmp_path / "not-a-directory.txt"
    file_path.write_text("x", encoding="utf-8")

    assert list_projects(AppSettings(contexts_location=str(file_path))) == []


def test_project_list_model_project_names_refresh_on_reload(tmp_path, monkeypatch):
    from rez_manager.adapter.storage import save_settings
    from rez_manager.models.settings import AppSettings
    from rez_manager.ui.main_window import ProjectListModel

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    contexts_root = tmp_path / "contexts"
    save_settings(AppSettings(contexts_location=str(contexts_root)))

    model = ProjectListModel()
    initial_revision = model.revision
    assert model.projectNames == []

    context_dir = contexts_root / "Pipeline" / "Context A"
    context_dir.mkdir(parents=True)
    (context_dir / "meta.json").write_text(
        (
            "{\n"
            '  "name": "Context A",\n'
            '  "description": "Created later",\n'
            '  "launch_target": "shell",\n'
            '  "custom_command": null,\n'
            '  "packages": ["python-3.11"]\n'
            "}\n"
        ),
        encoding="utf-8",
    )

    model.reload()

    assert model.revision > initial_revision
    assert model.projectNames == ["Pipeline"]


def test_context_list_model_refresh_updates_revision_and_counts(tmp_path, monkeypatch):
    from rez_manager.adapter.storage import save_settings
    from rez_manager.models.settings import AppSettings
    from rez_manager.ui.main_window import RezContextListModel

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    contexts_root = tmp_path / "contexts"
    save_settings(AppSettings(contexts_location=str(contexts_root)))

    model = RezContextListModel()
    initial_revision = model.revision
    assert model.contextCountFor("Pipeline") == 0

    context_dir = contexts_root / "Pipeline" / "Context A"
    context_dir.mkdir(parents=True)
    (context_dir / "meta.json").write_text(
        (
            "{\n"
            '  "name": "Context A",\n'
            '  "description": "Created later",\n'
            '  "launch_target": "shell",\n'
            '  "custom_command": null,\n'
            '  "packages": ["python-3.11"]\n'
            "}\n"
        ),
        encoding="utf-8",
    )

    model.reload()

    assert model.revision > initial_revision
    assert model.contextCountFor("Pipeline") == 1
    assert len(model.filteredContexts("Pipeline")) == 1
