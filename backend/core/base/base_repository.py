"""Base classes for persistence (``repositories/`` folder).

``BaseRepository`` implements the CRUD API once (template method); storage subclasses only
implement ``_load`` / ``_save``. Features subclass ``JsonFileRepository[MyEntity]``.
"""

import json
import os
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import ClassVar, Generic, TypeVar

from backend.core.base._generics import generic_args
from backend.core.base.base_model import BaseEntity
from backend.core.config import get_settings
from backend.core.exceptions import ConfigurationError, ConflictError, NotFoundError
from backend.core.naming import feature_key_from_module

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
                raise NotFoundError(f"Không tìm thấy {self.entity_type.__name__} với id '{entity_id}'.")
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
