"""Rez package repository and package query adapter."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from rez_manager.exceptions import RezPackageQueryError, RezRepositoryError


@dataclass
class PackageInfo:
    name: str
    versions: list[str]
    description: str
    requires: list[str]
    variants: list[list[str]]
    tools: list[str]
    python_statements: str


@dataclass
class RepositoryInfo:
    path: str
    label: str  # folder_name [dir_path]
    packages: list[str] = field(default_factory=list)


def list_repositories(repo_paths: list[str]) -> list[RepositoryInfo]:
    """Build a RepositoryInfo list from configured repository paths."""
    from rez.packages import package_repository_manager

    repos: list[RepositoryInfo] = []
    for path in repo_paths:
        folder_name = os.path.basename(path.rstrip("/\\"))
        label = f"{folder_name} [{path}]"
        try:
            repo = package_repository_manager.get_repository(path)
            packages = sorted(str(fam.name) for fam in repo.iter_package_families())
        except _repository_exception_types() as exc:
            raise RezRepositoryError(f"Failed to load Rez repository '{path}': {exc}") from exc
        repos.append(RepositoryInfo(path=path, label=label, packages=packages))
    return repos


def clear_package_cache() -> None:
    """Clear cached Rez package repository data."""
    from rez.packages import package_repository_manager

    package_repository_manager.clear_caches()


def get_package_info(name: str, version: str, repo_paths: list[str]) -> PackageInfo | None:
    """Retrieve detailed info for a specific package name and version."""
    from rez.packages import Package, get_package  # noqa: PLC0415
    from rez.version import Version  # noqa: PLC0415

    try:
        pkg: Package | None = get_package(name, Version(version), paths=repo_paths)
    except _package_query_exception_types() as exc:
        raise RezPackageQueryError(
            f"Failed to query Rez package '{name}-{version}': {exc}"
        ) from exc
    except ValueError as exc:
        raise RezPackageQueryError(
            f"Failed to query Rez package '{name}-{version}': {exc}"
        ) from exc

    if pkg is None:
        return None

    try:
        variants = [
            [requirement.name for requirement in variant] for variant in (pkg.variants or [[]])
        ]
        tools = list(pkg.tools or [])
        requires = [str(r) for r in (pkg.requires or [])]
        description = pkg.description or ""
        python_statements = str(pkg.data.get("commands", ""))
    except _package_query_exception_types() as exc:
        raise RezPackageQueryError(
            f"Failed to query Rez package '{name}-{version}': {exc}"
        ) from exc

    return PackageInfo(
        name=name,
        versions=[version],
        description=description,
        requires=requires,
        variants=variants,
        tools=tools,
        python_statements=python_statements,
    )


def get_package_versions(name: str, repo_paths: list[str]) -> list[str]:
    """Return all available versions for a package name, newest first."""
    from rez.packages import iter_packages  # noqa: PLC0415

    try:
        pkgs = list(iter_packages(name, paths=repo_paths))
    except _package_query_exception_types() as exc:
        raise RezPackageQueryError(
            f"Failed to query Rez package versions for '{name}': {exc}"
        ) from exc

    pkgs.sort(key=lambda p: p.version, reverse=True)
    return [str(p.version) for p in pkgs]


def _repository_exception_types() -> tuple[type[Exception], ...]:
    from rez.exceptions import (  # noqa: PLC0415
        ConfigurationError,
        PackageMetadataError,
        ResourceError,
        RezSystemError,
    )

    return (
        ConfigurationError,
        PackageMetadataError,
        ResourceError,
        RezSystemError,
    )


def _package_query_exception_types() -> tuple[type[Exception], ...]:
    from rez.exceptions import (  # noqa: PLC0415
        ConfigurationError,
        PackageMetadataError,
        ResourceError,
        RezSystemError,
    )

    return (
        ConfigurationError,
        PackageMetadataError,
        ResourceError,
        RezSystemError,
    )
