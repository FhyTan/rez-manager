"""Tests for the asynchronous context launcher controller."""

from __future__ import annotations


def test_command_resolver_wraps_windows_cmd_launches(monkeypatch):
    from rez_manager.models.project import Project
    from rez_manager.models.rez_context import ContextMeta, LaunchTarget, RezContext
    from rez_manager.ui.context_launcher import ContextLaunchCommandResolver

    monkeypatch.setattr("rez_manager.ui.context_launcher.IS_WINDOWS", True)

    context = RezContext(
        project=Project(name="Pipeline"),
        meta=ContextMeta(name="Base", launch_target=LaunchTarget.MAYA),
    )

    assert ContextLaunchCommandResolver().command_for(context) == 'start "" maya'


def test_command_resolver_uses_none_for_shell_launch(monkeypatch):
    from rez_manager.models.project import Project
    from rez_manager.models.rez_context import ContextMeta, LaunchTarget, RezContext
    from rez_manager.ui.context_launcher import ContextLaunchCommandResolver

    monkeypatch.setattr("rez_manager.ui.context_launcher.IS_WINDOWS", True)

    context = RezContext(
        project=Project(name="Pipeline"),
        meta=ContextMeta(name="Base", launch_target=LaunchTarget.SHELL),
    )

    assert ContextLaunchCommandResolver().command_for(context) is None


def test_context_launcher_controller_starts_launch_job_with_resolved_command(tmp_path, monkeypatch):
    from rez_manager.models.project import Project
    from rez_manager.models.rez_context import ContextMeta, LaunchTarget, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.context_launcher import ContextLauncherController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    monkeypatch.setattr("rez_manager.ui.context_launcher.IS_WINDOWS", True)
    save_settings(
        AppSettings(
            package_repositories=["D:\\packages\\maya", "D:\\packages\\base"],
            contexts_location=str(tmp_path / "contexts"),
        )
    )
    Project.create("Pipeline")
    RezContext.create(
        "Pipeline",
        ContextMeta(
            name="Base",
            launch_target=LaunchTarget.HOUDINI,
            packages=["houdini-20.5", "python-3.11"],
        ),
    )

    captured: dict[str, object] = {}

    def capture_start_launch_job(self, request_id, package_requests, package_paths, command):
        captured["request_id"] = request_id
        captured["package_requests"] = package_requests
        captured["package_paths"] = package_paths
        captured["command"] = command

    monkeypatch.setattr(
        ContextLauncherController,
        "_start_launch_job",
        capture_start_launch_job,
    )

    controller = ContextLauncherController()

    assert controller.launchContext("Pipeline", "Base")
    assert controller.projectName == "Pipeline"
    assert controller.contextName == "Base"
    assert controller.isLaunching
    assert captured["package_requests"] == ["houdini-20.5", "python-3.11"]
    assert captured["package_paths"] == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert captured["command"] == 'start "" houdini'


def test_context_launcher_controller_launches_unsaved_package_requests_in_shell(
    tmp_path, monkeypatch
):
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.context_launcher import ContextLauncherController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(
        AppSettings(
            package_repositories=["D:\\packages\\maya", "D:\\packages\\base"],
            contexts_location=str(tmp_path / "contexts"),
        )
    )

    captured: dict[str, object] = {}

    def capture_start_launch_job(self, request_id, package_requests, package_paths, command):
        captured["request_id"] = request_id
        captured["package_requests"] = package_requests
        captured["package_paths"] = package_paths
        captured["command"] = command

    monkeypatch.setattr(
        ContextLauncherController,
        "_start_launch_job",
        capture_start_launch_job,
    )
    monkeypatch.setattr(
        "rez_manager.ui.context_launcher.RezContext.load",
        lambda project, context: (_ for _ in ()).throw(AssertionError("load should not be used")),
    )

    controller = ContextLauncherController()

    assert controller.launchPackageRequests("Pipeline", "Draft", ["maya-2026.0", "python-3.11"])
    assert controller.projectName == "Pipeline"
    assert controller.contextName == "Draft"
    assert controller.isLaunching
    assert captured["package_requests"] == ["maya-2026.0", "python-3.11"]
    assert captured["package_paths"] == ["D:\\packages\\maya", "D:\\packages\\base"]
    assert captured["command"] is None


