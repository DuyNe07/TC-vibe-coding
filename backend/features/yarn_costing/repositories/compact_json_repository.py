"""JSON storage without indentation, for the large files (yarns, price history, legacy prices)."""

import json
import os
from typing import TypeVar

from backend.core.base import BaseEntity
from backend.features.yarn_costing.repositories.safe_json_repository import SafeJsonRepository

TEntity = TypeVar("TEntity", bound=BaseEntity)


class CompactJsonRepository(SafeJsonRepository[TEntity]):
    """Same API as ``JsonFileRepository``; the file is written compactly (several thousand records)."""

    def store(self, loaded: list[TEntity], changed: list[TEntity]) -> None:
        """Save ``changed`` on top of ``loaded`` (the full list read earlier in the same use case): one write, no re-read."""
        if not changed:
            return
        with self._lock:
            items = {item.id: item for item in loaded}
            for entity in changed:
                entity.touch()
                items[entity.id] = entity
            self._save(items)

    def _save(self, items: dict[str, TEntity]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [item.model_dump(mode="json", exclude_defaults=True) for item in items.values()]
        tmp = self.file_path.with_suffix(self.file_path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        os.replace(tmp, self.file_path)
