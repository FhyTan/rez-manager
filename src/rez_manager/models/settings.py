"""Application settings data model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AppSettings:
    package_repositories: list[str] = field(default_factory=list)
    contexts_location: str = ""

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
