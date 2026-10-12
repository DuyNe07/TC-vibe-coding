"""JSON storage that reports an unreadable data file with a clear message (BR-61, section 5.6).

Data files may be copied by hand from the previous app; a missing file is simply empty, a broken one raises
``DataFileError`` naming the file so Phòng SO can copy it again. Other files keep working.
"""

from typing import TypeVar

from backend.core.base import BaseEntity, JsonFileRepository
from backend.features.yarn_costing.constants import DATA_FILE_UNREADABLE_MESSAGE
from backend.features.yarn_costing.exceptions import DataFileError

TEntity = TypeVar("TEntity", bound=BaseEntity)


class SafeJsonRepository(JsonFileRepository[TEntity]):
    """Subclasses override ``_read`` (not ``_load``) to convert stored data."""

    def _load(self) -> dict[str, TEntity]:
        try:
            return self._read()
        except (ValueError, TypeError, KeyError, AttributeError, UnicodeDecodeError) as exc:
            raise DataFileError(DATA_FILE_UNREADABLE_MESSAGE.format(file_name=self.file_path.name)) from exc

    def _read(self) -> dict[str, TEntity]:
        return super()._load()
