"""Tests for Rez context launch adapter helpers."""

from __future__ import annotations

import sys
import types


def test_launch_context_passes_none_command_to_rez(monkeypatch):
    from rez_manager.adapter.context import launch_context

    captured: dict[str, object] = {}

    class FakeResolvedContext:
        def __init__(self, package_requests, *, package_paths=None):
            captured["package_requests"] = list(package_requests)
            captured["package_paths"] = package_paths

        def execute_shell(self, **kwargs):
            captured["execute_shell"] = kwargs
            return "process"

    rez_module = types.ModuleType("rez")
    resolved_context_module = types.ModuleType("rez.resolved_context")
    resolved_context_module.ResolvedContext = FakeResolvedContext
    monkeypatch.setitem(sys.modules, "rez", rez_module)
    monkeypatch.setitem(sys.modules, "rez.resolved_context", resolved_context_module)

    process = launch_context(
        ["maya-2025.0"],
        None,
        package_paths=["D:\\packages\\maya"],
    )

    assert process == "process"
    assert captured["package_paths"] == ["D:\\packages\\maya"]
    assert captured["execute_shell"]["command"] is None
