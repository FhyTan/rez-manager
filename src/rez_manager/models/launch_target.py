"""Central launch target definitions used across models, UI, and persistence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from rez_manager.runtime import IS_WINDOWS


class LaunchTarget(StrEnum):
    BLENDER = "Blender"
    MAYA = "Maya"
    HOUDINI = "Houdini"
    NUKE = "Nuke"
    NUKE_X = "NukeX"
    SHELL = "Shell"
    CUSTOM = "Custom"


def parse_launch_target(value: object) -> LaunchTarget:
    """Parse a launch target from persisted or UI-provided values."""

    if isinstance(value, LaunchTarget):
        return value
    if not isinstance(value, str):
        raise TypeError("launch_target must be a string")
    return LaunchTarget(value.strip())


@dataclass(frozen=True, slots=True)
class LaunchTargetDefinition:
    """Metadata and behavior for a single launch target."""

    value: LaunchTarget
    color: str
    command: str | None
    icon_name: str = ""

    @property
    def label(self) -> str:
        return self.value.value

    @property
    def icon_source(self) -> str:
        if not self.icon_name:
            return ""
        return f"qrc:/icons/dcc/{self.icon_name}"

    def resolve_command(self, custom_command: str | None = None) -> str | None:
        """Return the command to launch this target."""

        if self.value is not LaunchTarget.CUSTOM:
            return self.command

        command = (custom_command or "").strip()
        if not command:
            raise ValueError("Custom launch target requires a custom command.")
        return command


@dataclass(frozen=True, slots=True)
class LaunchTargetCatalog:
    """Registry of all supported launch targets in UI display order."""

    shell: LaunchTargetDefinition = LaunchTargetDefinition(
        value=LaunchTarget.SHELL,
        color="#4A88D8",
        command=None,
        icon_name="Shell",
    )
    maya: LaunchTargetDefinition = LaunchTargetDefinition(
        value=LaunchTarget.MAYA,
        color="#4DB880",
        command="maya",
        icon_name="Maya",
    )
    houdini: LaunchTargetDefinition = LaunchTargetDefinition(
        value=LaunchTarget.HOUDINI,
        color="#D98A38",
        command="houdini",
        icon_name="Houdini",
    )
    blender: LaunchTargetDefinition = LaunchTargetDefinition(
        value=LaunchTarget.BLENDER,
        color="#F08A28",
        command="blender",
        icon_name="Blender",
    )
    nuke: LaunchTargetDefinition = LaunchTargetDefinition(
        value=LaunchTarget.NUKE,
        color="#79C94B",
        command="nuke",
        icon_name="Nuke",
    )
    nuke_x: LaunchTargetDefinition = LaunchTargetDefinition(
        value=LaunchTarget.NUKE_X,
        color="#39B7A5",
        command="nukex",
        icon_name="NukeX",
    )
    custom: LaunchTargetDefinition = LaunchTargetDefinition(
        value=LaunchTarget.CUSTOM,
        color="#8A58D8",
        command=None,
    )

    def all(self) -> tuple[LaunchTargetDefinition, ...]:
        return (
            self.shell,
            self.maya,
            self.houdini,
            self.blender,
            self.nuke,
            self.nuke_x,
            self.custom,
        )

    def from_value(self, value: object) -> LaunchTargetDefinition:
        parsed_value = parse_launch_target(value)
        for target in self.all():
            if target.value is parsed_value:
                return target
        raise ValueError(f"Unsupported launch target: {parsed_value}")

    def command_for(self, value: object, custom_command: str | None = None) -> str | None:
        return self.from_value(value).resolve_command(custom_command)

    def launch_command_for(self, value: object, custom_command: str | None = None) -> str | None:
        command = self.command_for(value, custom_command)
        if command and IS_WINDOWS:
            return f'start "" {command}'
        return command

    def color_for(self, value: object) -> str:
        return self.from_value(value).color

    def label_for(self, value: object) -> str:
        return self.from_value(value).label


LAUNCH_TARGETS = LaunchTargetCatalog()
