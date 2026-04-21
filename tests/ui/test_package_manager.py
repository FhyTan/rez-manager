"""Tests for the package manager controller and models."""

from __future__ import annotations

import time

from PySide6.QtCore import QCoreApplication

from rez_manager.models.project import Project


def _wait_for(predicate, timeout: float = 1.0) -> None:
    app = QCoreApplication.instance() or QCoreApplication([])
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        app.processEvents()
        if predicate():
            return
        time.sleep(0.01)
    app.processEvents()
    assert predicate()


def test_package_manager_controller_loads_context_and_repository_tree(tmp_path, monkeypatch):
    import rez_manager.ui.package_manager as package_manager
    from rez_manager.adapter.packages import RepositoryInfo
    from rez_manager.models.rez_context import ContextMeta, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.package_manager import (
        PackageManagerController,
        PackageRequestListModel,
        RepositoryTreeModel,
    )

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
        ContextMeta(name="Render", packages=["redshift_houdini-3.5", "python-3.11"]),
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
    _wait_for(lambda: not controller.isLoadingRepositories)
    assert controller.packageCount == 2
    repository_model = controller.repositoryModel
    assert isinstance(repository_model, RepositoryTreeModel)
    assert repository_model.rowCount() == 2

    top_index = repository_model.index(0, 0)
    assert (
        repository_model.data(top_index, RepositoryTreeModel.LabelRole)
        == "maya [D:\\packages\\maya]"
    )
    assert repository_model.data(top_index, RepositoryTreeModel.NodeTypeRole) == "repository"
    assert repository_model.rowCount(top_index) == 2

    child_index = repository_model.index(0, 0, top_index)
    assert repository_model.data(child_index, RepositoryTreeModel.LabelRole) == "maya"
    assert repository_model.data(child_index, RepositoryTreeModel.NodeTypeRole) == "package"
    assert repository_model.data(child_index, RepositoryTreeModel.RepoIndexRole) == 0
    assert repository_model.data(child_index, RepositoryTreeModel.PackageIndexRole) == 0

    model = controller.packageRequestsModel
    assert isinstance(model, PackageRequestListModel)
    assert model.rowCount() == 2
    assert model.data(model.index(0, 0), PackageRequestListModel.NameRole) == "redshift_houdini"
    assert model.data(model.index(0, 0), PackageRequestListModel.VersionRole) == "3.5"
    assert model.data(model.index(1, 0), PackageRequestListModel.DisplayVersionRole) == "3.11"


def test_package_manager_controller_selects_package_and_saves_requests(tmp_path, monkeypatch):
    import rez_manager.ui.package_manager as package_manager
    from rez_manager.adapter.packages import PackageInfo, RepositoryInfo
    from rez_manager.models.rez_context import ContextMeta, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.error_hub import app_error_hub
    from rez_manager.ui.package_manager import PackageDetailObject, PackageManagerController

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
    _wait_for(lambda: not controller.isLoadingRepositories)
    assert controller.selectRepositoryPackage(0, 0)
    detail = controller.packageDetail
    assert isinstance(detail, PackageDetailObject)
    assert detail.name == "maya"
    assert detail.versions == ["auto", "2025.0", "2024.0"]
    assert detail.variants == ["platform-windows arch-x86_64"]
    assert detail.selectedVersion == "auto"
    assert detail.selectedVersionIndex == 0

    assert controller.selectDetailVersion(2)
    assert detail.description == "maya 2024.0"
    assert detail.selectedVersion == "2024.0"
    assert detail.selectedVersionIndex == 2

    assert controller.addPackageRequest("maya", "auto")
    assert controller.packageCount == 2
    assert controller.selectedRequestRow == 0

    assert controller.save()
    assert RezContext.load("Pipeline", "Base").packages == ["maya", "python-3.11"]
    assert app_error_hub.message == ""


def test_package_manager_controller_keeps_unsaved_requests_in_memory_until_save(
    tmp_path, monkeypatch
):
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
        lambda name, repo_paths: ["2026.0", "2024.0"] if name == "maya" else [],
    )
    monkeypatch.setattr(
        package_manager,
        "get_package_info",
        lambda name, version, repo_paths: None,
    )

    controller = PackageManagerController()

    assert controller.loadContext("Pipeline", "Base")
    _wait_for(lambda: not controller.isLoadingRepositories)
    assert controller.addPackageRequest("maya", "2026.0")
    assert controller.packageRequests == ["maya-2026.0", "python-3.11"]
    assert RezContext.load("Pipeline", "Base").packages == ["maya-2024.0", "python-3.11"]


