"""Rez context adapter — create, resolve, serialize, launch, and preview contexts."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from os import environ
from platform import system

from rez_manager.models.context_preview import (
    ContextPreviewData,
    PreviewEnvironmentEntry,
    PreviewEnvironmentSection,
    PreviewResolvedPackage,
)

_SYSTEM_ENV_CATALOG_NAME = "system_env_vars.json"
_WINDOWS_PLATFORM = "windows"
_SECTION_USER = "User Environment"
_SECTION_SYSTEM = "System Environment"
_SECTION_REZ = "REZ_ Environment"


@dataclass
class ResolveResult:
    success: bool
    packages: list[str]
    environ: dict[str, str]
    tools: list[str]
    error: str | None = None


@dataclass
class ContextPreviewResult:
    success: bool
    preview: ContextPreviewData | None
    effective_environ: dict[str, str]
    error: str | None = None


def resolve_context(package_requests: list[str]) -> ResolveResult:
    """Resolve a list of package requests using the Rez Python API."""
    try:
        from rez.resolved_context import ResolvedContext  # noqa: PLC0415

        ctx = ResolvedContext(package_requests)
        environ_map = {str(key): str(value) for key, value in ctx.get_environ().items()}
        packages = [str(package) for package in ctx.resolved_packages]
        tools = list(ctx.get_tools().keys())
        return ResolveResult(success=True, packages=packages, environ=environ_map, tools=tools)
    except Exception as exc:  # noqa: BLE001
        return ResolveResult(success=False, packages=[], environ={}, tools=[], error=str(exc))


def build_context_preview(
    package_requests: list[str],
    *,
    process_environ: Mapping[str, str] | None = None,
    platform_name: str | None = None,
) -> ContextPreviewResult:
    """Resolve a context and classify its effective environment for preview."""
    try:
        from rez.resolved_context import ResolvedContext  # noqa: PLC0415

        ctx = ResolvedContext(package_requests)
        preserved_system_environ = preserved_system_environment(
            process_environ=process_environ,
            platform_name=platform_name,
        )
        effective_environ = {
            str(key): str(value)
            for key, value in ctx.get_environ(parent_environ=preserved_system_environ).items()
        }
        preview = build_context_preview_data(
            resolved_packages=ctx.resolved_packages,
            effective_environ=effective_environ,
            preserved_system_environ=preserved_system_environ,
            tools=list(ctx.get_tools().keys()),
            platform_name=platform_name,
        )
        return ContextPreviewResult(
            success=True,
            preview=preview,
            effective_environ=effective_environ,
        )
    except Exception as exc:  # noqa: BLE001
        return ContextPreviewResult(
            success=False, preview=None, effective_environ={}, error=str(exc)
        )


def build_context_preview_data(
    *,
    resolved_packages: Sequence[object],
    effective_environ: Mapping[str, str],
    preserved_system_environ: Mapping[str, str],
    tools: Sequence[str] = (),
    platform_name: str | None = None,
) -> ContextPreviewData:
    """Build UI-friendly preview data from resolved package and environment payloads."""
    system_lookup = _environment_lookup(preserved_system_environ, platform_name=platform_name)
    user_entries: dict[str, str] = {}
    rez_entries: dict[str, str] = {}

    for key, raw_value in effective_environ.items():
        name = str(key)
        value = str(raw_value)
        if name.startswith("REZ_"):
            rez_entries[name] = value
            continue

        normalized_key = _normalize_env_key(name, platform_name=platform_name)
        if normalized_key in system_lookup and system_lookup[normalized_key] == value:
            continue
        user_entries[name] = value

    sections = [
        PreviewEnvironmentSection(
            title=_SECTION_USER,
            entries=_sorted_environment_entries(user_entries),
        ),
        PreviewEnvironmentSection(
            title=_SECTION_SYSTEM,
            entries=_sorted_environment_entries(preserved_system_environ),
        ),
        PreviewEnvironmentSection(
            title=_SECTION_REZ,
            entries=_sorted_environment_entries(rez_entries),
        ),
    ]

    return ContextPreviewData(
        packages=_preview_resolved_packages(resolved_packages),
        sections=sections,
        tools=[str(tool) for tool in tools],
    )


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
    allowed_names = {
        _normalize_env_key(name, platform_name=platform_name)
        for name in system_environment_variable_names(platform_name)
    }

    preserved: dict[str, str] = {}
    for key, raw_value in source_environ.items():
        name = str(key)
        if _normalize_env_key(name, platform_name=platform_name) not in allowed_names:
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
        environ_map = {str(key): str(value) for key, value in ctx.get_environ().items()}
        packages = [str(package) for package in ctx.resolved_packages]
        tools = list(ctx.get_tools().keys())
        return ResolveResult(success=True, packages=packages, environ=environ_map, tools=tools)
    except Exception as exc:  # noqa: BLE001
        return ResolveResult(success=False, packages=[], environ={}, tools=[], error=str(exc))


def launch_context(package_requests: list[str], command: list[str]) -> subprocess.Popen:
    """Launch a subprocess inside a resolved Rez context."""
    from rez.resolved_context import ResolvedContext  # noqa: PLC0415

    ctx = ResolvedContext(package_requests)
    return ctx.execute_shell(
        command=command,
        detached=True,
        parent_environ=preserved_system_environment(),
    )


def _platform_key(platform_name: str | None) -> str:
    resolved_platform = (platform_name or system()).strip().lower()
    if resolved_platform.startswith("win"):
        return _WINDOWS_PLATFORM
    if resolved_platform.startswith("darwin") or resolved_platform.startswith("mac"):
        return "macos"
    if resolved_platform.startswith("linux"):
        return "linux"
    raise ValueError(f"Unsupported platform for system environment preservation: {platform_name}")


def _normalize_env_key(name: str, *, platform_name: str | None = None) -> str:
    normalized = str(name)
    return normalized.upper() if _platform_key(platform_name) == _WINDOWS_PLATFORM else normalized


def _environment_lookup(
    environ_map: Mapping[str, str],
    *,
    platform_name: str | None = None,
) -> dict[str, str]:
    return {
        _normalize_env_key(key, platform_name=platform_name): str(value)
        for key, value in environ_map.items()
    }


def _sorted_environment_entries(environ_map: Mapping[str, str]) -> list[PreviewEnvironmentEntry]:
    return [
        PreviewEnvironmentEntry(name=str(name), value=str(value))
        for name, value in sorted(environ_map.items(), key=lambda item: item[0].lower())
    ]


def _preview_resolved_packages(packages: Sequence[object]) -> list[PreviewResolvedPackage]:
    preview_packages: list[PreviewResolvedPackage] = []
    for package in packages:
        name = getattr(package, "name", "")
        version = getattr(package, "version", "")
        label = str(package)
        if not name:
            name, version = _split_package_label(label)
        preview_packages.append(
            PreviewResolvedPackage(
                name=str(name),
                version=str(version) if version else "",
                label=label,
            )
        )
    return preview_packages


def _split_package_label(label: str) -> tuple[str, str]:
    name, separator, version = str(label).rpartition("-")
    if not separator:
        return str(label), ""
    return name, version
