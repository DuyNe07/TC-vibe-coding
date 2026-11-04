"""Base classes for persistence (``repositories/`` folder).

``BaseRepository`` implements the CRUD API once (template method); storage subclasses only
implement ``_load`` / ``_save``. Features subclass ``SqlRepository[MyEntity]`` (database, the default);
``JsonFileRepository`` (files in data/) and ``InMemoryRepository`` (tests) keep the same API.

Soft delete everywhere (SUPREME-RULES.md): ``delete`` / ``clear`` only set the entity's delete flag
(``is_deleted``, ``deleted_at``, ``deleted_by``); every read skips flagged rows; ``restore`` clears the flag and
``list_deleted`` lists them. ``_load`` returns every stored row, flagged ones included.
"""

import importlib
import json
import os
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from functools import lru_cache
from pathlib import Path
from typing import Any, ClassVar, Generic, TypeVar

from sqlalchemy import delete, insert, select

from backend.core import db
from backend.core.base._generics import generic_args
from backend.core.base.base_model import BaseEntity
from backend.core.config import get_settings
from backend.core.current_user import get_current_user
from backend.core.exceptions import ConfigurationError, ConflictError, NotFoundError
from backend.core.logger import get_logger
from backend.core.naming import DEVELOPER_PATTERN, feature_key_from_module, table_prefix, to_snake_case

TEntity = TypeVar("TEntity", bound=BaseEntity)


def _who() -> str | None:
    """Username recorded in ``deleted_by`` (None for system code and tests)."""
    user = get_current_user()
    return user.username if user else None


class BaseRepository(ABC, Generic[TEntity]):
    """Stores and retrieves entities of ONE type. No business logic here."""

    entity_type: ClassVar[type[BaseEntity]]

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        args = generic_args(cls, BaseRepository)
        if args and isinstance(args[0], type):
            if not issubclass(args[0], BaseEntity):
                raise ConfigurationError(f"{cls.__name__}: entity type must inherit BaseEntity")
            cls.entity_type = args[0]

    def __init__(self) -> None:
        if not hasattr(type(self), "entity_type"):
            raise ConfigurationError(f"{type(self).__name__} must be declared as XxxRepository[MyEntity]")
        self._lock = threading.RLock()

    # ---- storage primitives (implemented by storage classes, NOT by features) ----
    @abstractmethod
    def _load(self) -> dict[str, TEntity]:
        """Every stored entity, flagged (deleted) ones included."""

    @abstractmethod
    def _save(self, items: dict[str, TEntity]) -> None: ...

    def _not_found(self, entity_id: str) -> NotFoundError:
        return NotFoundError(f"Can not find entity {self.entity_type.__name__} with id '{entity_id}'.")

    # ---- read API (deleted rows are skipped everywhere) ----
    def get(self, entity_id: str) -> TEntity | None:
        entity = self._load().get(entity_id)
        return entity if entity is not None and not entity.is_deleted else None

    def get_or_raise(self, entity_id: str) -> TEntity:
        entity = self.get(entity_id)
        if entity is None:
            raise self._not_found(entity_id)
        return entity

    def list_all(self) -> list[TEntity]:
        return [item for item in self._load().values() if not item.is_deleted]

    def find(self, predicate: Callable[[TEntity], bool]) -> list[TEntity]:
        return [item for item in self._load().values() if not item.is_deleted and predicate(item)]

    def find_one(self, predicate: Callable[[TEntity], bool]) -> TEntity | None:
        return next((item for item in self._load().values() if not item.is_deleted and predicate(item)), None)

    def find_by(self, **fields: Any) -> list[TEntity]:
        """Rows whose fields equal the given values: ``repo.find_by(code="A01", status=Status.OPEN)``.

        Prefer it to ``find(lambda ...)`` for lookups by value: ``SqlRepository`` answers it from an index built
        once per loaded table, so a loop of lookups stays fast on big tables."""
        self._check_fields(fields)
        return self.find(lambda item: all(getattr(item, name) == value for name, value in fields.items()))

    def exists(self, entity_id: str) -> bool:
        return self.get(entity_id) is not None

    def count(self) -> int:
        return len(self.list_all())

    def list_deleted(self) -> list[TEntity]:
        """Rows flagged as deleted (e.g. for a "Thùng rác" screen with ``restore``)."""
        return [item for item in self._load().values() if item.is_deleted]

    def _check_fields(self, fields: dict[str, Any]) -> None:
        unknown = sorted(set(fields) - set(self.entity_type.model_fields))
        if not fields or unknown:
            raise ConfigurationError(f"{type(self).__name__}.find_by(): unknown or missing fields {unknown}")

    # ---- write API ----
    def add(self, entity: TEntity) -> TEntity:
        with self._lock:
            items = self._load()
            if entity.id in items:
                raise ConflictError(f"Entity {self.entity_type.__name__} with id '{entity.id}' already exists.")
            items[entity.id] = entity
            self._save(items)
        return entity

    def update(self, entity: TEntity) -> TEntity:
        with self._lock:
            items = self._load()
            stored = items.get(entity.id)
            if stored is None or stored.is_deleted:
                raise self._not_found(entity.id)
            entity.touch()
            items[entity.id] = entity
            self._save(items)
        return entity

    def save(self, entity: TEntity) -> TEntity:
        """Insert or update (upsert)."""
        return self.save_many([entity])[0]

    def save_many(self, entities: Iterable[TEntity]) -> list[TEntity]:
        saved = list(entities)
        with self._lock:
            items = self._load()
            for entity in saved:
                if entity.id in items:
                    entity.touch()
                items[entity.id] = entity
            self._save(items)
        return saved

    def delete(self, entity_id: str) -> None:
        """Soft delete: the row stays, flagged ``is_deleted`` (who and when are recorded)."""
        with self._lock:
            items = self._load()
            stored = items.get(entity_id)
            if stored is None or stored.is_deleted:
                raise self._not_found(entity_id)
            items[entity_id] = stored.marked_deleted(_who())
            self._save(items)

    def restore(self, entity_id: str) -> TEntity:
        """Clear the delete flag of a deleted row."""
        with self._lock:
            items = self._load()
            stored = items.get(entity_id)
            if stored is None or not stored.is_deleted:
                raise self._not_found(entity_id)
            items[entity_id] = restored = stored.restored()
            self._save(items)
        return restored

    def clear(self) -> None:
        """Soft delete every row."""
        with self._lock:
            who = _who()
            items = {key: item if item.is_deleted else item.marked_deleted(who) for key, item in self._load().items()}
            self._save(items)


