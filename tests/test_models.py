"""Tests for models and lightweight backend storage."""

from __future__ import annotations

import json

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

    assert model.rowCount() == 1
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
    assert model.rowCount() == 0

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

    assert model.rowCount() == 1
    assert [item["name"] for item in model.contexts] == ["Context A"]
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


def test_project_list_model_uses_incremental_updates_for_crud(tmp_path, monkeypatch):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.main_window import ProjectListModel

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))

    model = ProjectListModel()
    inserted_rows: list[tuple[int, int]] = []
    removed_rows: list[tuple[int, int]] = []
    reset_count = 0

    model.rowsInserted.connect(lambda _parent, first, last: inserted_rows.append((first, last)))
    model.rowsRemoved.connect(lambda _parent, first, last: removed_rows.append((first, last)))
    model.modelReset.connect(lambda: inserted_rows.append((-1, -1)))

    assert model.createProject("Shots")
    assert inserted_rows == [(0, 0)]

    assert model.renameProject("Shots", "Pipeline")
    assert removed_rows == [(0, 0)]
    assert inserted_rows == [(0, 0), (0, 0)]

    assert model.duplicateProject("Pipeline", "Shots")
    assert inserted_rows[-1] == (1, 1)

    assert model.deleteProject("Shots")
    assert removed_rows[-1] == (1, 1)
    assert inserted_rows.count((-1, -1)) == reset_count


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
    assert [context.name for context in project_model.get_project("Pipeline").contexts or []] == [
        "Base"
    ]
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


def test_context_list_model_uses_incremental_updates_for_loaded_project(tmp_path, monkeypatch):
    from rez_manager.models.rez_context import LaunchTarget
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

    inserted_rows: list[tuple[int, int]] = []
    removed_rows: list[tuple[int, int]] = []
    changed_rows: list[tuple[int, int]] = []
    reset_count = 0

    model.rowsInserted.connect(lambda _parent, first, last: inserted_rows.append((first, last)))
    model.rowsRemoved.connect(lambda _parent, first, last: removed_rows.append((first, last)))
    model.dataChanged.connect(
        lambda top_left, bottom_right, _roles: changed_rows.append(
            (top_left.row(), bottom_right.row())
        )
    )
    model.modelReset.connect(lambda: changed_rows.append((-1, -1)))

    assert model.saveContext("", "", "Pipeline", "Base", "Base context", "shell", "", [])
    assert inserted_rows == [(0, 0)]

    assert model.saveContext(
        "Pipeline",
        "Base",
        "Pipeline",
        "Base",
        "Updated context",
        "custom",
        "nuke -x %f",
        ["python-3.11"],
    )
    assert changed_rows == [(0, 0)]

    assert model.saveContext(
        "Pipeline",
        "Base",
        "Pipeline",
        "Shot Base",
        "Renamed context",
        LaunchTarget.SHELL.value,
        "",
        [],
    )
    assert removed_rows == [(0, 0)]
    assert inserted_rows[-1] == (0, 0)

    assert model.saveContext(
        "Pipeline",
        "Shot Base",
        "Shots",
        "Shot Base",
        "Moved context",
        LaunchTarget.SHELL.value,
        "",
        [],
    )
    assert removed_rows[-1] == (0, 0)
    assert model.contexts == []
    assert changed_rows.count((-1, -1)) == reset_count


def test_models_report_stale_project_and_context_actions(tmp_path, monkeypatch):
    from rez_manager.models.rez_context import ContextMeta
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.main_window import ProjectListModel, RezContextListModel

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))
    Project.create("Pipeline")
    RezContext.create("Pipeline", ContextMeta(name="Base", packages=[]))

    project_model = ProjectListModel()
    context_model = RezContextListModel()
    context_model.projectModel = project_model
    context_model.loadProject("Pipeline")

    app_error_hub.clear()
    Project.load("Pipeline").delete()

    assert not project_model.ensureProjectExists("Pipeline")
    assert "Refresh the list and try again" in app_error_hub.message

    app_error_hub.clear()
    assert not context_model.ensureContextExists("Pipeline", "Base")
    assert "Refresh the list and try again" in app_error_hub.message


def test_app_settings_controller_reload_exposes_saved_settings(tmp_path, monkeypatch):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.settings_controller import AppSettingsController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(
        AppSettings(
            package_repositories=["D:\\packages\\maya", "D:\\packages\\base"],
            contexts_location=str(tmp_path / "contexts"),
        )
    )

    app_error_hub.clear()
    controller = AppSettingsController()

    assert controller.packageRepositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert controller.contextsLocation == str(tmp_path / "contexts")
    assert app_error_hub.message == ""


def test_app_settings_controller_save_updates_settings_file(tmp_path, monkeypatch):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import load_settings, save_settings
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.settings_controller import AppSettingsController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))

    app_error_hub.clear()
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
    assert app_error_hub.message == ""


