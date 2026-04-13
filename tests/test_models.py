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


def test_app_settings_normalize_pathlike_inputs():
    from pathlib import Path

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


def test_platformdirs_paths_used_without_override(tmp_path, monkeypatch):
    from rez_manager.adapter import storage

    config_root = tmp_path / "config-root"
    data_root = tmp_path / "data-root"
    monkeypatch.delenv("REZ_MANAGER_HOME", raising=False)
    monkeypatch.setattr(storage, "user_config_path", lambda *args, **kwargs: config_root)
    monkeypatch.setattr(storage, "user_data_path", lambda *args, **kwargs: data_root)

    assert storage.app_config_dir() == config_root
    assert storage.app_data_dir() == data_root
    assert storage.settings_file_path() == config_root / "settings.json"
    assert storage.default_settings().contexts_location == str(data_root / "contexts")


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


def test_storage_project_crud_roundtrip(tmp_path):
    from rez_manager.adapter.storage import (
        create_project,
        delete_project,
        duplicate_project,
        list_projects,
        rename_project,
    )
    from rez_manager.models.settings import AppSettings

    settings = AppSettings(contexts_location=str(tmp_path / "contexts"))

    created = create_project(settings, "Pipeline")
    renamed = rename_project(settings, "Pipeline", "Pipeline Renamed")
    duplicated = duplicate_project(settings, "Pipeline Renamed", "Pipeline Copy")

    assert created.name == "Pipeline"
    assert renamed.name == "Pipeline Renamed"
    assert duplicated.name == "Pipeline Copy"
    assert [project.name for project in list_projects(settings)] == [
        "Pipeline Copy",
        "Pipeline Renamed",
    ]

    delete_project(settings, "Pipeline Copy")

    assert [project.name for project in list_projects(settings)] == ["Pipeline Renamed"]


def test_storage_project_rename_updates_case_only_names_on_windows(tmp_path):
    from rez_manager.adapter.storage import create_project, rename_project
    from rez_manager.models.settings import AppSettings

    settings = AppSettings(contexts_location=str(tmp_path / "contexts"))
    create_project(settings, "Pipeline")

    renamed = rename_project(settings, "Pipeline", "pipeline")

    assert renamed.name == "pipeline"
    assert [path.name for path in (tmp_path / "contexts").iterdir()] == ["pipeline"]


def test_storage_context_crud_roundtrip(tmp_path):
    from rez_manager.adapter.storage import (
        CONTEXT_FILE_NAME,
        META_FILE_NAME,
        THUMBNAIL_FILE_NAME,
        create_project,
        delete_context,
        duplicate_context,
        list_contexts,
        save_context,
    )
    from rez_manager.models.rez_context import ContextMeta, LaunchTarget
    from rez_manager.models.settings import AppSettings

    settings = AppSettings(contexts_location=str(tmp_path / "contexts"))
    create_project(settings, "Pipeline")
    create_project(settings, "Shots")

    created = save_context(
        settings,
        "Pipeline",
        ContextMeta(
            name="Base",
            description="Base context",
            launch_target=LaunchTarget.SHELL,
            packages=["python-3.11"],
        ),
    )
    source_context_dir = tmp_path / "contexts" / "Pipeline" / "Base"
    (source_context_dir / CONTEXT_FILE_NAME).write_text("resolved", encoding="utf-8")
    (source_context_dir / THUMBNAIL_FILE_NAME).write_bytes(b"png")

    edited = save_context(
        settings,
        "Shots",
        ContextMeta(
            name="Shot Base",
            description="Moved context",
            launch_target=LaunchTarget.CUSTOM,
            custom_command="nuke -x %f",
            packages=["python-3.11"],
        ),
        original_project_name="Pipeline",
        original_context_name="Base",
    )

    duplicated = duplicate_context(settings, "Shots", "Shot Base", "Pipeline", "Shot Base Copy")

    assert created.project_name == "Pipeline"
    assert edited.project_name == "Shots"
    assert edited.name == "Shot Base"
    assert duplicated.project_name == "Pipeline"
    assert duplicated.name == "Shot Base Copy"
    assert (tmp_path / "contexts" / "Pipeline" / "Shot Base Copy" / CONTEXT_FILE_NAME).exists()
    assert (tmp_path / "contexts" / "Pipeline" / "Shot Base Copy" / THUMBNAIL_FILE_NAME).exists()
    assert (
        tmp_path / "contexts" / "Pipeline" / "Shot Base Copy" / META_FILE_NAME
    ).read_text(encoding="utf-8").find('"name": "Shot Base Copy"') >= 0

    delete_context(settings, "Pipeline", "Shot Base Copy")

    contexts = list_contexts(settings)
    assert sorted((context.project_name, context.name) for context in contexts) == [
        ("Shots", "Shot Base"),
    ]


