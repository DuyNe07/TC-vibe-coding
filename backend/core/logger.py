"""Application logging: written to ``logs/app.log`` only (no log panel in the UI: it slowed every rerun).

Write logs:   logger = get_logger(__name__);  logger.info("Imported %s rows", n)
              (services/controllers/pages already have ``self.logger``)
Errors and warnings are what matter: the gateway logs every failed call; ``scripts/doctor.py`` and the AI repair loop
read ``logs/app.log``. Never use ``print``.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from backend.core.config import get_settings

LOG_FILE_NAME = "app.log"
_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_ROOT = "tc"
_configured = False


def log_file_path() -> Path:
    return get_settings().log_dir / LOG_FILE_NAME


def _configure() -> None:
    global _configured
    if _configured:
        return
    root = logging.getLogger(_ROOT)
    root.setLevel(get_settings().log_level.upper())
    root.propagate = False
    try:
        log_file_path().parent.mkdir(parents=True, exist_ok=True)
        handler: logging.Handler = RotatingFileHandler(
            log_file_path(), maxBytes=2_000_000, backupCount=3, encoding="utf-8"
        )
    except OSError:  # read-only disk: fall back to the terminal
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_FORMAT))
    root.addHandler(handler)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Logger for a module: ``get_logger(__name__)``."""
    _configure()
    return logging.getLogger(f"{_ROOT}.{name}")
