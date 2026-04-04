"""Rez context data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class LaunchTarget(str, Enum):
    MAYA = "maya"
    HOUDINI = "houdini"
    SHELL = "shell"
    CUSTOM = "custom"


@dataclass
class ContextMeta:
    """Metadata stored in meta.json alongside a context.rxt file."""

    name: str
    description: str = ""
    launch_target: LaunchTarget = LaunchTarget.SHELL
    custom_command: str | None = None
    packages: list[str] = field(default_factory=list)
    thumbnail_path: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "launch_target": self.launch_target.value,
            "custom_command": self.custom_command,
            "packages": self.packages,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ContextMeta:
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            launch_target=LaunchTarget(data.get("launch_target", "shell")),
            custom_command=data.get("custom_command"),
            packages=data.get("packages", []),
        )


@dataclass
class ContextInfo:
    """Runtime representation of a context shown in the UI."""

    project_name: str
    meta: ContextMeta
    rxt_path: str = ""

    @property
    def name(self) -> str:
        return self.meta.name
