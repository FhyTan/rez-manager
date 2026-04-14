"""Tests for models and lightweight backend storage."""

from __future__ import annotations

import pytest

from rez_manager.models.project import Project
from rez_manager.models.rez_context import RezContext


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
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.context_store import list_contexts
    from rez_manager.persistence.project_store import list_projects
    from rez_manager.persistence.settings_store import load_settings, save_settings

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
    from rez_manager.persistence.settings_store import load_settings

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    (tmp_path / "settings.json").write_text("{invalid json", encoding="utf-8")

    with pytest.warns(RuntimeWarning, match="Failed to load settings"):
        settings = load_settings()

    assert settings.package_repositories == []
    assert settings.contexts_location == str(tmp_path / "contexts")


def test_platformdirs_paths_used_without_override(tmp_path, monkeypatch):
    from rez_manager.persistence import app_paths, settings_store

    config_root = tmp_path / "config-root"
    data_root = tmp_path / "data-root"
    monkeypatch.delenv("REZ_MANAGER_HOME", raising=False)
    monkeypatch.setattr(app_paths, "user_config_path", lambda *args, **kwargs: config_root)
    monkeypatch.setattr(app_paths, "user_data_path", lambda *args, **kwargs: data_root)

    assert app_paths.app_config_dir() == config_root
    assert app_paths.app_data_dir() == data_root
    assert app_paths.settings_file_path() == config_root / "settings.json"
    assert settings_store.default_settings().contexts_location == str(data_root / "contexts")


def test_list_contexts_skips_invalid_metadata(tmp_path):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.context_store import list_contexts, list_project_contexts

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

    with pytest.warns(RuntimeWarning, match="Skipping invalid context metadata"):
        project_contexts = list_project_contexts(
            "Pipeline",
            AppSettings(contexts_location=str(contexts_root)),
        )

    assert [context.name for context in project_contexts] == ["Valid Context"]


def test_project_contexts_are_lazy_loaded_and_cached(tmp_path, monkeypatch):
    from rez_manager.models.rez_context import ContextMeta, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))
    project = Project.create("Pipeline")
    RezContext.create("Pipeline", ContextMeta(name="Base", packages=[]))

    assert project.contexts is None
    assert [context.name for context in project.load_contexts()] == ["Base"]
    assert [context.name for context in project.contexts or []] == ["Base"]

    RezContext.create("Pipeline", ContextMeta(name="Render", packages=[]))

    assert [context.name for context in project.contexts or []] == ["Base"]
    assert [context.name for context in project.load_contexts()] == ["Base", "Render"]


def test_list_projects_ignores_file_contexts_location(tmp_path):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.project_store import list_projects

    file_path = tmp_path / "not-a-directory.txt"
    file_path.write_text("x", encoding="utf-8")

    assert list_projects(AppSettings(contexts_location=str(file_path))) == []


def test_project_list_model_project_names_refresh_on_reload(tmp_path, monkeypatch):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
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


def test_context_list_model_refresh_updates_revision_and_loaded_contexts(tmp_path, monkeypatch):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.main_window import ProjectListModel, RezContextListModel

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    contexts_root = tmp_path / "contexts"
    save_settings(AppSettings(contexts_location=str(contexts_root)))

    project_model = ProjectListModel()
    model = RezContextListModel()
    model.projectModel = project_model
    initial_revision = model.revision
    assert model.count == 0

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

    project_model.reload()
    assert project_model.get_project("Pipeline").contexts is None
    model.loadProject("Pipeline")

    assert model.revision > initial_revision
    assert model.count == 1
    assert len(model.filteredContexts("Pipeline")) == 1
    assert [context.name for context in project_model.get_project("Pipeline").contexts or []] == [
        "Context A"
    ]