def test_app_settings_controller_save_deduplicates_normalized_repositories(tmp_path, monkeypatch):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import load_settings, save_settings
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.settings_controller import AppSettingsController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))

    app_error_hub.clear()
    controller = AppSettingsController()

    assert controller.save(
        [
            "  D:\\packages\\maya\\  ",
            "d:/packages/maya",
            "D:\\packages\\base\\",
            "d:\\packages\\BASE",
        ],
        str(tmp_path / "normalized-contexts"),
    )

    settings = load_settings()
    assert settings.package_repositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert controller.packageRepositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert app_error_hub.message == ""


def test_app_settings_controller_import_from_file_updates_in_memory_state(tmp_path, monkeypatch):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import load_settings, save_settings
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.settings_controller import AppSettingsController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "saved-contexts")))

    import_path = tmp_path / "import-settings.json"
    import_path.write_text(
        json.dumps(
            {
                "package_repositories": [
                    " D:\\packages\\maya\\ ",
                    "d:/packages/maya",
                    "D:\\packages\\base",
                ],
                "contexts_location": str(tmp_path / "imported-contexts"),
            }
        ),
        encoding="utf-8",
    )

    app_error_hub.clear()
    controller = AppSettingsController()

    assert controller.importFromFile(str(import_path))
    assert controller.packageRepositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert controller.contextsLocation == str(tmp_path / "imported-contexts")
    persisted = load_settings()
    assert persisted.package_repositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert persisted.contexts_location == str(tmp_path / "imported-contexts")
    assert app_error_hub.message == ""


def test_app_settings_controller_export_to_file_writes_normalized_settings(tmp_path, monkeypatch):
    from rez_manager.persistence.settings_store import load_settings
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.settings_controller import AppSettingsController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))

    export_path = tmp_path / "exported-settings.json"

    app_error_hub.clear()
    controller = AppSettingsController()

    assert controller.exportToFile(
        [" D:\\packages\\maya\\ ", "d:/packages/maya", "D:\\packages\\base"],
        f"  {tmp_path / 'exported-contexts'}  ",
        str(export_path),
    )

    exported = json.loads(export_path.read_text(encoding="utf-8"))
    assert exported == {
        "package_repositories": ["D:\\packages\\maya", "D:\\packages\\base"],
        "contexts_location": str(tmp_path / "exported-contexts"),
    }
    persisted = load_settings()
    assert persisted.package_repositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert persisted.contexts_location == str(tmp_path / "exported-contexts")
    assert controller.packageRepositories == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert controller.contextsLocation == str(tmp_path / "exported-contexts")
    assert app_error_hub.message == ""


def test_app_settings_controller_open_path_in_file_manager(tmp_path, monkeypatch):
    import rez_manager.ui.settings_controller as settings_controller
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.settings_controller import AppSettingsController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))

    opened_urls: list[str] = []

    def fake_open_url(url):
        opened_urls.append(url.toString())
        return True

    monkeypatch.setattr(settings_controller.QDesktopServices, "openUrl", fake_open_url)

    app_error_hub.clear()
    controller = AppSettingsController()
    repository_path = tmp_path / "packages" / "maya"
    repository_path.mkdir(parents=True)

    assert controller.revealInFileExplorer(str(repository_path))
    assert opened_urls == [f"file:///{repository_path.as_posix()}"]
    assert app_error_hub.message == ""


def test_app_settings_controller_save_rejects_blank_contexts_location(tmp_path, monkeypatch):
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.settings_controller import AppSettingsController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))

    app_error_hub.clear()
    controller = AppSettingsController()

    assert not controller.save(["D:\\packages\\maya"], "   ")
    assert app_error_hub.message == "Contexts location is required."


def test_package_manager_controller_loads_context_and_repository_tree(tmp_path, monkeypatch):
    import rez_manager.ui.package_manager as package_manager
    from rez_manager.adapter.packages import RepositoryInfo
    from rez_manager.models.rez_context import ContextMeta, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.package_manager import PackageManagerController, PackageRequestListModel

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(
        AppSettings(
            package_repositories=["D:\\packages\\maya", "D:\\packages\\base"],
            contexts_location=str(tmp_path / "contexts"),
        )
    )
    Project.create("Pipeline")
    RezContext.create(
        "Pipeline",
        ContextMeta(name="Render", packages=["redshift-houdini-3.5", "python-3.11"]),
    )

    monkeypatch.setattr(
        package_manager,
        "list_repositories",
        lambda repo_paths: [
            RepositoryInfo(
                path=repo_paths[0], label=f"maya [{repo_paths[0]}]", packages=["maya", "mtoa"]
            ),
            RepositoryInfo(
                path=repo_paths[1], label=f"base [{repo_paths[1]}]", packages=["python"]
            ),
        ],
    )

    controller = PackageManagerController()

    assert controller.loadContext("Pipeline", "Render")
    assert controller.packageCount == 2
    assert controller.repositoryTree == [
        {
            "path": "D:\\packages\\maya",
            "label": "maya [D:\\packages\\maya]",
            "packages": ["maya", "mtoa"],
        },
        {
            "path": "D:\\packages\\base",
            "label": "base [D:\\packages\\base]",
            "packages": ["python"],
        },
    ]

    model = controller.packageRequestsModel
    assert isinstance(model, PackageRequestListModel)
    assert model.rowCount() == 2
    assert model.data(model.index(0, 0), PackageRequestListModel.NameRole) == "redshift-houdini"
    assert model.data(model.index(0, 0), PackageRequestListModel.VersionRole) == "3.5"


