"""Application settings data model."""

from __future__ import annotations

from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path


def _settings_store():
    from rez_manager.persistence import settings_store

    return settings_store


@dataclass
class PackageCacheSettings:
    enabled: bool = True
    max_size_gb: int = 2
    ttl_days: int = 30
    path: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "path": self.path,
            "max_size_gb": self.max_size_gb,
            "ttl_days": self.ttl_days,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> PackageCacheSettings:
        return cls(
            enabled=bool(data.get("enabled", True)),
            max_size_gb=int(data.get("max_size_gb", 2)),
            ttl_days=int(data.get("ttl_days", 30)),
            path=str(data.get("path", "")),
        )


@dataclass
class GeneralSettings:
    package_repositories: list[str] = field(default_factory=list)
    contexts_location: str = ""

    def __post_init__(self) -> None:
        self.package_repositories = [str(path) for path in self.package_repositories]
        self.contexts_location = str(self.contexts_location)

    def to_dict(self) -> dict[str, object]:
        return {
            "package_repositories": list(self.package_repositories),
            "contexts_location": self.contexts_location,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> GeneralSettings:
        package_repositories = data.get("package_repositories", [])
        contexts_location = data.get("contexts_location", "")

        if not isinstance(package_repositories, list):
            raise TypeError("package_repositories must be a list")
        if not isinstance(contexts_location, (str, PathLike)):
            raise TypeError("contexts_location must be a string or PathLike")

        return cls(
            package_repositories=[str(path) for path in package_repositories],
            contexts_location=str(contexts_location),
        )


@dataclass(init=False)
class AppSettings:
    general: GeneralSettings
    package_cache: PackageCacheSettings

    def __init__(
        self,
        general: GeneralSettings | None = None,
        package_cache: PackageCacheSettings | None = None,
        **kwargs: object,
    ) -> None:
        if kwargs:
            general = GeneralSettings.from_dict(kwargs)
        if general is None:
            general = GeneralSettings()
        if package_cache is None:
            package_cache = PackageCacheSettings()
        object.__setattr__(self, "general", general)
        object.__setattr__(self, "package_cache", package_cache)

    @classmethod
    def default(cls) -> AppSettings:
        return _settings_store().default_settings()

    @classmethod
    def load(cls) -> AppSettings:
        return _settings_store().load_settings()

    def save(self) -> Path:
        return _settings_store().save_settings(self)

    def to_dict(self) -> dict[str, object]:
        return {
            "general": self.general.to_dict(),
            "package_cache": self.package_cache.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> AppSettings:
        if "general" in data:
            general_data = data.get("general", {})
            pkg_cache_data = data.get("package_cache", {})
            if not isinstance(general_data, dict):
                raise TypeError("general must be a dict")
            if not isinstance(pkg_cache_data, dict):
                raise TypeError("package_cache must be a dict")
            return cls(
                general=GeneralSettings.from_dict(general_data),
                package_cache=PackageCacheSettings.from_dict(pkg_cache_data),
            )

        return cls(
            general=GeneralSettings.from_dict(data),
            package_cache=PackageCacheSettings.from_dict(data.get("package_cache", {})),
        )