def test_package_manager_controller_selects_required_package_with_auto_version(
    tmp_path, monkeypatch
):
    import rez_manager.ui.package_manager as package_manager
    from rez_manager.adapter.packages import PackageInfo, RepositoryInfo
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
    RezContext.create("Pipeline", ContextMeta(name="Base", packages=["maya", "python-3.11"]))

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
        lambda name, repo_paths: ["2025.0", "2024.0"],
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

    controller = PackageManagerController()

    assert controller.loadContext("Pipeline", "Base")
    _wait_for(lambda: not controller.isLoadingRepositories)
    assert controller.selectRequiredPackage(0)
    assert controller.selectedRequestRow == 0
    assert controller.selectedRepositoryIndex == -1
    assert controller.packageDetail.selectedVersion == "auto"
    assert controller.packageDetail.versions == ["auto", "2025.0", "2024.0"]
    assert controller.packageDetail.description == "maya 2025.0"


def test_package_manager_controller_clears_stale_context_after_failed_load(tmp_path, monkeypatch):
    import rez_manager.ui.package_manager as package_manager
    from rez_manager.adapter.packages import RepositoryInfo
    from rez_manager.models.rez_context import ContextMeta, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.package_manager import PackageManagerController, RepositoryTreeModel

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
    _wait_for(lambda: not controller.isLoadingRepositories)
    assert controller.packageCount == 1

    assert not controller.loadContext("Pipeline", "Missing")
    assert controller.packageCount == 0
    assert isinstance(controller.repositoryModel, RepositoryTreeModel)
    assert controller.repositoryModel.rowCount() == 0
    assert controller.packageDetail.name == ""
    assert controller.packageDetail.versions == []
    assert controller.packageDetail.description == ""
    assert controller.selectedRequestRow == -1
    assert controller.selectedRepositoryIndex == -1
    assert controller.selectedRepositoryPackageIndex == -1
    assert not controller.save()


def test_package_manager_controller_refresh_clears_cache_and_reloads_detail(
    tmp_path, monkeypatch
):
    import rez_manager.ui.package_manager as package_manager
    from rez_manager.adapter.packages import PackageInfo, RepositoryInfo
    from rez_manager.models.rez_context import ContextMeta, RezContext
    from rez_manager.models.settings import AppSettings
    from rez_manager.persistence.settings_store import save_settings
    from rez_manager.ui.package_manager import PackageManagerController, RepositoryTreeModel

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    save_settings(
        AppSettings(
            package_repositories=["D:\\packages\\maya"],
            contexts_location=str(tmp_path / "contexts"),
        )
    )
    Project.create("Pipeline")
    RezContext.create("Pipeline", ContextMeta(name="Base", packages=["maya"]))

    state = {"phase": 0, "clear_calls": 0}

    def fake_clear_package_cache() -> None:
        state["clear_calls"] += 1
        state["phase"] = 1

    def fake_list_repositories(repo_paths: list[str]) -> list[RepositoryInfo]:
        packages = ["maya"] if state["phase"] == 0 else ["maya", "mtoa"]
        return [
            RepositoryInfo(
                path=repo_paths[0],
                label=f"maya [{repo_paths[0]}]",
                packages=packages,
            )
        ]

    def fake_get_package_versions(name: str, repo_paths: list[str]) -> list[str]:
        if name != "maya":
            return []
        return ["2024.0"] if state["phase"] == 0 else ["2025.0", "2024.0"]

    def fake_get_package_info(name: str, version: str, repo_paths: list[str]) -> PackageInfo:
        return PackageInfo(
            name=name,
            versions=[version],
            description=f"{name} {version}",
            requires=["python-3.11"],
            variants=[["platform-windows", "arch-x86_64"]],
            tools=["maya"],
            python_statements=f"name = '{name}'\nversion = '{version}'",
        )

    monkeypatch.setattr(package_manager, "clear_package_cache", fake_clear_package_cache)
    monkeypatch.setattr(package_manager, "list_repositories", fake_list_repositories)
    monkeypatch.setattr(package_manager, "get_package_versions", fake_get_package_versions)
    monkeypatch.setattr(package_manager, "get_package_info", fake_get_package_info)

    controller = PackageManagerController()

    assert controller.loadContext("Pipeline", "Base")
    _wait_for(lambda: not controller.isLoadingRepositories)
    assert controller.selectRequiredPackage(0)
    assert controller.packageDetail.description == "maya 2024.0"
    assert controller.packageDetail.versions == ["auto", "2024.0"]

    assert controller.refresh()
    assert controller.isLoadingRepositories
    _wait_for(lambda: not controller.isLoadingRepositories)

    assert state["clear_calls"] == 1
    assert controller.packageDetail.description == "maya 2025.0"
    assert controller.packageDetail.versions == ["auto", "2025.0", "2024.0"]
    repository_model = controller.repositoryModel
    assert isinstance(repository_model, RepositoryTreeModel)
    top_index = repository_model.index(0, 0)
    assert repository_model.rowCount(top_index) == 2
