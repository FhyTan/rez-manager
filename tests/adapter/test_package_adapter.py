"""Tests for Rez package repository adapter helpers."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest


def _install_fake_rez_packages(
    monkeypatch: pytest.MonkeyPatch,
    *,
    package_repository_manager: object,
    iter_packages=None,
    get_package=None,
    version_class=None,
    exception_members: dict[str, type[Exception]],
) -> None:
    rez_module = types.ModuleType("rez")
    exceptions_module = types.ModuleType("rez.exceptions")
    packages_module = types.ModuleType("rez.packages")
    version_module = types.ModuleType("rez.version")
    packages_module.package_repository_manager = package_repository_manager
    packages_module.iter_packages = iter_packages
    packages_module.get_package = get_package
    packages_module.Package = object
    version_module.Version = version_class or (lambda value: value)
    for name, exception_type in exception_members.items():
        setattr(exceptions_module, name, exception_type)
    monkeypatch.setitem(sys.modules, "rez", rez_module)
    monkeypatch.setitem(sys.modules, "rez.exceptions", exceptions_module)
    monkeypatch.setitem(sys.modules, "rez.packages", packages_module)
    monkeypatch.setitem(sys.modules, "rez.version", version_module)


def test_list_repositories_lists_real_package_families(
    temp_packages_dir: Path,
    rez_package_matrix: dict[str, object],
):
    from rez_manager.adapter.packages import list_repositories

    repositories = list_repositories([str(temp_packages_dir)])

    assert len(repositories) == 1
    assert repositories[0].path == str(temp_packages_dir)
    assert repositories[0].label == f"{temp_packages_dir.name} [{temp_packages_dir}]"
    assert repositories[0].packages == [
        "app",
        "bad_commands",
        "bad_requires",
        "broken_dep",
        "python",
        "syntax_pkg",
    ]


def test_get_package_versions_returns_newest_first(
    temp_packages_dir: Path,
    rez_package_matrix: dict[str, object],
):
    from rez_manager.adapter.packages import get_package_versions

    assert get_package_versions("python", [str(temp_packages_dir)]) == ["3.11", "3.10"]


def test_get_package_info_reads_real_package_metadata(
    temp_packages_dir: Path,
    rez_package_matrix: dict[str, object],
):
    from rez_manager.adapter.packages import get_package_info

    package_info = get_package_info("app", "1.0.0", [str(temp_packages_dir)])

    assert package_info is not None
    assert package_info.name == "app"
    assert package_info.versions == ["1.0.0"]
    assert package_info.description == "Test application package"
    assert package_info.requires == ["python-3.11"]
    assert package_info.variants == [[]]
    assert package_info.tools == ["app"]


def test_get_package_info_returns_none_for_missing_version(
    temp_packages_dir: Path,
    rez_package_matrix: dict[str, object],
):
    from rez_manager.adapter.packages import get_package_info

    assert get_package_info("app", "9.9.9", [str(temp_packages_dir)]) is None


def test_get_package_info_wraps_invalid_package_metadata(
    temp_packages_dir: Path,
    rez_package_matrix: dict[str, object],
):
    from rez.exceptions import PackageMetadataError

    from rez_manager.adapter.packages import get_package_info
    from rez_manager.exceptions import RezPackageQueryError

    with pytest.raises(RezPackageQueryError) as exc_info:
        get_package_info("bad_requires", "1.0.0", [str(temp_packages_dir)])

    assert isinstance(exc_info.value.__cause__, PackageMetadataError)


def test_list_repositories_wraps_repository_errors(monkeypatch: pytest.MonkeyPatch):
    from rez_manager.adapter.packages import list_repositories
    from rez_manager.exceptions import RezRepositoryError

    class FakeConfigurationError(Exception):
        pass

    class FakeRepository:
        def iter_package_families(self):
            raise FakeConfigurationError("broken repository")

    fake_manager = SimpleNamespace(
        get_repository=lambda path: FakeRepository(),
        clear_caches=lambda: None,
    )
    _install_fake_rez_packages(
        monkeypatch,
        package_repository_manager=fake_manager,
        exception_members={
            "ConfigurationError": FakeConfigurationError,
            "PackageMetadataError": type("PackageMetadataError", (Exception,), {}),
            "ResourceError": type("ResourceError", (Exception,), {}),
            "RezSystemError": type("RezSystemError", (Exception,), {}),
        },
    )

    with pytest.raises(RezRepositoryError) as exc_info:
        list_repositories([r"D:\packages\broken"])

    assert isinstance(exc_info.value.__cause__, FakeConfigurationError)


def test_get_package_versions_wraps_query_errors(monkeypatch: pytest.MonkeyPatch):
    from rez_manager.adapter.packages import get_package_versions
    from rez_manager.exceptions import RezPackageQueryError

    class FakePackageMetadataError(Exception):
        pass

    def fake_iter_packages(name, paths):
        raise FakePackageMetadataError("invalid package metadata")

    _install_fake_rez_packages(
        monkeypatch,
        package_repository_manager=SimpleNamespace(clear_caches=lambda: None),
        iter_packages=fake_iter_packages,
        get_package=lambda name, version, paths: None,
        exception_members={
            "ConfigurationError": type("ConfigurationError", (Exception,), {}),
            "PackageMetadataError": FakePackageMetadataError,
            "ResourceError": type("ResourceError", (Exception,), {}),
            "RezSystemError": type("RezSystemError", (Exception,), {}),
        },
    )

    with pytest.raises(RezPackageQueryError) as exc_info:
        get_package_versions("python", [r"D:\packages\broken"])

    assert isinstance(exc_info.value.__cause__, FakePackageMetadataError)
