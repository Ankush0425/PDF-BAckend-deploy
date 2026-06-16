"""
Centralized logging system for the PDF Toolkit.
Provides rotating file logs and console output.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import LOGS_DIR


_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
_BACKUP_COUNT = 5

_initialized = False


def _setup_root_logger() -> None:
    """Configure the root logger with file and console handlers."""
    global _initialized
    if _initialized:
        return

    root_logger = logging.getLogger("pdf_toolkit")
    root_logger.setLevel(logging.DEBUG)

    # ── File Handler (rotating) ──
    log_file = LOGS_DIR / "pdf_toolkit.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=_MAX_LOG_SIZE,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root_logger.addHandler(file_handler)

    # ── Console Handler ──
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root_logger.addHandler(console_handler)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger under the pdf_toolkit namespace.

    Args:
        name: Module or component name (e.g., 'pdf_operations', 'ai_features').

    Returns:
        Configured Logger instance.
    """
    _setup_root_logger()
    return logging.getLogger(f"pdf_toolkit.{name}")
