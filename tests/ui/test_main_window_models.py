"""Tests for main-window-facing Qt models."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlparse

from rez_manager.models.project import Project


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
            '  "launch_target": "Shell",\n'
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
    assert model.contextCount == 0

    context_dir = contexts_root / "Pipeline" / "Context A"
    context_dir.mkdir(parents=True)
    (context_dir / "meta.json").write_text(
        (
            "{\n"
            '  "name": "Context A",\n'
            '  "description": "Created later",\n'
            '  "launch_target": "Shell",\n'
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
    assert model.contextCount == 1
    assert [item["name"] for item in model.contexts] == ["Context A"]
    assert len(model.filteredContexts("Pipeline")) == 1
    assert [context.name for context in project_model.get_project("Pipeline").contexts or []] == [
        "Context A"
    ]


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

    assert model.saveContext("", "", "Pipeline", "Base", "Base context", "Shell", "", "", "", [])
    assert [context.name for context in project_model.get_project("Pipeline").contexts or []] == [
        "Base"
    ]
    assert model.saveContext(
        "Pipeline",
        "Base",
        "Shots",
        "Shot Base",
        "Moved context",
        "Custom",
        "nuke -x %f",
        "",
        "",
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

    assert model.saveContext("", "", "Pipeline", "Base", "Base context", "Shell", "", "", "", [])
    assert inserted_rows == [(0, 0)]

    assert model.saveContext(
        "Pipeline",
        "Base",
        "Pipeline",
        "Base",
        "Updated context",
        "Custom",
        "nuke -x %f",
        "",
        "",
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
        "",
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
        "",
        "",
        [],
    )
    assert removed_rows[-1] == (0, 0)
    assert model.contexts == []
    assert changed_rows.count((-1, -1)) == reset_count


def test_models_report_stale_project_and_context_actions(tmp_path, monkeypatch):
    from rez_manager.models.rez_context import ContextMeta, RezContext
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


def test_context_list_model_payload_includes_thumbnail_fields(tmp_path, monkeypatch):
    from rez_manager.models.rez_context import ContextMeta, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.main_window import ProjectListModel, RezContextListModel

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))
    Project.create("Pipeline")
    created = RezContext.create(
        "Pipeline",
        ContextMeta(
            name="Base",
            builtin_thumbnail_source="qrc:/icons/dcc/Maya",
            packages=["maya-2025.0"],
        ),
    )
    Path(created.path, "thumbnail.png").write_bytes(b"png")

    project_model = ProjectListModel()
    context_model = RezContextListModel()
    context_model.projectModel = project_model
    context_model.loadProject("Pipeline")

    payload = context_model.get(0)

    assert payload["builtinThumbnailSource"] == "qrc:/icons/dcc/Maya"
    assert payload["thumbnailSource"].startswith("file:///")
    query = parse_qs(urlparse(payload["thumbnailSource"]).query)
    assert "mtime" in query


def test_context_list_model_payload_includes_launch_target_color(tmp_path, monkeypatch):
    from rez_manager.models.rez_context import ContextMeta, LaunchTarget, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.main_window import ProjectListModel, RezContextListModel

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))
    Project.create("Pipeline")
    RezContext.create(
        "Pipeline",
        ContextMeta(name="Base", launch_target=LaunchTarget.MAYA, packages=["maya-2025.0"]),
    )

    project_model = ProjectListModel()
    context_model = RezContextListModel()
    context_model.projectModel = project_model
    context_model.loadProject("Pipeline")

    payload = context_model.get(0)

    assert payload["launchTarget"] == "Maya"
    assert payload["launchTargetColor"] == "#4DB880"


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
