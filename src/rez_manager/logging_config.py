"""Centralized application logging configuration."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from rez_manager.persistence.app_paths import log_file_path


def configure_logging() -> Path:
    """Configure Loguru sinks for console and rotating file output."""

    target_path = log_file_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        backtrace=False,
        diagnose=False,
        format=("{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} - {message}"),
    )
    logger.add(
        target_path,
        level="DEBUG",
        rotation="5 MB",
        retention="14 days",
        encoding="utf-8",
        backtrace=True,
        diagnose=False,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | "
            "{process.name}:{thread.name} | {name}:{function}:{line} - {message}"
        ),
    )
    logger.debug("Logging configured at {}", target_path)
    return target_path
