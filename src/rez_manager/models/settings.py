"""Application settings data model."""

from __future__ import annotations

from dataclasses import dataclass, field
from os import PathLike


@dataclass
class AppSettings:
    package_repositories: list[str] = field(default_factory=list)
    contexts_location: str | PathLike[str] = ""

    def __post_init__(self) -> None:
        self.package_repositories = [str(path) for path in self.package_repositories]
        self.contexts_location = str(self.contexts_location)

    def to_dict(self) -> dict[str, object]:
        return {
            "package_repositories": list(self.package_repositories),
            "contexts_location": self.contexts_location,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> AppSettings:
        package_repositories = data.get("package_repositories", [])
        contexts_location = data.get("contexts_location", "")

        if not isinstance(package_repositories, list):
            raise TypeError("package_repositories must be a list")
        if not isinstance(contexts_location, str):
            raise TypeError("contexts_location must be a string")

        return cls(
            package_repositories=[str(path) for path in package_repositories],
            contexts_location=contexts_location,
        )
