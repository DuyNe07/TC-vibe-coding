"""One-time warm-up of a fresh server, run in the background while the first login form is on screen.

A new server process pays once for importing every app (seconds) and for the first read of every table over the
network. Doing it while the user types their password makes the first page after login open at normal speed.
"""

import threading
from concurrent.futures import ThreadPoolExecutor

from backend.core import db
from backend.core.base import SqlRepository
from backend.core.logger import get_logger

_lock = threading.Lock()
_started = False
logger = get_logger(__name__)


def start_warm_up() -> None:
    """Start the warm-up once per process (later calls do nothing)."""
    global _started
    with _lock:
        if _started:
            return
        _started = True
    threading.Thread(target=warm_up, name="tc-warm-up", daemon=True).start()


def warm_up() -> None:
    try:
        from frontend.core.registry import FeatureRegistry

        FeatureRegistry.discover()  # imports every app: their repositories become known
        if db.database_url().startswith("sqlite"):
            return  # local file: first reads are already fast (and tests switch databases under our feet)
        with ThreadPoolExecutor(max_workers=8) as pool:  # the reads overlap: one round trip instead of one per table
            list(pool.map(_preload, _repository_classes()))
        logger.info("Warm-up done")
    except Exception:
        logger.exception("Warm-up failed (pages still work, the first one is just slower)")


def _repository_classes() -> list[type[SqlRepository]]:
    found: list[type[SqlRepository]] = []
    todo = list(SqlRepository.__subclasses__())
    while todo:
        cls = todo.pop()
        todo.extend(cls.__subclasses__())
        found.append(cls)
    return found


def _preload(cls: type[SqlRepository]) -> None:
    try:
        cls().preload()  # type: ignore[call-arg]
    except Exception:  # an abstract base or a repository needing arguments: skipped
        logger.debug("Warm-up skipped %s", cls.__name__)