def test_storage_project_crud_roundtrip(tmp_path, monkeypatch):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.project_store import list_projects
    from rez_manager.persistence.settings_store import save_settings

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    settings = AppSettings(contexts_location=str(tmp_path / "contexts"))
    save_settings(settings)

    created = Project.create("Pipeline")
    renamed = Project.load("Pipeline").rename("Pipeline Renamed")
    duplicated = Project.load("Pipeline Renamed").duplicate("Pipeline Copy")

    assert created.name == "Pipeline"
    assert renamed.name == "Pipeline Renamed"
    assert duplicated.name == "Pipeline Copy"
    assert [project.name for project in list_projects()] == [
        "Pipeline Copy",
        "Pipeline Renamed",
    ]

    Project.load("Pipeline Copy").delete()

    assert [project.name for project in list_projects()] == ["Pipeline Renamed"]


def test_storage_project_rename_updates_case_only_names_on_windows(tmp_path, monkeypatch):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    settings = AppSettings(contexts_location=str(tmp_path / "contexts"))
    save_settings(settings)
    Project.create("Pipeline")

    renamed = Project.load("Pipeline").rename("pipeline")

    assert renamed.name == "pipeline"
    assert [path.name for path in (tmp_path / "contexts").iterdir()] == ["pipeline"]


