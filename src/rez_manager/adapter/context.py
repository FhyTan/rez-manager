"""Rez context adapter — create, resolve, serialize, launch, and preview contexts."""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from os import environ
from typing import Protocol

from rez_manager.runtime import IS_LINUX, IS_MACOS, IS_WINDOWS

_SYSTEM_ENV_CATALOG_NAME = "system_env_vars.json"
_WINDOWS_PLATFORM = "windows"
_SECTION_USER = "User Environment"
_SECTION_SYSTEM = "System Environment"
_SECTION_REZ = "REZ_ Environment"


@dataclass(frozen=True)
class EnvironmentSection:
    """A logical section of resolved environment variables."""

    title: str
    variables: dict[str, str]


@dataclass
class ResolveResult:
    success: bool
    packages: list[str]
    environ: dict[str, str]
    environ_sections: list[EnvironmentSection]
    tools: list[str]
    error: str | None = None


class _ResolvedContextLike(Protocol):
    resolved_packages: list[object]

    def get_environ(
        self, *, parent_environ: Mapping[str, str] | None = None
    ) -> Mapping[object, object]: ...

    def get_tools(self) -> Mapping[object, object]: ...


def resolve_context(package_requests: list[str]) -> ResolveResult:
    """Resolve a list of package requests using the Rez Python API."""
    try:
        from rez.resolved_context import ResolvedContext  # noqa: PLC0415

        ctx = ResolvedContext(package_requests)
        return _resolve_result_from_context(ctx)
    except Exception as exc:  # noqa: BLE001
        return ResolveResult(
            success=False,
            packages=[],
            environ={},
            environ_sections=[],
            tools=[],
            error=str(exc),
        )


def build_environment_sections(
    *,
    effective_environ: Mapping[str, str],
    preserved_system_environ: Mapping[str, str],
    platform_name: str | None = None,
) -> list[EnvironmentSection]:
    """Split an effective environment into user, system, and Rez-generated sections."""
    platform_key = _platform_key(platform_name)
    if platform_key == _WINDOWS_PLATFORM:
        system_lookup = {
            str(key).upper(): str(value) for key, value in preserved_system_environ.items()
        }
    else:
        system_lookup = {str(key): str(value) for key, value in preserved_system_environ.items()}

    user_entries: dict[str, str] = {}
    rez_entries: dict[str, str] = {}

    for key, raw_value in effective_environ.items():
        name = str(key)
        value = str(raw_value)
        if name.startswith("REZ_"):
            rez_entries[name] = value
            continue

        lookup_key = name.upper() if platform_key == _WINDOWS_PLATFORM else name
        if lookup_key in system_lookup and system_lookup[lookup_key] == value:
            continue
        user_entries[name] = value

    return [
        EnvironmentSection(
            title=_SECTION_USER,
            variables=_sorted_environment_map(user_entries),
        ),
        EnvironmentSection(
            title=_SECTION_SYSTEM,
            variables=_sorted_environment_map(preserved_system_environ),
        ),
        EnvironmentSection(
            title=_SECTION_REZ,
            variables=_sorted_environment_map(rez_entries),
        ),
    ]


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


def save_context(package_requests: list[str], path: str) -> tuple[bool, str]:
    """Serialize a resolved context to a .rxt file at the given path."""
    try:
        from rez.resolved_context import ResolvedContext  # noqa: PLC0415

        ctx = ResolvedContext(package_requests)
        ctx.save(path)
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def load_context(path: str) -> ResolveResult:
    """Load a serialized context from a .rxt file."""
    try:
        from rez.resolved_context import ResolvedContext  # noqa: PLC0415

        ctx = ResolvedContext.load(path)
        return _resolve_result_from_context(ctx)
    except Exception as exc:  # noqa: BLE001
        return ResolveResult(
            success=False,
            packages=[],
            environ={},
            environ_sections=[],
            tools=[],
            error=str(exc),
        )


def launch_context(package_requests: list[str], command: list[str]) -> subprocess.Popen:
    """Launch a subprocess inside a resolved Rez context."""
    from rez.resolved_context import ResolvedContext  # noqa: PLC0415

    ctx = ResolvedContext(package_requests)
    return ctx.execute_shell(
        command=command,
        detached=True,
        block=False,
        start_new_session=True,
        parent_environ=preserved_system_environment(),
    )


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
        success=True,
        packages=[str(package) for package in context.resolved_packages],
        environ=effective_environ,
        environ_sections=build_environment_sections(
            effective_environ=effective_environ,
            preserved_system_environ=preserved_environ,
            platform_name=platform_name,
        ),
        tools=[str(tool) for tool in context.get_tools().keys()],
    )


def _sorted_environment_map(environ_map: Mapping[str, str]) -> dict[str, str]:
    return {
        str(name): str(value)
        for name, value in sorted(environ_map.items(), key=lambda item: item[0].lower())
    }