class InMemoryRepository(BaseRepository[TEntity]):
    """Keeps entities in memory (lost on restart). Use for tests or temporary data only."""

    def __init__(self) -> None:
        super().__init__()
        self._items: dict[str, TEntity] = {}

    def _load(self) -> dict[str, TEntity]:
        return {key: item.model_copy(deep=True) for key, item in self._items.items()}

    def _save(self, items: dict[str, TEntity]) -> None:
        self._items = {key: item.model_copy(deep=True) for key, item in items.items()}


_FILE_LOCKS: dict[Path, threading.RLock] = {}
_FILE_LOCKS_GUARD = threading.Lock()


def _lock_for(path: Path) -> threading.RLock:
    with _FILE_LOCKS_GUARD:
        return _FILE_LOCKS.setdefault(path, threading.RLock())


class JsonFileRepository(BaseRepository[TEntity]):
    """Persists entities in ``data/<feature_key>/<storage_file>`` as JSON (file-shaped data only).

    Subclass and set ``storage_file``::

        class ProductRepository(JsonFileRepository[Product]):
            storage_file = "products.json"
    """

    storage_file: ClassVar[str] = ""

    def __init__(self, file_path: Path | None = None) -> None:
        super().__init__()
        self.file_path = file_path or self._default_path()
        self._lock = _lock_for(self.file_path)

    def _default_path(self) -> Path:
        if not self.storage_file:
            raise ConfigurationError(f"{type(self).__name__} must define storage_file = 'xxx.json'")
        feature_key = feature_key_from_module(type(self).__module__) or "_shared"
        return get_settings().feature_data_dir(feature_key) / self.storage_file

    def _load(self) -> dict[str, TEntity]:
        if not self.file_path.exists():
            return {}
        raw = json.loads(self.file_path.read_text(encoding="utf-8") or "[]")
        entities = [self.entity_type.model_validate(item) for item in raw]
        return {entity.id: entity for entity in entities}  # type: ignore[misc]

    def _save(self, items: dict[str, TEntity]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [item.to_document() for item in items.values()]
        tmp = self.file_path.with_suffix(self.file_path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.file_path)  # atomic write


MAX_TABLE_NAME = 63  # PostgreSQL identifier limit
_CHUNK = 500  # ids per IN (...) clause, below every driver's parameter limit


def _chunks(values: list[str]) -> list[list[str]]:
    return [values[start : start + _CHUNK] for start in range(0, len(values), _CHUNK)]


@lru_cache(maxsize=256)
def feature_developer(feature_key: str) -> str:
    """Table prefix of a feature, from ``DEVELOPER = "<github username>"`` in ``backend/features/<key>/__init__.py``.

    Cached: every repository instance (one per service call) asks for it."""
    developer = getattr(importlib.import_module(f"backend.features.{feature_key}"), "DEVELOPER", "")
    if not isinstance(developer, str) or not DEVELOPER_PATTERN.match(developer):
        raise ConfigurationError(
            f'backend/features/{feature_key}/__init__.py must declare DEVELOPER = "<github username>" '
            "(prefix of the feature's database tables, shared database)"
        )
    return table_prefix(developer)


class SqlRepository(BaseRepository[TEntity]):
    """Persists entities in the app database (PostgreSQL; SQLite in tests): one table per repository,
    one JSON document per entity. DEFAULT storage of every feature::

        class ProductRepository(SqlRepository[Product]):
            pass  # table "<developer>__sample_product_import__product"; table_name = "..." replaces "product"

    One database is shared by every developer: a feature's tables start with the GitHub username declared in
    ``backend/features/<key>/__init__.py`` as ``DEVELOPER = "<github username>"``.

    Same API as ``JsonFileRepository``. Reads come from a RAM cache of the whole table (``db.cached_table``), so a
    page rerun costs no database round trip; ``find_by`` uses an index built once per loaded table; every write is
    one async SQLAlchemy transaction (``db.run``) and clears the table's cache. Entities read are SHARED by every
    caller: never change one in place without saving it, use ``entity.model_copy(update={...})``.
    """

    table_name: ClassVar[str] = ""

    def __init__(self) -> None:
        super().__init__()
        self.table = db.document_table(self._full_table_name())

    def _full_table_name(self) -> str:
        """Feature: ``<developer>__<feature_key>__<name>``; framework (no feature): ``table_name`` or ``core__<name>``."""
        name = self.table_name or to_snake_case(type(self).__name__.removesuffix("Repository"))
        feature_key = feature_key_from_module(type(self).__module__)
        if feature_key is None:
            return name if self.table_name else f"core__{name}"
        full = f"{feature_developer(feature_key)}__{feature_key}__{name}"
        if len(full) > MAX_TABLE_NAME:
            raise ConfigurationError(
                f"Table name {full!r} is longer than {MAX_TABLE_NAME} characters: set a shorter table_name"
            )
        return full

    # ---- async primitives ----
    async def _fetch(self) -> dict[str, TEntity]:
        await db.ensure_table(self.table)
        async with db.engine().connect() as connection:
            rows = (await connection.execute(select(self.table))).all()
        limit = get_settings().db_warn_rows
        if len(rows) > limit:
            get_logger(type(self).__module__).warning(
                "Table %s has %s rows (> %s): it is kept in RAM and filtered in Python, expect slow pages",
                self.table.name, len(rows), limit,
            )  # fmt: skip
        known = self.entity_type.model_fields
        # keys written by a NEWER app version on the shared database are ignored, never an error
        return {
            row.id: self.entity_type.model_validate({k: v for k, v in row.data.items() if k in known}) for row in rows
        }  # type: ignore[misc]

    async def _write(self, entities: list[TEntity], replace_ids: list[str]) -> int:
        """Upsert ``entities`` (rows ``replace_ids`` are replaced) in one transaction. Returns rows replaced.
        The only physical DELETE is this replace of a row by its new version (and ``_purge``)."""
        await db.ensure_table(self.table)
        replaced = 0
        try:
            async with db.engine().begin() as connection:
                for chunk in _chunks(replace_ids):
                    statement = delete(self.table).where(self.table.c.id.in_(chunk))
                    replaced += (await connection.execute(statement)).rowcount
                if entities:
                    rows = [{"id": e.id, "data": e.to_document()} for e in entities]
                    await connection.execute(insert(self.table), rows)
        finally:
            db.table_changed(self.table.name)
        return replaced

    # ---- storage primitives ----
    # ponytail: whole tables live in RAM and are filtered in Python; add SQL filters on `data` past ~200k rows
    def _stored(self) -> dict[str, TEntity]:
        """Every stored row (RAM cache, else the database), deleted ones included. SHARED: never change the dict.
        Not overridden: subclasses may seed in ``_load``."""
        items = db.cached_table(self.table.name)
        if items is None:
            version = db.data_version()
            items = db.run(self._fetch())
            db.cache_table(self.table.name, items, version)
        return items

    def _load(self) -> dict[str, TEntity]:
        return dict(self._stored())

    def preload(self) -> None:
        """Read the table into the RAM cache now, without seeding (warm-up while the login form is shown)."""
        self._stored()

    def _save(self, items: dict[str, TEntity]) -> None:
        """Whole-table save: upsert ``items``; stored rows missing from ``items`` are flagged deleted, never removed."""
        who = _who()
        gone = [e.marked_deleted(who) for key, e in self._stored().items() if key not in items and not e.is_deleted]
        changed = [*items.values(), *gone]
        db.run(self._write(changed, [e.id for e in changed]))

    def _purge(self, entity_ids: list[str]) -> None:
        """HARD delete. Framework only (expired login sessions); features never call it (tests/architecture)."""
        db.run(self._write([], entity_ids))

    # ---- row-level API (no full-table copy or rewrite) ----
    def get(self, entity_id: str) -> TEntity | None:
        entity = self._stored().get(entity_id)
        return entity if entity is not None and not entity.is_deleted else None

    def find_by(self, **fields: Any) -> list[TEntity]:
        self._check_fields(fields)
        names = tuple(sorted(fields))
        wanted = tuple(fields[name] for name in names)
        self._stored()  # load the table first: the index belongs to this loaded version

        def build() -> dict[tuple[Any, ...], list[TEntity]]:
            index: dict[tuple[Any, ...], list[TEntity]] = {}
            for item in self._load().values():
                if not item.is_deleted:
                    index.setdefault(tuple(getattr(item, name) for name in names), []).append(item)
            return index

        try:
            return list(db.table_index(self.table.name, ("find_by", names), build).get(wanted, ()))
        except TypeError:  # unhashable values (lists, dicts): plain scan
            return super().find_by(**fields)

    def add(self, entity: TEntity) -> TEntity:
        with self._lock:
            if entity.id in self._stored():
                raise ConflictError(f"Entity {self.entity_type.__name__} with id '{entity.id}' already exists.")
            db.run(self._write([entity], [entity.id]))
        return entity

    def update(self, entity: TEntity) -> TEntity:
        with self._lock:
            if not self.exists(entity.id):
                raise self._not_found(entity.id)
            entity.touch()
            db.run(self._write([entity], [entity.id]))
        return entity

    def save_many(self, entities: Iterable[TEntity]) -> list[TEntity]:
        saved = list(entities)
        with self._lock:
            existing = self._stored()
            for entity in saved:
                if entity.id in existing:
                    entity.touch()
            db.run(self._write(saved, [entity.id for entity in saved]))
        return saved

    def delete(self, entity_id: str) -> None:
        with self._lock:
            stored = self.get(entity_id)
            if stored is None:
                raise self._not_found(entity_id)
            db.run(self._write([stored.marked_deleted(_who())], [entity_id]))

    def restore(self, entity_id: str) -> TEntity:
        with self._lock:
            stored = self._stored().get(entity_id)
            if stored is None or not stored.is_deleted:
                raise self._not_found(entity_id)
            restored = stored.restored()
            db.run(self._write([restored], [entity_id]))
        return restored

    def clear(self) -> None:
        with self._lock:
            who = _who()
            marked = [e.marked_deleted(who) for e in self._stored().values() if not e.is_deleted]
            if marked:
                db.run(self._write(marked, [e.id for e in marked]))
