"""Base classes for persistence (``repositories/`` folder).

``BaseRepository`` implements the CRUD API once (template method); storage subclasses only
implement ``_load`` / ``_save``. Features subclass ``SqlRepository[MyEntity]`` (database, the default);
``JsonFileRepository`` (files in data/) and ``InMemoryRepository`` (tests) keep the same API.
"""

import importlib
import json
import os
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import ClassVar, Generic, TypeVar

from sqlalchemy import delete, insert, select

from backend.core import db
from backend.core.base._generics import generic_args
from backend.core.base.base_model import BaseEntity
from backend.core.config import get_settings
from backend.core.exceptions import ConfigurationError, ConflictError, NotFoundError
from backend.core.naming import DEVELOPER_PATTERN, feature_key_from_module, table_prefix, to_snake_case

TEntity = TypeVar("TEntity", bound=BaseEntity)


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
    def _load(self) -> dict[str, TEntity]: ...

    @abstractmethod
    def _save(self, items: dict[str, TEntity]) -> None: ...

    # ---- read API ----
    def get(self, entity_id: str) -> TEntity | None:
        return self._load().get(entity_id)

    def get_or_raise(self, entity_id: str) -> TEntity:
        entity = self.get(entity_id)
        if entity is None:
            raise NotFoundError(f"Can not find entity {self.entity_type.__name__} with id '{entity_id}'.")
        return entity

    def list_all(self) -> list[TEntity]:
        return list(self._load().values())

    def find(self, predicate: Callable[[TEntity], bool]) -> list[TEntity]:
        return [item for item in self._load().values() if predicate(item)]

    def find_one(self, predicate: Callable[[TEntity], bool]) -> TEntity | None:
        return next((item for item in self._load().values() if predicate(item)), None)

    def exists(self, entity_id: str) -> bool:
        return entity_id in self._load()

    def count(self) -> int:
        return len(self._load())

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
            if entity.id not in items:
                raise NotFoundError(f"Can not find entity {self.entity_type.__name__} with id '{entity.id}'.")
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
        with self._lock:
            items = self._load()
            if items.pop(entity_id, None) is None:
                raise NotFoundError(f"Can not find entity {self.entity_type.__name__} with id '{entity_id}'.")
            self._save(items)

    def clear(self) -> None:
        with self._lock:
            self._save({})


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
    """Persists entities in ``data/<feature_key>/<storage_file>`` as JSON (default storage).

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
        payload = [item.model_dump(mode="json") for item in items.values()]
        tmp = self.file_path.with_suffix(self.file_path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.file_path)  # atomic write


MAX_TABLE_NAME = 63  # PostgreSQL identifier limit
_CHUNK = 500  # ids per IN (...) clause, below every driver's parameter limit


def _chunks(values: list[str]) -> list[list[str]]:
    return [values[start : start + _CHUNK] for start in range(0, len(values), _CHUNK)]


def feature_developer(feature_key: str) -> str:
    """Table prefix of a feature, from ``DEVELOPER = "<github username>"`` in ``backend/features/<key>/__init__.py``."""
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

    Same API as ``JsonFileRepository``; each call is one async SQLAlchemy transaction run through ``db.run``.
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
    async def _fetch(self, ids: list[str] | None = None) -> dict[str, TEntity]:
        await db.ensure_table(self.table)
        statements = (
            [select(self.table)]
            if ids is None
            else [select(self.table).where(self.table.c.id.in_(chunk)) for chunk in _chunks(ids)]
        )
        async with db.engine().connect() as connection:
            rows = [row for statement in statements for row in (await connection.execute(statement)).all()]
        return {row.id: self.entity_type.model_validate(row.data) for row in rows}  # type: ignore[misc]

    async def _write(self, entities: list[TEntity], delete_ids: list[str] | None = None) -> int:
        """Delete ``delete_ids`` (all rows when None), then insert ``entities``; one transaction. Returns rows deleted."""
        await db.ensure_table(self.table)
        deleted = 0
        async with db.engine().begin() as connection:
            if delete_ids is None:
                deleted = (await connection.execute(delete(self.table))).rowcount
            for chunk in _chunks(delete_ids or []):
                deleted += (await connection.execute(delete(self.table).where(self.table.c.id.in_(chunk)))).rowcount
            if entities:
                rows = [{"id": e.id, "data": e.model_dump(mode="json")} for e in entities]
                await connection.execute(insert(self.table), rows)
        return deleted

    # ---- storage primitives (whole table; used by list_all / find / find_one) ----
    # ponytail: queries load the whole table and filter in Python; add SQL filters on `data` past ~100k rows
    def _load(self) -> dict[str, TEntity]:
        return db.run(self._fetch())

    def _save(self, items: dict[str, TEntity]) -> None:
        db.run(self._write(list(items.values())))

    # ---- row-level API (no full-table rewrite) ----
    def get(self, entity_id: str) -> TEntity | None:
        return db.run(self._fetch([entity_id])).get(entity_id)

    def exists(self, entity_id: str) -> bool:
        return self.get(entity_id) is not None

    def count(self) -> int:
        return len(self._load())

    def add(self, entity: TEntity) -> TEntity:
        with self._lock:
            if self.exists(entity.id):
                raise ConflictError(f"Entity {self.entity_type.__name__} with id '{entity.id}' already exists.")
            db.run(self._write([entity], [entity.id]))
        return entity

    def update(self, entity: TEntity) -> TEntity:
        with self._lock:
            if not self.exists(entity.id):
                raise NotFoundError(f"Can not find entity {self.entity_type.__name__} with id '{entity.id}'.")
            entity.touch()
            db.run(self._write([entity], [entity.id]))
        return entity

    def save_many(self, entities: Iterable[TEntity]) -> list[TEntity]:
        saved = list(entities)
        ids = [entity.id for entity in saved]
        with self._lock:
            existing = db.run(self._fetch(ids))
            for entity in saved:
                if entity.id in existing:
                    entity.touch()
            db.run(self._write(saved, ids))
        return saved

    def delete(self, entity_id: str) -> None:
        if db.run(self._write([], [entity_id])) == 0:
            raise NotFoundError(f"Can not find entity {self.entity_type.__name__} with id '{entity_id}'.")

    def clear(self) -> None:
        db.run(self._write([]))
