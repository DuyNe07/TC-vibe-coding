"""Database storage of the feature, importing the data of the previous app once (BR-61, section 5.6).

Each repository is one table ``yarn_costing__<name>``. While its table is empty, the first read imports the JSON file
the previous app kept in ``data/yarn_costing/<legacy_file>`` (old formats converted by ``_convert``); the file is then
renamed ``<name>.imported`` so it is never imported twice. No file -> the seed rows (``_seed``), if any.
A broken file raises ``DataFileError`` naming it so Phòng SO can copy it again; other tables keep working.
"""

import json
from typing import Any, ClassVar, TypeVar

from backend.core.base import BaseEntity, SqlRepository
from backend.core.config import get_settings
from backend.core.logger import get_logger
from backend.features.yarn_costing.constants import DATA_FILE_UNREADABLE_MESSAGE
from backend.features.yarn_costing.exceptions import DataFileError

TEntity = TypeVar("TEntity", bound=BaseEntity)
FEATURE_KEY = "yarn_costing"


class YarnSqlRepository(SqlRepository[TEntity]):
    legacy_file: ClassVar[str] = ""  # file name used by the previous app, e.g. "yarns.json"

    # ponytail: an emptied table is re-seeded on next read; two first reads at the same time may seed twice
    def _load(self) -> dict[str, TEntity]:
        items = super()._load()
        if items:
            return items
        first = self._import_legacy_file()
        if not first and (first := self._seed()):
            self.save_many(first)
        return {item.id: item for item in first}

    def store(self, loaded: list[TEntity], changed: list[TEntity]) -> None:
        """Save the entities changed by a use case (``loaded`` = the list read earlier, kept for call-site clarity)."""
        if changed:
            self.save_many(changed)

    # ---- hooks ----
    def _convert(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert rows stored by the previous version to the current model (default: unchanged)."""
        return raw

    def _seed(self) -> list[TEntity]:
        """Rows created when there is no data at all (default: none)."""
        return []

    def _import_legacy_file(self) -> list[TEntity]:
        if not self.legacy_file:
            return []
        path = get_settings().data_dir / FEATURE_KEY / self.legacy_file
        if not path.exists():
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8") or "[]")
            items = [self.entity_type.model_validate(item) for item in self._convert(raw)]
        except (ValueError, TypeError, KeyError, AttributeError, UnicodeDecodeError) as exc:
            raise DataFileError(DATA_FILE_UNREADABLE_MESSAGE.format(file_name=self.legacy_file)) from exc
        self.save_many(items)  # type: ignore[arg-type]
        path.replace(path.with_name(path.name + ".imported"))
        get_logger(__name__).info("Imported %s rows of %s into the database", len(items), path.name)
        return items  # type: ignore[return-value]
