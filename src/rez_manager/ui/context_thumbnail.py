"""Thumbnail normalization helpers for persisted contexts."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QImage, QImageReader, QPainter

from rez_manager.persistence.filesystem import THUMBNAIL_FILE_NAME

THUMBNAIL_IMAGE_SIZE = QSize(128, 128)


def normalize_context_thumbnail(source: str, destination: Path, size: QSize) -> None:
    """Load an image source, fit it into a fixed canvas, and save it as a PNG."""
    normalized_source = _normalized_image_source(source)
    if not normalized_source:
        raise ValueError("Thumbnail source cannot be empty.")

    reader = QImageReader(normalized_source)
    reader.setAutoTransform(True)
    image = reader.read()
    if image.isNull():
        raise ValueError(f"Failed to load thumbnail image: {reader.errorString()}")

    composed = QImage(size, QImage.Format.Format_ARGB32_Premultiplied)
    composed.fill(Qt.GlobalColor.transparent)

    scaled = image.scaled(
        size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    offset_x = (size.width() - scaled.width()) // 2
    offset_y = (size.height() - scaled.height()) // 2

    painter = QPainter(composed)
    painter.drawImage(offset_x, offset_y, scaled)
    painter.end()

    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_destination = destination.with_name(f"{destination.name}.tmp")
    if temp_destination.exists():
        temp_destination.unlink()
    if not composed.save(str(temp_destination), "PNG"):
        raise ValueError(f"Failed to save thumbnail image to '{destination}'.")
    temp_destination.replace(destination)


def write_context_thumbnail_png(
    source: str,
    context_path: Path,
    size: QSize = THUMBNAIL_IMAGE_SIZE,
) -> Path:
    """Write a normalized thumbnail.png for a context."""
    destination = context_path / THUMBNAIL_FILE_NAME
    normalize_context_thumbnail(source, destination, size)
    return destination


def remove_context_thumbnail(context_path: Path) -> None:
    """Remove the normalized thumbnail file if it exists."""
    thumbnail_path = context_path / THUMBNAIL_FILE_NAME
    if thumbnail_path.exists():
        thumbnail_path.unlink()


def thumbnail_file_url(path: Path, *, query_key: str = "mtime") -> str:
    """Return a cache-busted file URL for a thumbnail image."""
    if not path.exists():
        return ""

    url = QUrl.fromLocalFile(str(path.resolve()))
    url.setQuery(f"{query_key}={path.stat().st_mtime_ns}")
    return url.toString()


def apply_context_thumbnail_selection(
    context_path: Path,
    *,
    builtin_thumbnail_source: str | None,
    thumbnail_source: str | None,
    size: QSize = THUMBNAIL_IMAGE_SIZE,
) -> None:
    """Apply the persisted thumbnail selection for a context."""
    if (builtin_thumbnail_source or "").strip():
        remove_context_thumbnail(context_path)
        return

    normalized_source = (thumbnail_source or "").strip()
    if not normalized_source:
        remove_context_thumbnail(context_path)
        return

    write_context_thumbnail_png(normalized_source, context_path, size)


def _normalized_image_source(source: str) -> str:
    stripped_source = source.strip()
    if not stripped_source:
        return ""
    if stripped_source.startswith("qrc:/"):
        return ":" + stripped_source.removeprefix("qrc:")

    url = QUrl(stripped_source)
    if url.isLocalFile():
        return url.toLocalFile()
    return stripped_source
