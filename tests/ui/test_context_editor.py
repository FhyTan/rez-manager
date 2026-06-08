"""Tests for the context editor controller."""

from __future__ import annotations

import json


def _setup_context_on_disk(
    tmp_path,
    monkeypatch,
    project_name: str = "VFX Pipeline",
    context_name: str = "Maya Base",
    contexts_dir_name: str = "rez-contexts",
) -> str:
    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings

    contexts_root = tmp_path / contexts_dir_name
    context_dir = contexts_root / project_name / context_name
    context_dir.mkdir(parents=True)
    (context_dir / "meta.json").write_text(
        json.dumps(
            {
                "name": context_name,
                "description": "",
                "launch_target": "Maya",
                "custom_command": None,
                "packages": ["maya-2024"],
            }
        ),
        encoding="utf-8",
    )

    save_settings(AppSettings(contexts_location=str(contexts_root)))
    return str(contexts_root)


def _make_controller() -> object:
    from rez_manager.ui.context_editor import ContextEditorController

    return ContextEditorController()


def test_new_context_empty_name(tmp_path, monkeypatch):
    controller = _make_controller()

    controller.checkNameAvailability("Pipeline", "", "", "")

    assert controller.nameError == "Name cannot be empty"
    assert not controller.nameAvailable


def test_new_context_whitespace_only_name(tmp_path, monkeypatch):
    controller = _make_controller()

    controller.checkNameAvailability("Pipeline", "   ", "", "")

    assert controller.nameError == "Name cannot be empty"
    assert not controller.nameAvailable


def test_new_context_name_with_path_separator(tmp_path, monkeypatch):
    controller = _make_controller()

    controller.checkNameAvailability("Pipeline", "Maya/2024", "", "")

    assert controller.nameError == "Name contains invalid path characters"
    assert not controller.nameAvailable


def test_new_context_name_with_backslash(tmp_path, monkeypatch):
    controller = _make_controller()

    controller.checkNameAvailability("Pipeline", "Maya\\2024", "", "")

    assert controller.nameError == "Name contains invalid path characters"
    assert not controller.nameAvailable


def test_new_context_name_dot(tmp_path, monkeypatch):
    controller = _make_controller()

    controller.checkNameAvailability("Pipeline", ".", "", "")

    assert controller.nameError == "Name contains invalid path characters"
    assert not controller.nameAvailable


def test_new_context_name_dotdot(tmp_path, monkeypatch):
    controller = _make_controller()

    controller.checkNameAvailability("Pipeline", "..", "", "")

    assert controller.nameError == "Name contains invalid path characters"
    assert not controller.nameAvailable


def test_new_context_name_available(tmp_path, monkeypatch):
    _setup_context_on_disk(tmp_path, monkeypatch, project_name="Pipeline", context_name="Maya Base")
    controller = _make_controller()

    controller.checkNameAvailability("Pipeline", "Nuke Base", "", "")

    assert controller.nameError == ""
    assert controller.nameAvailable


def test_new_context_name_already_exists(tmp_path, monkeypatch):
    _setup_context_on_disk(tmp_path, monkeypatch, project_name="Pipeline", context_name="Maya Base")
    controller = _make_controller()

    controller.checkNameAvailability("Pipeline", "Maya Base", "", "")

    assert "Maya Base" in controller.nameError
    assert "Pipeline" in controller.nameError
    assert not controller.nameAvailable


def test_new_context_project_does_not_exist_yet(tmp_path, monkeypatch):
    _setup_context_on_disk(
        tmp_path, monkeypatch, project_name="Pipeline", context_name="Maya Base"
    )
    controller = _make_controller()

    controller.checkNameAvailability("NewProject", "Maya Base", "", "")

    assert controller.nameError == ""
    assert controller.nameAvailable


def test_new_context_name_exists_in_selected_project_not_in_other(tmp_path, monkeypatch):
    _setup_context_on_disk(
        tmp_path, monkeypatch, project_name="Pipeline", context_name="Maya Base"
    )
    _make_context_on_disk(tmp_path, monkeypatch, "OtherProject", "Maya Base")
    controller = _make_controller()

    controller.checkNameAvailability("Pipeline", "Houdini FX", "", "")

    assert controller.nameError == ""
    assert controller.nameAvailable


def _make_context_on_disk(tmp_path, monkeypatch, project_name: str, context_name: str) -> None:
    from rez_manager.persistence.settings_store import load_settings

    settings = load_settings()
    contexts_root = settings.general.contexts_location
    if not contexts_root:
        from rez_manager.persistence.app_paths import default_rez_contexts_dir

        contexts_root = str(default_rez_contexts_dir())

    from pathlib import Path

    context_dir = Path(contexts_root) / project_name / context_name
    context_dir.mkdir(parents=True, exist_ok=True)
    (context_dir / "meta.json").write_text(
        json.dumps(
            {
                "name": context_name,
                "description": "",
                "launch_target": "Shell",
                "custom_command": None,
                "packages": [],
            }
        ),
        encoding="utf-8",
    )