def test_context_launcher_controller_emits_success_after_completed_launch(tmp_path, monkeypatch):
    from rez_manager.models.project import Project
    from rez_manager.models.rez_context import ContextMeta, LaunchTarget, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.context_launcher import ContextLauncherController, LaunchResult
    from rez_manager.ui.error_hub import app_error_hub

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    monkeypatch.setattr("rez_manager.ui.context_launcher.IS_WINDOWS", False)
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))
    Project.create("Pipeline")
    RezContext.create(
        "Pipeline",
        ContextMeta(name="Base", launch_target=LaunchTarget.MAYA, packages=["maya-2025.0"]),
    )
    monkeypatch.setattr(
        ContextLauncherController,
        "_start_launch_job",
        lambda self,
        request_id,
        package_requests,
        package_paths,
        command: self._apply_launch_result(
            request_id,
            LaunchResult(success=True),
        ),
    )

    app_error_hub.clear()
    launched: list[tuple[str, str]] = []
    controller = ContextLauncherController()
    controller.launchSucceeded.connect(lambda project, context: launched.append((project, context)))

    assert controller.launchContext("Pipeline", "Base")
    assert not controller.isLaunching
    assert launched == [("Pipeline", "Base")]
    assert app_error_hub.message == ""


def test_context_launcher_controller_rejects_blank_custom_command(tmp_path, monkeypatch):
    from rez_manager.models.project import Project
    from rez_manager.models.rez_context import ContextMeta, LaunchTarget, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.context_launcher import ContextLauncherController
    from rez_manager.ui.error_hub import app_error_hub

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))
    Project.create("Pipeline")
    RezContext.create(
        "Pipeline",
        ContextMeta(
            name="Broken",
            launch_target=LaunchTarget.CUSTOM,
            custom_command="   ",
            packages=["python-3.11"],
        ),
    )

    app_error_hub.clear()
    controller = ContextLauncherController()

    assert not controller.launchContext("Pipeline", "Broken")
    assert not controller.isLaunching
    assert app_error_hub.message == "Custom launch target requires a custom command."


def test_context_launcher_controller_reports_invalid_context_metadata(tmp_path, monkeypatch):
    from rez_manager.ui.context_launcher import ContextLauncherController
    from rez_manager.ui.error_hub import app_error_hub

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    monkeypatch.setattr(
        "rez_manager.ui.context_launcher.RezContext.load",
        lambda project, context: (_ for _ in ()).throw(KeyError("name")),
    )

    app_error_hub.clear()
    controller = ContextLauncherController()

    assert not controller.launchContext("Pipeline", "Broken")
    assert controller.projectName == ""
    assert controller.contextName == ""
    assert app_error_hub.message == "'name'"


def test_context_launcher_controller_ignores_stale_worker_results_after_failed_reload(
    tmp_path, monkeypatch
):
    from rez_manager.models.project import Project
    from rez_manager.models.rez_context import ContextMeta, LaunchTarget, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.context_launcher import ContextLauncherController, LaunchResult
    from rez_manager.ui.error_hub import app_error_hub

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    monkeypatch.setattr("rez_manager.ui.context_launcher.IS_WINDOWS", True)
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))
    Project.create("Pipeline")
    RezContext.create(
        "Pipeline",
        ContextMeta(name="Base", launch_target=LaunchTarget.SHELL, packages=["maya-2025.0"]),
    )
    monkeypatch.setattr(
        ContextLauncherController,
        "_start_launch_job",
        lambda self, request_id, package_requests, package_paths, command: None,
    )

    app_error_hub.clear()
    controller = ContextLauncherController()

    assert controller.launchContext("Pipeline", "Base")
    assert controller.isLaunching
    assert not controller.launchContext("Pipeline", "Missing")
    controller._apply_launch_result(1, LaunchResult(success=True))

    assert controller.projectName == ""
    assert controller.contextName == ""
    assert not controller.isLaunching
    assert "not exist" in app_error_hub.message
