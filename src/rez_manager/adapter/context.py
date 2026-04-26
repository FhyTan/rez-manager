"""Rez context adapter — create, resolve, serialize, and launch contexts."""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from os import environ
from typing import Protocol

from rez_manager.exceptions import (
    RezContextLaunchError,
    RezContextLoadError,
    RezContextSaveError,
    RezResolveError,
)
from rez_manager.runtime import IS_LINUX, IS_MACOS, IS_WINDOWS

_SYSTEM_ENV_CATALOG_NAME = "system_env_vars.json"
_WINDOWS_PLATFORM = "windows"


@dataclass
class ResolveResult:
    packages: list[str]
    environ: dict[str, str]
    tools: list[str]


class _ResolvedContextLike(Protocol):
    resolved_packages: list[object]

    def get_environ(
        self, *, parent_environ: Mapping[str, str] | None = None
    ) -> Mapping[object, object]: ...

    def get_tools(self) -> Mapping[object, object]: ...


def resolve_context(
    package_requests: list[str], *, package_paths: Sequence[str] | None = None
) -> ResolveResult:
    """Resolve a list of package requests using the Rez Python API."""
    try:
        ctx = _create_resolved_context(package_requests, package_paths=package_paths)
    except _context_creation_exception_types() as exc:
        raise RezResolveError(f"Failed to resolve Rez context: {exc}") from exc

    return _resolve_result_from_context(ctx)


def system_environment_variable_names(platform_name: str | None = None) -> list[str]:
    """Return the curated system-environment allowlist for a platform."""
    return list(_cached_system_environment_variable_names(platform_name))


@cache
def _cached_system_environment_variable_names(platform_name: str | None = None) -> tuple[str, ...]:
    """Return the immutable cached system-environment allowlist for a platform."""
    platform_key = _platform_key(platform_name)
    raw_catalog = (
        files("rez_manager.data").joinpath(_SYSTEM_ENV_CATALOG_NAME).read_text(encoding="utf-8")
    )
    catalog = json.loads(raw_catalog)
    if not isinstance(catalog, dict):
        raise TypeError("system_env_vars.json must contain an object keyed by platform.")

    names = catalog.get(platform_key)
    if not isinstance(names, list) or any(not isinstance(name, str) for name in names):
        raise TypeError(f"system_env_vars.json entry '{platform_key}' must be a list of strings.")
    return tuple(names)


def preserved_system_environment(
    *,
    process_environ: Mapping[str, str] | None = None,
    platform_name: str | None = None,
) -> dict[str, str]:
    """Return the subset of host environment variables preserved for preview and launch."""
    source_environ = process_environ if process_environ is not None else environ
    platform_key = _platform_key(platform_name)
    allowed_names = system_environment_variable_names(platform_name)
    allowed_lookup = (
        {name.upper() for name in allowed_names}
        if platform_key == _WINDOWS_PLATFORM
        else set(allowed_names)
    )

    preserved: dict[str, str] = {}
    for key, raw_value in source_environ.items():
        name = str(key)
        lookup_key = name.upper() if platform_key == _WINDOWS_PLATFORM else name
        if lookup_key not in allowed_lookup:
            continue
        preserved[name] = str(raw_value)
    return preserved


def save_context(
    package_requests: list[str],
    path: str,
    *,
    package_paths: Sequence[str] | None = None,
) -> None:
    """Serialize a resolved context to a .rxt file at the given path."""
    try:
        ctx = _create_resolved_context(package_requests, package_paths=package_paths)
        ctx.save(path)
    except _context_creation_exception_types() as exc:
        raise RezContextSaveError(f"Failed to save Rez context to '{path}': {exc}") from exc
    except OSError as exc:
        raise RezContextSaveError(f"Failed to save Rez context to '{path}': {exc}") from exc


def load_context(path: str) -> ResolveResult:
    """Load a serialized context from a .rxt file."""
    try:
        from rez.resolved_context import ResolvedContext  # noqa: PLC0415

        ctx = ResolvedContext.load(path)
    except _context_load_exception_types() as exc:
        raise RezContextLoadError(f"Failed to load Rez context from '{path}': {exc}") from exc
    except OSError as exc:
        raise RezContextLoadError(f"Failed to load Rez context from '{path}': {exc}") from exc

    return _resolve_result_from_context(ctx)


