"""Tests for thumbnail normalization helpers."""

from __future__ import annotations

from PySide6.QtGui import QImage


def test_write_context_thumbnail_png_normalizes_raster_image(tmp_path):
    from rez_manager.ui.context_thumbnail import THUMBNAIL_IMAGE_SIZE, write_context_thumbnail_png

    source_path = tmp_path / "source.png"
    image = QImage(320, 120, QImage.Format.Format_ARGB32)
    image.fill(0xFF336699)
    assert image.save(str(source_path), "PNG")

    context_path = tmp_path / "Pipeline" / "Base"
    written_path = write_context_thumbnail_png(str(source_path), context_path)
    written_image = QImage(str(written_path))

    assert written_path == context_path / "thumbnail.png"
    assert written_image.size() == THUMBNAIL_IMAGE_SIZE


def test_write_context_thumbnail_png_normalizes_svg_input(tmp_path):
    from rez_manager.ui.context_thumbnail import THUMBNAIL_IMAGE_SIZE, write_context_thumbnail_png

    source_path = tmp_path / "source.svg"
    source_path.write_text(
        (
            '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100" '
            'viewBox="0 0 200 100">'
            '<rect width="200" height="100" fill="#f08a28"/>'
            '<circle cx="100" cy="50" r="28" fill="#ffffff"/>'
            "</svg>"
        ),
        encoding="utf-8",
    )

    context_path = tmp_path / "Pipeline" / "Comp"
    written_path = write_context_thumbnail_png(str(source_path), context_path)
    written_image = QImage(str(written_path))

    assert written_image.size() == THUMBNAIL_IMAGE_SIZE


def test_apply_context_thumbnail_selection_removes_thumbnail_for_builtin_icon(tmp_path):
    from rez_manager.ui.context_thumbnail import apply_context_thumbnail_selection

    context_path = tmp_path / "Pipeline" / "Base"
    context_path.mkdir(parents=True)
    thumbnail_path = context_path / "thumbnail.png"
    thumbnail_path.write_bytes(b"png")

    apply_context_thumbnail_selection(
        context_path,
        builtin_thumbnail_source="qrc:/icons/dcc/Maya",
        thumbnail_source="",
    )

    assert not thumbnail_path.exists()