def test_storage_context_edit_rejects_partial_original_identity(tmp_path):
    from rez_manager.adapter.storage import create_project, save_context
    from rez_manager.models.rez_context import ContextMeta
    from rez_manager.models.settings import AppSettings

    settings = AppSettings(contexts_location=str(tmp_path / "contexts"))
    create_project(settings, "Pipeline")

    with pytest.raises(ValueError, match="must both be provided"):
        save_context(
            settings,
            "Pipeline",
            ContextMeta(name="Base", packages=[]),
            original_project_name="Pipeline",
            original_context_name=None,
        )


def test_storage_context_rename_updates_case_only_names_on_windows(tmp_path):
    from rez_manager.adapter.storage import create_project, save_context
    from rez_manager.models.rez_context import ContextMeta
    from rez_manager.models.settings import AppSettings

    settings = AppSettings(contexts_location=str(tmp_path / "contexts"))
    create_project(settings, "Pipeline")
    save_context(settings, "Pipeline", ContextMeta(name="Base", packages=[]))

    edited = save_context(
        settings,
        "Pipeline",
        ContextMeta(name="base", packages=[]),
        original_project_name="Pipeline",
        original_context_name="Base",
    )

    assert edited.name == "base"
    assert [path.name for path in (tmp_path / "contexts" / "Pipeline").iterdir()] == ["base"]


def test_storage_rejects_duplicate_names_and_invalid_separators(tmp_path):
    from rez_manager.adapter.storage import create_project, duplicate_project, save_context
    from rez_manager.models.rez_context import ContextMeta
    from rez_manager.models.settings import AppSettings

    settings = AppSettings(contexts_location=str(tmp_path / "contexts"))
    create_project(settings, "Pipeline")

    with pytest.raises(ValueError, match="already exists"):
        create_project(settings, "Pipeline")

    with pytest.raises(ValueError, match="invalid path characters"):
        create_project(settings, "Bad/Name")

    save_context(settings, "Pipeline", ContextMeta(name="Base", packages=[]))

    with pytest.raises(ValueError, match="already exists"):
        duplicate_project(settings, "Pipeline", "Pipeline")

    with pytest.raises(ValueError, match="already exists"):
        save_context(settings, "Pipeline", ContextMeta(name="Base", packages=[]))


def test_project_list_model_project_crud_slots(tmp_path, monkeypatch):
    from rez_manager.adapter.storage import save_settings
    from rez_manager.models.settings import AppSettings
    from rez_manager.ui.main_window import ProjectListModel

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))

    model = ProjectListModel()

    assert model.createProject("Pipeline")
    assert model.renameProject("Pipeline", "Pipeline Renamed")
    assert model.duplicateProject("Pipeline Renamed", "Pipeline Copy")
    assert model.deleteProject("Pipeline Copy")
    assert model.projectNames == ["Pipeline Renamed"]


def test_context_list_model_context_crud_slots(tmp_path, monkeypatch):
    from rez_manager.adapter.storage import create_project, save_settings
    from rez_manager.models.settings import AppSettings
    from rez_manager.ui.main_window import RezContextListModel

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    settings = AppSettings(contexts_location=str(tmp_path / "contexts"))
    save_settings(settings)
    create_project(settings, "Pipeline")
    create_project(settings, "Shots")

    model = RezContextListModel()

    assert model.saveContext("", "", "Pipeline", "Base", "Base context", "shell", "", [])
    assert model.saveContext(
        "Pipeline",
        "Base",
        "Shots",
        "Shot Base",
        "Moved context",
        "custom",
        "nuke -x %f",
        ["python-3.11"],
    )
    assert model.duplicateContext("Shots", "Shot Base", "Pipeline", "Shot Base Copy")
    assert model.deleteContext("Pipeline", "Shot Base Copy")
    assert [(item["project"], item["name"]) for item in model.filteredContexts("Shots")] == [
        ("Shots", "Shot Base"),
    ]
