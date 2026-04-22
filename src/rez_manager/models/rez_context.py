"""Rez context data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING

from .launch_target import LAUNCH_TARGETS, LaunchTarget, LaunchTargetDefinition, parse_launch_target

if TYPE_CHECKING:
    from .project import Project


def _context_store():
    from rez_manager.persistence import context_store

    return context_store

@dataclass
class ContextMeta:
    """Metadata stored in meta.json alongside a context.rxt file."""

    name: str
    description: str = ""
    launch_target: LaunchTarget = LaunchTarget.SHELL
    custom_command: str | None = None
    builtin_thumbnail_source: str | None = None
    packages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "launch_target": self.launch_target.value,
            "custom_command": self.custom_command,
            "builtin_thumbnail_source": self.builtin_thumbnail_source,
            "packages": self.packages,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ContextMeta:
        name = data["name"]
        description = data.get("description", "")
        launch_target = data.get("launch_target", LaunchTarget.SHELL.value)
        custom_command = data.get("custom_command")
        builtin_thumbnail_source = data.get("builtin_thumbnail_source")
        packages = data.get("packages", [])

        if not isinstance(name, str):
            raise TypeError("name must be a string")
        if not isinstance(description, str):
            raise TypeError("description must be a string")
        if not isinstance(launch_target, str):
            raise TypeError("launch_target must be a string")
        if custom_command is not None and not isinstance(custom_command, str):
            raise TypeError("custom_command must be a string or null")
        if builtin_thumbnail_source is not None and not isinstance(builtin_thumbnail_source, str):
            raise TypeError("builtin_thumbnail_source must be a string or null")
        if not isinstance(packages, list) or any(not isinstance(pkg, str) for pkg in packages):
            raise TypeError("packages must be a list of strings")

        return cls(
            name=name,
            description=description,
            launch_target=parse_launch_target(launch_target),
            custom_command=custom_command,
            builtin_thumbnail_source=builtin_thumbnail_source,
            packages=list(packages),
        )


@dataclass
class RezContext:
    """Runtime representation of a context shown in the UI."""

    project: Project
    meta: ContextMeta
    path: str | PathLike[str] = ""

    def __post_init__(self) -> None:
        self.path = str(self.path)

    @classmethod
    def all(cls) -> list[RezContext]:
        return _context_store().list_contexts()

    @classmethod
    def load(cls, project_name: str, context_name: str) -> RezContext:
        return _context_store().load_context(project_name, context_name)

    @classmethod
    def create(cls, project_name: str, meta: ContextMeta) -> RezContext:
        return _context_store().save_context(project_name, meta)

    @property
    def name(self) -> str:
        return self.meta.name

    @property
    def description(self) -> str:
        return self.meta.description

    @property
    def launch_target(self) -> str:
        return self.meta.launch_target.value

    @property
    def launch_target_definition(self) -> LaunchTargetDefinition:
        return LAUNCH_TARGETS.from_value(self.meta.launch_target)

    @property
    def packages(self) -> list[str]:
        return list(self.meta.packages)

    @property
    def project_name(self) -> str:
        return self.project.name

    @property
    def builtin_thumbnail_source(self) -> str:
        return self.meta.builtin_thumbnail_source or ""

    @property
    def thumbnail_path(self) -> str:
        if not self.path:
            return ""
        path = Path(self.path) / "thumbnail.png"
        return str(path) if path.exists() else ""

    @property
    def rxt_path(self) -> str:
        if not self.path:
            return ""
        path = Path(self.path) / "context.rxt"
        return str(path) if path.exists() else ""

    def update(self, project_name: str, meta: ContextMeta) -> RezContext:
        updated = _context_store().save_context(
            project_name,
            meta,
            original_project_name=self.project_name,
            original_context_name=self.name,
        )
        self.project = updated.project
        self.meta = updated.meta
        self.path = updated.path
        return self

    def duplicate(self, target_project_name: str, target_context_name: str) -> RezContext:
        return _context_store().duplicate_context(
            self.project_name,
            self.name,
            target_project_name,
            target_context_name,
        )

    def delete(self) -> None:
        _context_store().delete_context(self.project_name, self.name)
