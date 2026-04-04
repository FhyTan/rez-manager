"""Rez context adapter — create, resolve, serialize, and preview contexts."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class ResolveResult:
    success: bool
    packages: list[str]
    environ: dict[str, str]
    tools: list[str]
    error: str | None = None


def resolve_context(package_requests: list[str]) -> ResolveResult:
    """Resolve a list of package requests using the Rez Python API.

    Returns a ResolveResult with resolved packages, environment variables,
    and available tools. On failure, success=False and error contains the message.
    """
    try:
        from rez.resolved_context import ResolvedContext  # noqa: PLC0415

        ctx = ResolvedContext(package_requests)
        environ = dict(ctx.get_environ())
        packages = [str(p) for p in ctx.resolved_packages]
        tools = list(ctx.get_tools().keys())
        return ResolveResult(success=True, packages=packages, environ=environ, tools=tools)
    except Exception as exc:  # noqa: BLE001
        return ResolveResult(success=False, packages=[], environ={}, tools=[], error=str(exc))


def save_context(package_requests: list[str], path: str) -> tuple[bool, str]:
    """Serialize a resolved context to a .rxt file at the given path.

    Returns (success, error_message).
    """
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
        environ = dict(ctx.get_environ())
        packages = [str(p) for p in ctx.resolved_packages]
        tools = list(ctx.get_tools().keys())
        return ResolveResult(success=True, packages=packages, environ=environ, tools=tools)
    except Exception as exc:  # noqa: BLE001
        return ResolveResult(success=False, packages=[], environ={}, tools=[], error=str(exc))


def launch_context(package_requests: list[str], command: list[str]) -> subprocess.Popen:
    """Launch a subprocess inside a resolved Rez context."""
    from rez.resolved_context import ResolvedContext  # noqa: PLC0415

    ctx = ResolvedContext(package_requests)
    return ctx.execute_shell(command=command, detached=True)
