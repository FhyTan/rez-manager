"""Tests for Rez package cache behaviour during context resolution."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from tests.conftest import RezTestPackage


def _wait_for_cache_entry(cache_dir: Path, pkg_name: str, timeout: float = 10.0) -> bool:
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        if (cache_dir / pkg_name).is_dir():
            return True
        time.sleep(0.5)
    return False


def test_cachable_package_is_cached_and_contains_data_file(
    rez_cache_settings,
    rez_pkg_cache_binary,
    temp_cache_dir: Path,
    cachable_pkg: RezTestPackage,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("REZ_PACKAGE_CACHE_SAME_DEVICE", "1")

    from rez_manager.adapter.context import resolve_context

    resolve_context([cachable_pkg.request])

    assert _wait_for_cache_entry(temp_cache_dir, cachable_pkg.name), (
        f"Package '{cachable_pkg.name}' was not cached in {temp_cache_dir}"
    )

    data_files = list((temp_cache_dir / cachable_pkg.name).rglob("data.bin"))
    assert data_files, "data.bin not found in cached package"
    assert data_files[0].stat().st_size == 1024


def test_non_cachable_package_is_not_cached(
    rez_cache_settings,
    rez_pkg_cache_binary,
    temp_cache_dir: Path,
    app_package: RezTestPackage,
    python_311_package: RezTestPackage,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("REZ_PACKAGE_CACHE_SAME_DEVICE", "1")

    from rez_manager.adapter.context import resolve_context

    resolve_context([app_package.request])

    time.sleep(1)

    assert not (temp_cache_dir / app_package.name).is_dir(), (
        f"Non-cachable package '{app_package.name}' should not be cached"
    )
