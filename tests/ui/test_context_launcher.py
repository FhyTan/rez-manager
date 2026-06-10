"""Tests for the asynchronous context launcher controller."""

from __future__ import annotations


def test_command_resolver_wraps_windows_cmd_launches(monkeypatch):
    from rez_manager.models.launch_target import LAUNCH_TARGETS

    monkeypatch.setattr("rez_manager.models.launch_target.IS_WINDOWS", True)

    assert LAUNCH_TARGETS.launch_command_for("Maya") == 'start "" maya'


def test_command_resolver_supports_new_dcc_targets(monkeypatch):
    from rez_manager.models.launch_target import LAUNCH_TARGETS

    monkeypatch.setattr("rez_manager.models.launch_target.IS_WINDOWS", False)

    assert LAUNCH_TARGETS.launch_command_for("Blender") == "blender"
    assert LAUNCH_TARGETS.launch_command_for("Nuke") == "nuke"
    assert LAUNCH_TARGETS.launch_command_for("NukeX") == "nukex"


def test_command_resolver_uses_none_for_shell_launch(monkeypatch):
    from rez_manager.models.launch_target import LAUNCH_TARGETS

    monkeypatch.setattr("rez_manager.models.launch_target.IS_WINDOWS", True)

    assert LAUNCH_TARGETS.launch_command_for("Shell") is None


def test_context_launcher_controller_starts_resolve_job_with_command(tmp_path, monkeypatch):
    from rez_manager.models.project import Project
    from rez_manager.models.rez_context import ContextMeta, LaunchTarget, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.context_launcher import ContextLauncherController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    monkeypatch.setattr("rez_manager.models.launch_target.IS_WINDOWS", True)
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

    def capture_start_resolve_job(self, request_id, package_requests, command, rxt_path=None):
        captured["request_id"] = request_id
        captured["package_requests"] = package_requests
        captured["command"] = command
        captured["rxt_path"] = rxt_path

    monkeypatch.setattr(
        ContextLauncherController,
        "_start_resolve_job",
        capture_start_resolve_job,
    )

    controller = ContextLauncherController()

    assert controller.launchContext("Pipeline", "Base")
    assert controller.projectName == "Pipeline"
    assert controller.contextName == "Base"
    assert captured["package_requests"] == ["houdini-20.5", "python-3.11"]
    assert captured["command"] == 'start "" houdini'
    assert captured["rxt_path"].endswith("context.rxt")


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

    def capture_start_resolve_job(self, request_id, package_requests, command, rxt_path=None):
        captured["request_id"] = request_id
        captured["package_requests"] = package_requests
        captured["command"] = command
        captured["rxt_path"] = rxt_path

    monkeypatch.setattr(
        ContextLauncherController,
        "_start_resolve_job",
        capture_start_resolve_job,
    )
    monkeypatch.setattr(
        "rez_manager.ui.context_launcher.RezContext.load",
        lambda project, context: (_ for _ in ()).throw(AssertionError("load should not be used")),
    )

    controller = ContextLauncherController()

    assert controller.launchPackageRequests("Pipeline", "Draft", ["maya-2026.0", "python-3.11"])
    assert controller.projectName == "Pipeline"
    assert controller.contextName == "Draft"
    assert captured["package_requests"] == ["maya-2026.0", "python-3.11"]
    assert captured["command"] is None
    assert captured["rxt_path"] is None


def test_context_launcher_controller_emits_success_after_completed_launch(tmp_path, monkeypatch):
    from rez_manager.adapter.context import ContextInfo
    from rez_manager.models.project import Project
    from rez_manager.models.rez_context import ContextMeta, LaunchTarget, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.context_launcher import ContextLauncherController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    monkeypatch.setattr("rez_manager.models.launch_target.IS_WINDOWS", False)
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))
    Project.create("Pipeline")
    RezContext.create(
        "Pipeline",
        ContextMeta(name="Base", launch_target=LaunchTarget.MAYA, packages=["maya-2025.0"]),
    )

    result = ContextInfo(
        packages=["maya-2025.0"],
        environ={},
        tools=[],
        _resolved_context=None,
    )
    monkeypatch.setattr(
        ContextLauncherController,
        "_start_resolve_job",
        lambda self, request_id, package_requests, command, rxt_path=None: (
            self._apply_launch_result(request_id, result)
        ),
    )

    launched: list[tuple[str, str]] = []
    controller = ContextLauncherController()
    controller.launchSucceeded.connect(lambda project, context: launched.append((project, context)))

    assert controller.launchContext("Pipeline", "Base")
    assert launched == [("Pipeline", "Base")]


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


def test_context_launcher_controller_uses_attached_error_target_for_launch_errors(
    tmp_path, monkeypatch
):
    from rez_manager.ui.context_launcher import ContextLauncherController
    from rez_manager.ui.error_hub import app_error_hub

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    monkeypatch.setattr(
        "rez_manager.ui.context_launcher.RezContext.load",
        lambda project, context: (_ for _ in ()).throw(KeyError("name")),
    )
    monkeypatch.setattr(
        "rez_manager.ui.context_launcher.report_object_ui_error",
        lambda owner, message: app_error_hub.publish_for_target(message, "package-manager"),
    )

    app_error_hub.clear()
    controller = ContextLauncherController()

    assert not controller.launchContext("Pipeline", "Broken")
    assert app_error_hub.message == "'name'"
    assert app_error_hub.messageTarget == "package-manager"


def test_context_launcher_controller_ignores_stale_worker_results_after_failed_reload(
    tmp_path, monkeypatch
):
    from rez_manager.adapter.context import ContextInfo
    from rez_manager.models.project import Project
    from rez_manager.models.rez_context import ContextMeta, LaunchTarget, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.context_launcher import ContextLauncherController
    from rez_manager.ui.error_hub import app_error_hub

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    monkeypatch.setattr("rez_manager.models.launch_target.IS_WINDOWS", True)
    save_settings(AppSettings(contexts_location=str(tmp_path / "contexts")))
    Project.create("Pipeline")
    RezContext.create(
        "Pipeline",
        ContextMeta(name="Base", launch_target=LaunchTarget.SHELL, packages=["maya-2025.0"]),
    )
    monkeypatch.setattr(
        ContextLauncherController,
        "_start_resolve_job",
        lambda self, request_id, package_requests, command, rxt_path=None: None,
    )

    app_error_hub.clear()
    controller = ContextLauncherController()

    assert controller.launchContext("Pipeline", "Base")
    assert not controller.launchContext("Pipeline", "Missing")
    stale_result = ContextInfo(
        packages=["maya-2025.0"], environ={}, tools=[], _resolved_context=None
    )
    controller._apply_launch_result(1, stale_result)

    assert controller.projectName == ""
    assert controller.contextName == ""
    assert "not exist" in app_error_hub.message


def test_context_resolve_worker_reports_adapter_errors(monkeypatch):
    from rez_manager.exceptions import RezResolveError
    from rez_manager.ui.context_resolve import ContextResolveWorker

    monkeypatch.setattr(
        "rez_manager.ui.context_resolve.resolve_context",
        lambda package_requests: (_ for _ in ()).throw(
            RezResolveError("Resolution failed.")
        ),
    )

    emitted: list[tuple[int, object]] = []
    worker = ContextResolveWorker(7, ["python-3.11"], mode="resolve")
    worker.signals.finished.connect(lambda request_id, result: emitted.append((request_id, result)))

    worker.run()

    assert len(emitted) == 1
    assert emitted[0][0] == 7
    assert isinstance(emitted[0][1], RezResolveError)
    assert "Resolution failed" in str(emitted[0][1])