def launch_context(
    package_requests: list[str],
    command: None | str | Sequence[str],
    *,
    package_paths: Sequence[str] | None = None,
) -> subprocess.Popen:
    """Launch a subprocess inside a resolved Rez context."""
    from rez.resolved_context import ResolvedContext

    try:
        ctx: ResolvedContext = _create_resolved_context(
            package_requests,
            package_paths=package_paths,
        )
        return ctx.execute_shell(
            command=_normalized_launch_command(command),
            block=False,
            start_new_session=True,
            parent_environ=preserved_system_environment(),
        )
    except _context_creation_exception_types() as exc:
        raise RezContextLaunchError(f"Failed to launch Rez context: {exc}") from exc
    except _context_launch_exception_types() as exc:
        raise RezContextLaunchError(f"Failed to launch Rez context: {exc}") from exc
    except OSError as exc:
        raise RezContextLaunchError(f"Failed to launch Rez context: {exc}") from exc


def _platform_key(platform_name: str | None) -> str:
    if platform_name is None:
        if IS_WINDOWS:
            return _WINDOWS_PLATFORM
        if IS_MACOS:
            return "macos"
        if IS_LINUX:
            return "linux"
        raise ValueError(
            f"Unsupported platform for system environment preservation: {sys.platform}"
        )

    resolved_platform = platform_name.strip().lower()
    if resolved_platform.startswith("win"):
        return _WINDOWS_PLATFORM
    if resolved_platform.startswith("darwin") or resolved_platform.startswith("mac"):
        return "macos"
    if resolved_platform.startswith("linux"):
        return "linux"
    raise ValueError(f"Unsupported platform for system environment preservation: {platform_name}")


def _resolve_result_from_context(
    context: _ResolvedContextLike,
    *,
    process_environ: Mapping[str, str] | None = None,
    platform_name: str | None = None,
) -> ResolveResult:
    preserved_environ = preserved_system_environment(
        process_environ=process_environ,
        platform_name=platform_name,
    )
    effective_environ = {
        str(key): str(value)
        for key, value in context.get_environ(parent_environ=preserved_environ).items()
    }
    return ResolveResult(
        packages=[package.qualified_package_name for package in context.resolved_packages],
        environ=effective_environ,
        tools=[str(tool) for tool in context.get_tools().keys()],
    )


def _create_resolved_context(
    package_requests: Sequence[str],
    *,
    package_paths: Sequence[str] | None = None,
) -> _ResolvedContextLike:
    from rez.resolved_context import ResolvedContext  # noqa: PLC0415

    resolved_package_paths = (
        None if package_paths is None else [str(path) for path in package_paths]
    )
    return ResolvedContext(list(package_requests), package_paths=resolved_package_paths)


def _normalized_launch_command(command: None | str | Sequence[str]) -> None | str | list[str]:
    if isinstance(command, str):
        return command
    if command is None:
        return None

    return [str(part) for part in command]


def _context_creation_exception_types() -> tuple[type[Exception], ...]:
    from rez.exceptions import (  # noqa: PLC0415
        ConfigurationError,
        PackageCommandError,
        PackageFamilyNotFoundError,
        PackageMetadataError,
        PackageNotFoundError,
        PackageRequestError,
        ResolveError,
        RezSystemError,
    )

    return (
        ConfigurationError,
        PackageCommandError,
        PackageFamilyNotFoundError,
        PackageMetadataError,
        PackageNotFoundError,
        PackageRequestError,
        ResolveError,
        RezSystemError,
    )


def _context_load_exception_types() -> tuple[type[Exception], ...]:
    from rez.exceptions import (  # noqa: PLC0415
        ConfigurationError,
        PackageMetadataError,
        ResolvedContextError,
        ResourceContentError,
        ResourceNotFoundError,
        RezSystemError,
    )

    return (
        ConfigurationError,
        PackageMetadataError,
        ResolvedContextError,
        ResourceContentError,
        ResourceNotFoundError,
        RezSystemError,
    )


def _context_launch_exception_types() -> tuple[type[Exception], ...]:
    from rez.exceptions import (  # noqa: PLC0415
        ConfigurationError,
        PackageCommandError,
        RezSystemError,
    )

    return (
        ConfigurationError,
        PackageCommandError,
        RezSystemError,
    )
