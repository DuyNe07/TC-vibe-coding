"""Application logging: written to ``logs/app.log`` (not the terminal) and shown in the UI log panel.

Write logs:   logger = get_logger(__name__);  logger.info("Imported %s rows", n)
              (services/controllers/pages already have ``self.logger``)
Read logs:    read_log_entries(feature_key="leave_request", min_level="INFO", limit=200)
              -> used by frontend/core/components/log_panel.py, shown at the bottom of every page.
Never use ``print``.
"""

import logging
import re
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path

from backend.core.config import get_settings

LOG_FILE_NAME = "app.log"
LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_LINE = re.compile(r"^(\d{4}-\d{2}-\d{2} [\d:,]+) \| (\w+)\s* \| (\S+) \| (.*)$")
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


@dataclass(frozen=True)
class LogEntry:
    time: str
    level: str
    source: str
    message: str  # may contain several lines (tracebacks)

    @property
    def text(self) -> str:
        return f"{self.time} | {self.level:<8} | {self.source} | {self.message}"


def read_log_entries(feature_key: str | None = None, min_level: str = "DEBUG", limit: int = 200) -> list[LogEntry]:
    """Last ``limit`` entries (oldest first), optionally only those of one feature."""
    path = log_file_path()
    if not path.exists():
        return []
    entries: list[LogEntry] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = _LINE.match(line)
        if match:
            time, level, source, message = match.groups()
            entries.append(LogEntry(time, level, source.removeprefix(f"{_ROOT}."), message))
        elif entries:  # continuation line of a multi-line message (traceback)
            last = entries[-1]
            entries[-1] = LogEntry(last.time, last.level, last.source, f"{last.message}\n{line}")
    threshold = LEVELS.index(min_level.upper()) if min_level.upper() in LEVELS else 0
    marker = f".features.{feature_key}." if feature_key else ""
    selected = [
        e
        for e in entries
        if (e.level not in LEVELS or LEVELS.index(e.level) >= threshold) and (not marker or marker in f".{e.source}.")
    ]
    return selected[-limit:]
