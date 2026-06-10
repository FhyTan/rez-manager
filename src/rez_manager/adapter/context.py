"""Rez context adapter — resolve, serialize, launch, and introspect contexts."""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from os import environ
from pathlib import Path

from loguru import logger

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
class ContextInfo:
    """Resolved context data returned by the adapter layer.

    ``_resolved_context`` holds the live Rez ``ResolvedContext`` object
    and is consumed by ``save_context`` and ``launch_context`` — external
    code should treat it as opaque.
    """

    packages: list[str]
    environ: dict[str, str]
    tools: list[str]
    _resolved_context: object


def resolve_context(package_requests: list[str]) -> ContextInfo:
    """Resolve a list of package requests using the Rez Python API.

    Args:
        package_requests: A list of Rez package request strings
            (e.g. ``["python-3.10", "maya-2024"]``).

    Returns:
        A ``ContextInfo`` containing resolved packages, environment variables,
        tools, and the opaque resolved context.

    Raises:
        RezResolveError: If the Rez resolve fails for any reason.
    """
    logger.info("Resolving context for requests: {}", package_requests)

    from rez.config import config  # noqa: PLC0415
    from rez.resolved_context import ResolvedContext  # noqa: PLC0415

    cache_path = config.get("cache_packages_path")
    if cache_path:
        Path(str(cache_path)).mkdir(parents=True, exist_ok=True)

    try:
        ctx = ResolvedContext(
            list(package_requests),
            package_paths=config.get("packages_path"),
        )
    except _context_creation_exception_types() as exc:
        logger.error("Failed to resolve context: {}", exc)
        raise RezResolveError(f"Failed to resolve Rez context: {exc}") from exc

    result = _context_info_from_resolved_context(ctx)
    logger.info("Resolved context: {} packages", len(result.packages))
    return result


def load_context(path: str) -> ContextInfo:
    """Load a serialized context from a .rxt file.

    Args:
        path: Filesystem path to the ``.rxt`` file.

    Returns:
        A ``ContextInfo`` containing resolved packages, environment variables,
        tools, and the opaque resolved context.

    Raises:
        RezContextLoadError: If the ``.rxt`` file cannot be loaded.
    """
    logger.info("Loading resolved context from {}", path)

    from rez.resolved_context import ResolvedContext  # noqa: PLC0415

    try:
        ctx = ResolvedContext.load(path)
    except _context_load_exception_types() as exc:
        logger.warning("Failed to load .rxt context from {}: {}", path, exc)
        raise RezContextLoadError(f"Failed to load Rez context from '{path}': {exc}") from exc
    except OSError as exc:
        logger.warning("Failed to load .rxt context from {}: {}", path, exc)
        raise RezContextLoadError(f"Failed to load Rez context from '{path}': {exc}") from exc

    result = _context_info_from_resolved_context(ctx)
    logger.info("Loaded context from .rxt: {} packages", len(result.packages))
    return result


def save_context(context: ContextInfo, path: str) -> None:
    """Serialize an already-resolved context to a .rxt file at the given path.

    Args:
        context: The ``ContextInfo`` to serialize (must hold a live Rez ``ResolvedContext``).
        path: Destination filesystem path for the ``.rxt`` file.

    Raises:
        RezContextSaveError: If the context cannot be saved to disk.
    """
    logger.info("Saving resolved context to {}", path)

    try:
        context._resolved_context.save(path)
    except OSError as exc:
        logger.error("Failed to save .rxt context to {}: {}", path, exc)
        raise RezContextSaveError(f"Failed to save Rez context to '{path}': {exc}") from exc

    logger.info("Saved resolved context to {}", path)


def launch_context(
    context: ContextInfo,
    command: str | None | Sequence[str],
) -> subprocess.Popen:
    """Launch a subprocess inside an already-resolved Rez context.

    Args:
        context: The ``ContextInfo`` to use as the launch environment.
        command: The command to execute; ``None`` for an interactive shell,
            a string for a shell command, or a sequence of strings for a
            direct subprocess invocation.

    Returns:
        A ``subprocess.Popen`` handle for the launched process.

    Raises:
        RezContextLaunchError: If the context cannot be launched.
    """
    logger.info("Launching resolved context with command: {}", command)

    try:
        return context._resolved_context.execute_shell(
            command=_normalized_launch_command(command),
            detached=True,
            block=False,
            start_new_session=True,
            parent_environ=preserved_system_environment(),
        )
    except _context_launch_exception_types() as exc:
        logger.error("Failed to launch context: {}", exc)
        raise RezContextLaunchError(f"Failed to launch Rez context: {exc}") from exc
    except OSError as exc:
        logger.error("Failed to launch context: {}", exc)
        raise RezContextLaunchError(f"Failed to launch Rez context: {exc}") from exc


def system_environment_variable_names(platform_name: str | None = None) -> list[str]:
    """Return the curated system-environment allowlist for a platform.

    Args:
        platform_name: An optional platform name (e.g. ``"windows"``, ``"linux"``,
            ``"macos"``). If ``None``, the current platform is used.

    Returns:
        A list of environment variable names that are preserved for preview and launch.

    Raises:
        TypeError: If the allowlist catalog has an unexpected format.
        ValueError: If the platform is not supported.
    """
    return list(_cached_system_environment_variable_names(platform_name))


@cache
def _cached_system_environment_variable_names(platform_name: str | None = None) -> tuple[str, ...]:
    """Return the immutable cached system-environment allowlist for a platform.

    Args:
        platform_name: An optional platform name. If ``None``, the current platform is used.

    Returns:
        A tuple of environment variable names for the given platform.

    Raises:
        TypeError: If the allowlist catalog has an unexpected format.
        ValueError: If the platform is not supported.
    """
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
    """Return the subset of host environment variables preserved for preview and launch.

    Args:
        process_environ: An optional environment mapping to filter.
            If ``None``, ``os.environ`` is used.
        platform_name: An optional platform name. If ``None``, the current platform is used.

    Returns:
        A dictionary of preserved environment variable names to their values.
    """
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


def _context_info_from_resolved_context(
    ctx: object,
    *,
    process_environ: Mapping[str, str] | None = None,
    platform_name: str | None = None,
) -> ContextInfo:
    """Build a ``ContextInfo`` from a live Rez ``ResolvedContext``.

    Args:
        ctx: A live Rez ``ResolvedContext`` instance.
        process_environ: An optional environment mapping for system variable
            preservation. If ``None``, ``os.environ`` is used.
        platform_name: An optional platform name. If ``None``, the current
            platform is used.

    Returns:
        A ``ContextInfo`` with packages, environment, tools, and the opaque context.

    Raises:
        RezResolveError: If environment extraction fails.
    """
    preserved_environ = preserved_system_environment(
        process_environ=process_environ,
        platform_name=platform_name,
    )
    try:
        effective_environ = {
            str(key): str(value)
            for key, value in ctx.get_environ(parent_environ=preserved_environ).items()
        }
    except _context_creation_exception_types() as exc:
        raise RezResolveError(f"Failed to apply resolved environment: {exc}") from exc
    return ContextInfo(
        packages=[package.qualified_package_name for package in ctx.resolved_packages],
        environ=effective_environ,
        tools=[str(tool) for tool in ctx.get_tools().keys()],
        _resolved_context=ctx,
    )


def _platform_key(platform_name: str | None) -> str:
    """Normalize a platform name or detect the current platform.

    Args:
        platform_name: A platform name string, or ``None`` for auto-detection.

    Returns:
        One of ``"windows"``, ``"macos"``, or ``"linux"``.

    Raises:
        ValueError: If the platform is not supported.
    """
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