def test_storage_context_crud_roundtrip(tmp_path, monkeypatch):
    from rez_manager.models.project import Project
    from rez_manager.models.rez_context import ContextMeta, LaunchTarget, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.context_store import list_contexts
    from rez_manager.persistence.filesystem import (
        CONTEXT_FILE_NAME,
        META_FILE_NAME,
        THUMBNAIL_FILE_NAME,
    )
    from rez_manager.persistence.settings_store import save_settings

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    settings = AppSettings(contexts_location=str(tmp_path / "contexts"))
    save_settings(settings)
    Project.create("Pipeline")
    Project.create("Shots")

    created = RezContext.create(
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

    edited = RezContext.load("Pipeline", "Base").update(
        "Shots",
        ContextMeta(
            name="Shot Base",
            description="Moved context",
            launch_target=LaunchTarget.CUSTOM,
            custom_command="nuke -x %f",
            packages=["python-3.11"],
        ),
    )

    duplicated = RezContext.load("Shots", "Shot Base").duplicate("Pipeline", "Shot Base Copy")

    assert created.project_name == "Pipeline"
    assert edited.project_name == "Shots"
    assert edited.name == "Shot Base"
    assert duplicated.project_name == "Pipeline"
    assert duplicated.name == "Shot Base Copy"
    assert (tmp_path / "contexts" / "Pipeline" / "Shot Base Copy" / CONTEXT_FILE_NAME).exists()
    assert (tmp_path / "contexts" / "Pipeline" / "Shot Base Copy" / THUMBNAIL_FILE_NAME).exists()
    assert (tmp_path / "contexts" / "Pipeline" / "Shot Base Copy" / META_FILE_NAME).read_text(
        encoding="utf-8"
    ).find('"name": "Shot Base Copy"') >= 0

    RezContext.load("Pipeline", "Shot Base Copy").delete()

    contexts = list_contexts()
    assert sorted((context.project_name, context.name) for context in contexts) == [
        ("Shots", "Shot Base"),
    ]


def test_storage_context_edit_rejects_partial_original_identity(tmp_path, monkeypatch):
    from rez_manager.models.rez_context import ContextMeta
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.context_store import save_context
    from rez_manager.persistence.settings_store import save_settings

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    settings = AppSettings(contexts_location=str(tmp_path / "contexts"))
    save_settings(settings)
    Project.create("Pipeline")

    with pytest.raises(ValueError, match="must both be provided"):
        save_context(
            "Pipeline",
            ContextMeta(name="Base", packages=[]),
            original_project_name="Pipeline",
            original_context_name=None,
            settings=settings,
        )


def test_storage_context_rename_updates_case_only_names_on_windows(tmp_path, monkeypatch):
    from rez_manager.models.rez_context import ContextMeta
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    settings = AppSettings(contexts_location=str(tmp_path / "contexts"))
    save_settings(settings)
    Project.create("Pipeline")
    RezContext.create("Pipeline", ContextMeta(name="Base", packages=[]))

    edited = RezContext.load("Pipeline", "Base").update(
        "Pipeline",
        ContextMeta(name="base", packages=[]),
    )

    assert edited.name == "base"
    assert [path.name for path in (tmp_path / "contexts" / "Pipeline").iterdir()] == ["base"]


def test_storage_rejects_duplicate_names_and_invalid_separators(tmp_path, monkeypatch):
    from rez_manager.models.rez_context import ContextMeta
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    settings = AppSettings(contexts_location=str(tmp_path / "contexts"))
    save_settings(settings)
    Project.create("Pipeline")

    with pytest.raises(ValueError, match="already exists"):
        Project.create("Pipeline")

    with pytest.raises(ValueError, match="invalid path characters"):
        Project.create("Bad/Name")

    RezContext.create("Pipeline", ContextMeta(name="Base", packages=[]))

    with pytest.raises(ValueError, match="already exists"):
        Project.load("Pipeline").duplicate("Pipeline")

    with pytest.raises(ValueError, match="already exists"):
        RezContext.create("Pipeline", ContextMeta(name="Base", packages=[]))


def test_project_list_model_project_crud_slots(tmp_path, monkeypatch):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
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
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.main_window import ProjectListModel, RezContextListModel

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    settings = AppSettings(contexts_location=str(tmp_path / "contexts"))
    save_settings(settings)
    Project.create("Pipeline")
    Project.create("Shots")

    project_model = ProjectListModel()
    model = RezContextListModel()
    model.projectModel = project_model
    model.loadProject("Pipeline")

    assert model.saveContext("", "", "Pipeline", "Base", "Base context", "shell", "", [])
    assert [
        context.name for context in project_model.get_project("Pipeline").contexts or []
    ] == ["Base"]
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
    assert project_model.get_project("Pipeline").contexts == []
    assert project_model.get_project("Shots").contexts is None
    assert model.duplicateContext("Shots", "Shot Base", "Pipeline", "Shot Base Copy")
    model.loadProject("Pipeline")
    assert model.deleteContext("Pipeline", "Shot Base Copy")
    model.loadProject("Shots")
    assert [(item["project"], item["name"]) for item in model.filteredContexts("Shots")] == [
        ("Shots", "Shot Base"),
    ]


def test_app_settings_controller_reload_exposes_saved_settings(tmp_path, monkeypatch):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.settings_controller import AppSettingsController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(
        AppSettings(
            package_repositories=["D:\\packages\\maya", "D:\\packages\\base"],
            contexts_location=str(tmp_path / "contexts"),
        )
    )

    controller = AppSettingsController()

    assert controller.packageRepositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert controller.contextsLocation == str(tmp_path / "contexts")
    assert controller.lastError == ""


def test_app_settings_controller_save_updates_settings_file(tmp_path, monkeypatch):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import load_settings, save_settings
    from rez_manager.ui.settings_controller import AppSettingsController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))

    controller = AppSettingsController()

    assert controller.save(
        ["  D:\\packages\\maya  ", "", "D:\\packages\\base"],
        f"  {tmp_path / 'new-contexts'}  ",
    )

    settings = load_settings()
    assert settings.package_repositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert settings.contexts_location == str(tmp_path / "new-contexts")
    assert controller.packageRepositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert controller.contextsLocation == str(tmp_path / "new-contexts")


def test_app_settings_controller_save_rejects_blank_contexts_location(tmp_path, monkeypatch):
    from rez_manager.ui.settings_controller import AppSettingsController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))

    controller = AppSettingsController()

    assert not controller.save(["D:\\packages\\maya"], "   ")
    assert controller.lastError == "Contexts location is required."