def test_edit_context_same_project_same_name(tmp_path, monkeypatch):
    _setup_context_on_disk(tmp_path, monkeypatch, project_name="Pipeline", context_name="Maya Base")
    controller = _make_controller()

    controller.checkNameAvailability("Pipeline", "Maya Base", "Pipeline", "Maya Base")

    assert controller.nameError == ""
    assert controller.nameAvailable


def test_edit_context_same_project_different_name_available(tmp_path, monkeypatch):
    _setup_context_on_disk(tmp_path, monkeypatch, project_name="Pipeline", context_name="Maya Base")
    controller = _make_controller()

    controller.checkNameAvailability("Pipeline", "Maya 2025", "Pipeline", "Maya Base")

    assert controller.nameError == ""
    assert controller.nameAvailable


def test_edit_context_same_project_different_name_conflict(tmp_path, monkeypatch):
    _setup_context_on_disk(tmp_path, monkeypatch, project_name="Pipeline", context_name="Maya Base")
    _make_context_on_disk(tmp_path, monkeypatch, "Pipeline", "Nuke Base")
    controller = _make_controller()

    controller.checkNameAvailability("Pipeline", "Nuke Base", "Pipeline", "Maya Base")

    assert "Nuke Base" in controller.nameError
    assert not controller.nameAvailable


def test_edit_context_different_project_same_name_available(tmp_path, monkeypatch):
    _setup_context_on_disk(tmp_path, monkeypatch, project_name="Pipeline", context_name="Maya Base")
    controller = _make_controller()

    controller.checkNameAvailability("OtherProject", "Maya Base", "Pipeline", "Maya Base")

    assert controller.nameError == ""
    assert controller.nameAvailable


def test_edit_context_different_project_same_name_conflict(tmp_path, monkeypatch):
    _setup_context_on_disk(tmp_path, monkeypatch, project_name="Pipeline", context_name="Maya Base")
    _make_context_on_disk(tmp_path, monkeypatch, "OtherProject", "Maya Base")
    controller = _make_controller()

    controller.checkNameAvailability("OtherProject", "Maya Base", "Pipeline", "Maya Base")

    assert "Maya Base" in controller.nameError
    assert "OtherProject" in controller.nameError
    assert not controller.nameAvailable


def test_edit_context_different_project_different_name_available(tmp_path, monkeypatch):
    _setup_context_on_disk(tmp_path, monkeypatch, project_name="Pipeline", context_name="Maya Base")
    controller = _make_controller()

    controller.checkNameAvailability("OtherProject", "Nuke Base", "Pipeline", "Maya Base")

    assert controller.nameError == ""
    assert controller.nameAvailable


def test_edit_context_different_project_different_name_conflict(tmp_path, monkeypatch):
    _setup_context_on_disk(tmp_path, monkeypatch, project_name="Pipeline", context_name="Maya Base")
    _make_context_on_disk(tmp_path, monkeypatch, "OtherProject", "Nuke Base")
    controller = _make_controller()

    controller.checkNameAvailability("OtherProject", "Nuke Base", "Pipeline", "Maya Base")

    assert "Nuke Base" in controller.nameError
    assert not controller.nameAvailable


def test_edit_context_only_project_changed_to_existing_project_with_same_context_name(
    tmp_path, monkeypatch
):
    _setup_context_on_disk(tmp_path, monkeypatch, project_name="Pipeline", context_name="Maya Base")
    _make_context_on_disk(tmp_path, monkeypatch, "NewPipeline", "Maya Base")
    controller = _make_controller()

    controller.checkNameAvailability("NewPipeline", "Maya Base", "Pipeline", "Maya Base")

    assert "Maya Base" in controller.nameError
    assert "NewPipeline" in controller.nameError
    assert not controller.nameAvailable


def test_name_error_clears_when_issue_resolved(tmp_path, monkeypatch):
    _setup_context_on_disk(tmp_path, monkeypatch, project_name="Pipeline", context_name="Maya Base")
    controller = _make_controller()

    controller.checkNameAvailability("Pipeline", "Maya Base", "", "")
    assert not controller.nameAvailable

    controller.checkNameAvailability("Pipeline", "Houdini FX", "", "")
    assert controller.nameAvailable


def test_name_error_does_not_emit_signal_when_unchanged(tmp_path, monkeypatch):
    _setup_context_on_disk(tmp_path, monkeypatch, project_name="Pipeline", context_name="Maya Base")
    controller = _make_controller()

    change_count = 0
    controller.nameErrorChanged.connect(lambda: change_count.__setattr__(  # type: ignore[attr-defined]
        "val", change_count.__dict__.get("val", 0) + 1
    ))

    controller.checkNameAvailability("Pipeline", "Maya Base", "", "")
    controller.checkNameAvailability("Pipeline", "Maya Base", "", "")
    controller.checkNameAvailability("Pipeline", "Maya Base", "", "")

    assert not controller.nameAvailable
