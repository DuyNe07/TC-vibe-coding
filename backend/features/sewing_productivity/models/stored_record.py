"""Common base of what this feature stores: a deterministic id and a comparison of the stored values."""

import hashlib
from typing import Self

from backend.core.base import BaseEntity

ID_LENGTH = 32
ID_SEPARATOR = "\x1f"
_BOOKKEEPING_FIELDS = frozenset(BaseEntity.model_fields)


def stable_id(*parts: object) -> str:
    """Same parts give the same id, so saving a row again replaces it instead of adding one."""
    text = ID_SEPARATOR.join("" if part is None else str(part) for part in parts)
    return hashlib.sha1(text.encode("utf-8"), usedforsecurity=False).hexdigest()[:ID_LENGTH]


class StoredRecord(BaseEntity):
    """An entity whose business values can be compared with another version of the same row."""

    def same_content(self, other: Self) -> bool:
        """True when every business field is equal (id, timestamps and the delete flag are not compared)."""
        names = (name for name in type(self).model_fields if name not in _BOOKKEEPING_FIELDS)
        return all(getattr(self, name) == getattr(other, name) for name in names)
