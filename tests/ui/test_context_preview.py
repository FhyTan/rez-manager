"""Tests for the context preview controller."""

from __future__ import annotations


def test_context_preview_controller_loads_resolved_preview(tmp_path, monkeypatch):
    from rez_manager.adapter.context import EnvironmentSection, ResolveResult
    from rez_manager.models.project import Project
    from rez_manager.models.rez_context import ContextMeta, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.context_preview import ContextPreviewController, EnvironmentsTableModel
    from rez_manager.ui.error_hub import app_error_hub

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))
    Project.create("Pipeline")
    RezContext.create("Pipeline", ContextMeta(name="Base", packages=["maya-2025.0", "python-3.11"]))

    preview_result = ResolveResult(
        success=True,
        packages=["maya-2025.0", "python-3.11"],
        environ={"MAYA_LOCATION": "D:\\packages\\maya\\2025.0"},
        environ_sections=[
            EnvironmentSection(
                title="User Environment",
                variables={"MAYA_LOCATION": "D:\\packages\\maya\\2025.0"},
            ),
            EnvironmentSection(
                title="System Environment",
                variables={"PATH": "C:\\Windows\\System32"},
            ),
            EnvironmentSection(title="REZ_ Environment", variables={}),
        ],
        tools=["maya.exe"],
    )
    monkeypatch.setattr(
        ContextPreviewController,
        "_start_preview_job",
        lambda self, request_id, package_requests, package_paths: self._apply_preview_result(
            request_id, preview_result
        ),
    )

    app_error_hub.clear()
    controller = ContextPreviewController()

    assert controller.loadContext("Pipeline", "Base")
    assert controller.projectName == "Pipeline"
    assert controller.contextName == "Base"
    assert controller.resolvedPackages == [
        {"name": "maya", "version": "2025.0", "label": "maya-2025.0"},
        {"name": "python", "version": "3.11", "label": "python-3.11"},
    ]
    sections = controller.environmentSections
    assert [section["title"] for section in sections] == [
        "User Environment",
        "System Environment",
        "REZ_ Environment",
    ]
    assert sections[0]["rows"] == [{"name": "MAYA_LOCATION", "value": "D:\\packages\\maya\\2025.0"}]
    assert sections[0]["rowCount"] == 1
    assert isinstance(sections[0]["tableModel"], EnvironmentsTableModel)
    assert sections[0]["tableModel"].rowData(0) == {
        "name": "MAYA_LOCATION",
        "value": "D:\\packages\\maya\\2025.0",
    }
    assert sections[1]["rows"] == [{"name": "PATH", "value": "C:\\Windows\\System32"}]
    assert sections[1]["rowCount"] == 1
    assert sections[2]["rows"] == []
    assert sections[2]["rowCount"] == 0
    assert controller.tools == ["maya.exe"]
    assert app_error_hub.message == ""


def test_context_preview_controller_clears_stale_state_after_failed_load(tmp_path, monkeypatch):
    from rez_manager.adapter.context import ResolveResult
    from rez_manager.models.project import Project
    from rez_manager.models.rez_context import ContextMeta, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.context_preview import ContextPreviewController
    from rez_manager.ui.error_hub import app_error_hub

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))
    Project.create("Pipeline")
    RezContext.create("Pipeline", ContextMeta(name="Base", packages=["maya-2025.0"]))

    preview_result = ResolveResult(
        success=False,
        packages=[],
        environ={},
        environ_sections=[],
        tools=[],
        error="Resolve failed.",
    )
    monkeypatch.setattr(
        ContextPreviewController,
        "_start_preview_job",
        lambda self, request_id, package_requests, package_paths: self._apply_preview_result(
            request_id, preview_result
        ),
    )

    controller = ContextPreviewController()

    assert controller.loadContext("Pipeline", "Base")
    assert controller.projectName == "Pipeline"
    assert controller.contextName == "Base"
    assert not controller.isLoading
    assert controller.resolvedPackages == []
    assert controller.environmentSections == []
    assert app_error_hub.message == "Resolve failed."


def test_context_preview_controller_reports_invalid_context_metadata(tmp_path, monkeypatch):
    from rez_manager.ui.context_preview import ContextPreviewController
    from rez_manager.ui.error_hub import app_error_hub

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    monkeypatch.setattr(
        "rez_manager.ui.context_preview.RezContext.load",
        lambda project, context: (_ for _ in ()).throw(KeyError("name")),
    )

    app_error_hub.clear()
    controller = ContextPreviewController()

    assert not controller.loadContext("Pipeline", "Broken")
    assert controller.projectName == ""
    assert controller.contextName == ""
    assert app_error_hub.message == "'name'"


def test_context_preview_controller_ignores_stale_worker_results_after_failed_reload(
    tmp_path, monkeypatch
):
    from rez_manager.adapter.context import ResolveResult
    from rez_manager.models.project import Project
    from rez_manager.models.rez_context import ContextMeta, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.context_preview import ContextPreviewController
    from rez_manager.ui.error_hub import app_error_hub

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))
    Project.create("Pipeline")
    RezContext.create("Pipeline", ContextMeta(name="Base", packages=["maya-2025.0"]))

    monkeypatch.setattr(
        ContextPreviewController,
        "_start_preview_job",
        lambda self, request_id, package_requests, package_paths: None,
    )

    app_error_hub.clear()
    controller = ContextPreviewController()

    assert controller.loadContext("Pipeline", "Base")
    stale_result = ResolveResult(
        success=True,
        packages=["maya-2025.0"],
        environ={},
        environ_sections=[],
        tools=[],
    )

    assert not controller.loadContext("Pipeline", "Missing")
    controller._apply_preview_result(1, stale_result)

    assert controller.projectName == ""
    assert controller.contextName == ""
    assert controller.resolvedPackages == []
    assert "not exist" in app_error_hub.message


def test_context_preview_controller_passes_settings_package_paths(tmp_path, monkeypatch):
    from rez_manager.models.project import Project
    from rez_manager.models.rez_context import ContextMeta, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.context_preview import ContextPreviewController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(
        AppSettings(
            package_repositories=["D:\\packages\\maya", "D:\\packages\\base"],
            contexts_location=str(tmp_path / "contexts"),
        )
    )
    Project.create("Pipeline")
    RezContext.create("Pipeline", ContextMeta(name="Base", packages=["maya-2025.0"]))

    captured: dict[str, object] = {}

    def capture_start_preview_job(self, request_id, package_requests, package_paths):
        captured["request_id"] = request_id
        captured["package_requests"] = package_requests
        captured["package_paths"] = package_paths

    monkeypatch.setattr(
        ContextPreviewController,
        "_start_preview_job",
        capture_start_preview_job,
    )

    controller = ContextPreviewController()

    assert controller.loadContext("Pipeline", "Base")
    assert captured["package_requests"] == ["maya-2025.0"]
    assert captured["package_paths"] == ["D:\\packages\\maya", "D:\\packages\\base"]