def test_package_manager_controller_selects_package_and_saves_requests(tmp_path, monkeypatch):
    import rez_manager.ui.package_manager as package_manager
    from rez_manager.adapter.packages import PackageInfo, RepositoryInfo
    from rez_manager.models.rez_context import ContextMeta, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.package_manager import PackageManagerController, PackageRequestListModel

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(
        AppSettings(
            package_repositories=["D:\\packages\\maya"],
            contexts_location=str(tmp_path / "contexts"),
        )
    )
    Project.create("Pipeline")
    RezContext.create("Pipeline", ContextMeta(name="Base", packages=["maya-2024.0", "python-3.11"]))

    monkeypatch.setattr(
        package_manager,
        "list_repositories",
        lambda repo_paths: [
            RepositoryInfo(path=repo_paths[0], label=f"maya [{repo_paths[0]}]", packages=["maya"])
        ],
    )
    monkeypatch.setattr(
        package_manager,
        "get_package_versions",
        lambda name, repo_paths: ["2025.0", "2024.0"] if name == "maya" else [],
    )
    monkeypatch.setattr(
        package_manager,
        "get_package_info",
        lambda name, version, repo_paths: PackageInfo(
            name=name,
            versions=[version],
            description=f"{name} {version}",
            requires=["python-3.11"],
            variants=[["platform-windows", "arch-x86_64"]],
            tools=["maya"],
            python_statements=f"name = '{name}'\nversion = '{version}'",
        ),
    )

    app_error_hub.clear()
    controller = PackageManagerController()

    assert controller.loadContext("Pipeline", "Base")
    assert controller.selectPackage(0, 0)
    assert controller.packageDetail["name"] == "maya"
    assert controller.packageDetail["versions"] == ["2025.0", "2024.0"]
    assert controller.packageDetail["variants"] == ["platform-windows arch-x86_64"]
    assert controller.selectedDetailVersion == 0

    assert controller.selectDetailVersion(1)
    assert controller.packageDetail["description"] == "maya 2024.0"
    assert controller.selectedDetailVersion == 1

    assert controller.addPackageRequest("maya", "2025.0")
    assert controller.packageCount == 2

    model = controller.packageRequestsModel
    assert isinstance(model, PackageRequestListModel)
    assert model.data(model.index(0, 0), PackageRequestListModel.RequestRole) == "maya-2025.0"

    assert controller.save()
    assert RezContext.load("Pipeline", "Base").packages == ["maya-2025.0", "python-3.11"]
    assert app_error_hub.message == ""


def test_package_manager_controller_clears_stale_context_after_failed_load(tmp_path, monkeypatch):
    import rez_manager.ui.package_manager as package_manager
    from rez_manager.adapter.packages import RepositoryInfo
    from rez_manager.models.rez_context import ContextMeta, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.package_manager import PackageManagerController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(
        AppSettings(
            package_repositories=["D:\\packages\\maya"],
            contexts_location=str(tmp_path / "contexts"),
        )
    )
    Project.create("Pipeline")
    RezContext.create("Pipeline", ContextMeta(name="Base", packages=["maya-2024.0"]))

    monkeypatch.setattr(
        package_manager,
        "list_repositories",
        lambda repo_paths: [
            RepositoryInfo(path=repo_paths[0], label=f"maya [{repo_paths[0]}]", packages=["maya"])
        ],
    )

    controller = PackageManagerController()

    assert controller.loadContext("Pipeline", "Base")
    assert controller.packageCount == 1

    assert not controller.loadContext("Pipeline", "Missing")
    assert controller.packageCount == 0
    assert controller.repositoryTree == []
    assert controller.packageDetail == {
        "name": "",
        "versions": [],
        "description": "",
        "requires": [],
        "variants": [],
        "tools": [],
        "code": "",
    }
    assert not controller.save()


def test_project_list_model_reports_errors_to_app_error_hub(tmp_path, monkeypatch):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.main_window import ProjectListModel

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))

    app_error_hub.clear()
    model = ProjectListModel()

    assert model.createProject("Pipeline")
    assert not model.createProject("Pipeline")
    assert "already exists" in app_error_hub.message


def test_uncaught_hook_reports_unexpected_exceptions_to_app_error_hub():
    from rez_manager.exception_hook import qt_exception_hook
    from rez_manager.ui.error_hub import app_error_hub

    app_error_hub.clear()

    try:
        raise RuntimeError("boom")
    except RuntimeError as exc:
        qt_exception_hook.exception_hook(type(exc), exc, exc.__traceback__)

    assert app_error_hub.message == "Unexpected application error: RuntimeError: boom"
