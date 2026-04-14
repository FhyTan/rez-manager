"""Project data model."""

from __future__ import annotations

from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .rez_context import RezContext


def _context_store():
    from rez_manager.persistence import context_store

    return context_store


def _project_store():
    from rez_manager.persistence import project_store

    return project_store


@dataclass
class Project:
    name: str
    path: str | PathLike[str] = ""
    contexts: list[RezContext] | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.path = str(self.path)

    @property
    def display_name(self) -> str:
        return self.name

    @property
    def thumbnail_path(self) -> str:
        if not self.path:
            return ""
        path = Path(self.path) / "thumbnail.png"
        return str(path) if path.exists() else ""

    @classmethod
    def all(cls) -> list[Project]:
        return _project_store().list_projects()

    @classmethod
    def create(cls, name: str) -> Project:
        return _project_store().create_project(name)

    @classmethod
    def load(cls, name: str) -> Project:
        return _project_store().get_project(name)

    def load_contexts(self) -> list[RezContext]:
        self.contexts = _context_store().list_project_contexts(self.name, project=self)
        return list(self.contexts)

    def rename(self, new_name: str) -> Project:
        renamed = _project_store().rename_project(self.name, new_name)
        self.name = renamed.name
        self.path = renamed.path
        return self

    def duplicate(self, new_name: str) -> Project:
        return _project_store().duplicate_project(self.name, new_name)

    def delete(self) -> None:
        self.contexts = None
        _project_store().delete_project(self.name)
