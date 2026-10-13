"""Database access: SQLAlchemy 2 async engine (PostgreSQL via asyncpg, SQLite via aiosqlite), callable from sync code.

Streamlit pages and services are synchronous. Every coroutine runs on ONE background event loop thread through
``run(...)``, so the async engine and its connection pool always live on the same loop::

    rows = db.run(fetch_rows())      # from sync code (repositories)

Features never use this module directly: they subclass ``SqlRepository`` (``backend.core.base``).
"""

import asyncio
import threading
import time
from collections.abc import Coroutine
from functools import cache
from typing import Any, TypeVar

from sqlalchemy import JSON, URL, Column, MetaData, String, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from backend.core.config import get_settings

T = TypeVar("T")

# ponytail: one loop thread serialises all DB I/O - plenty for an internal app; use a pool of loops if it ever queues
_loop: asyncio.AbstractEventLoop | None = None
_engines: dict[str, AsyncEngine] = {}
_created_tables: set[tuple[str, str]] = set()
_guard = threading.Lock()
# RAM cache of whole tables: (database url, table) -> (loaded at, {id: entity}). This process's writes clear it at
# once; writes by another process (another app instance on the same database) show after db_cache_seconds.
_tables: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}
_version = 0  # +1 on every write: read-only use cases cached by the gateway are keyed by it


def _background_loop() -> asyncio.AbstractEventLoop:
    global _loop
    with _guard:
        if _loop is None:
            # Selector loop on every OS: Windows' default Proactor loop prints WinError 10054 tracebacks whenever
            # the server drops an idle connection.
            _loop = asyncio.SelectorEventLoop()
            threading.Thread(target=_loop.run_forever, name="tc-db-loop", daemon=True).start()
        return _loop


def run(coro: Coroutine[Any, Any, T]) -> T:
    """Run a coroutine on the database loop and wait for its result. Call it from sync code only."""
    return asyncio.run_coroutine_threadsafe(coro, _background_loop()).result()


def database_url() -> str:
    """APP_DATABASE_URL, else PostgreSQL from POSTGRES_* (.env), else SQLite file data/app.db."""
    settings = get_settings()
    if settings.database_url:
        return settings.database_url
    if settings.postgres_ip:
        return URL.create(
            "postgresql+asyncpg",
            username=settings.postgres_user,
            password=settings.postgres_password,
            host=settings.postgres_ip,
            port=settings.postgres_port,
            database=settings.postgres_db,
        ).render_as_string(hide_password=False)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite+aiosqlite:///{(settings.data_dir / 'app.db').as_posix()}"


def engine() -> AsyncEngine:
    url = database_url()
    with _guard:
        if url not in _engines:
            # recycle before servers/firewalls cut idle connections; pre_ping replaces any that died anyway
            _engines[url] = create_async_engine(url, pool_pre_ping=True, pool_recycle=300)
        return _engines[url]


def data_version() -> int:
    return _version


def cached_table(name: str) -> dict[str, Any] | None:
    hit = _tables.get((database_url(), name))
    return hit[1] if hit and time.monotonic() - hit[0] < get_settings().db_cache_seconds else None


def cache_table(name: str, items: dict[str, Any], version_before: int) -> None:
    if version_before == _version:  # no write happened while loading: the rows are current
        _tables[(database_url(), name)] = (time.monotonic(), items)


def table_changed(name: str) -> None:
    global _version
    _tables.pop((database_url(), name), None)
    _version += 1


def dispose_all() -> None:
    """Close every connection pool and forget cached rows (tests switch databases between runs)."""
    with _guard:
        engines = list(_engines.values())
        _engines.clear()
        _created_tables.clear()
        _tables.clear()
    for item in engines:
        run(item.dispose())


@cache
def document_table(name: str) -> Table:
    """A table holding one JSON document per entity: ``id`` (primary key) + ``data``."""
    return Table(
        name,
        MetaData(),
        Column("id", String(64), primary_key=True),
        Column("data", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
    )


async def ensure_table(table: Table) -> None:
    """CREATE TABLE IF NOT EXISTS, once per process and database."""
    current = engine()
    marker = (str(current.url), table.name)
    if marker in _created_tables:
        return
    async with current.begin() as connection:
        await connection.run_sync(table.create, checkfirst=True)
    _created_tables.add(marker)
