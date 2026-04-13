"""Rez context data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class LaunchTarget(StrEnum):
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
    def from_dict(cls, data: dict[str, object]) -> ContextMeta:
        name = data["name"]
        description = data.get("description", "")
        launch_target = data.get("launch_target", "shell")
        custom_command = data.get("custom_command")
        packages = data.get("packages", [])

        if not isinstance(name, str):
            raise TypeError("name must be a string")
        if not isinstance(description, str):
            raise TypeError("description must be a string")
        if not isinstance(launch_target, str):
            raise TypeError("launch_target must be a string")
        if custom_command is not None and not isinstance(custom_command, str):
            raise TypeError("custom_command must be a string or null")
        if not isinstance(packages, list) or any(not isinstance(pkg, str) for pkg in packages):
            raise TypeError("packages must be a list of strings")

        return cls(
            name=name,
            description=description,
            launch_target=LaunchTarget(launch_target),
            custom_command=custom_command,
            packages=list(packages),
        )


@dataclass
class ContextInfo:
    """Runtime representation of a context shown in the UI."""

    project_name: str
    meta: ContextMeta
    context_dir: str = ""
    rxt_path: str = ""

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
    def packages(self) -> list[str]:
        return list(self.meta.packages)
