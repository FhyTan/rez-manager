"""Application exception hierarchy."""

from __future__ import annotations


class RezManagerError(Exception):
    """Base exception for rez-manager."""


class AdapterError(RezManagerError):
    """Base exception raised from adapter boundaries."""


class RezAdapterError(AdapterError):
    """Base exception for adapter failures backed by the Rez API."""


class RezContextError(RezAdapterError):
    """Base exception for Rez context operations."""


class RezResolveError(RezContextError):
    """Raised when Rez fails to resolve a context."""


class RezContextLoadError(RezContextError):
    """Raised when a serialized Rez context cannot be loaded."""


class RezContextSaveError(RezContextError):
    """Raised when a Rez context cannot be saved."""


class RezContextLaunchError(RezContextError):
    """Raised when a Rez context cannot be launched."""


class RezRepositoryError(RezAdapterError):
    """Raised when Rez repository data cannot be enumerated."""


class RezPackageQueryError(RezAdapterError):
    """Raised when Rez package detail queries fail."""
