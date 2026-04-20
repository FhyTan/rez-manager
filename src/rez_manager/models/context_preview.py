"""Data models for resolved context preview payloads."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PreviewEnvironmentEntry:
    """A single environment variable displayed in the preview."""

    name: str
    value: str


@dataclass(frozen=True)
class PreviewEnvironmentSection:
    """A named section of environment variables."""

    title: str
    entries: list[PreviewEnvironmentEntry] = field(default_factory=list)


@dataclass(frozen=True)
class PreviewResolvedPackage:
    """A resolved package shown in the preview."""

    name: str
    version: str
    label: str


@dataclass(frozen=True)
class ContextPreviewData:
    """Structured preview data exposed to the UI."""

    packages: list[PreviewResolvedPackage] = field(default_factory=list)
    sections: list[PreviewEnvironmentSection] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
