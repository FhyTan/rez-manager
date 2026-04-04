"""Project data model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Project:
    name: str
    thumbnail_path: str = ""
    contexts_dir: str = ""  # absolute path to this project's context folder

    @property
    def display_name(self) -> str:
        return self.name
