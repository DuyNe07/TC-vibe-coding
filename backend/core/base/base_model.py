"""Base classes for data models (``models/`` folder of every feature)."""

from datetime import UTC, datetime
from typing import Any, Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class BaseSchema(BaseModel):
    """Root of every pydantic class in the project. Features never inherit it directly."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)


class BaseEntity(BaseSchema):
    """An object with identity (``id``) and a lifecycle, persisted by a repository.

    Put only fields and *self-contained* derived properties here (e.g. ``total = qty * price``).
    Rules involving several objects, stored data or policies belong in ``business/``.
    """

    id: str = Field(default_factory=lambda: uuid4().hex)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    # Soft delete (SUPREME-RULES.md): a repository's delete() only sets these; reads skip flagged rows.
    # exclude=True keeps them out of model_dump(), so ``XxxDTO(**entity.model_dump())`` keeps working;
    # repositories store them through ``to_document()``.
    is_deleted: bool = Field(default=False, exclude=True)
    deleted_at: datetime | None = Field(default=None, exclude=True)
    deleted_by: str | None = Field(default=None, exclude=True)

    def touch(self) -> None:
        """Mark the entity as modified. Repositories call it on update."""
        self.updated_at = utc_now()

    def to_document(self) -> dict[str, Any]:
        """JSON document stored by repositories. The delete flag is written only on deleted rows: a live row keeps
        exactly the format older app versions on the shared database read (no unknown keys)."""
        document = self.model_dump(mode="json")
        if self.is_deleted:
            document |= {
                "is_deleted": True,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
                "deleted_by": self.deleted_by,
            }
        return document

    def marked_deleted(self, by: str | None) -> Self:
        """A copy flagged as deleted (the stored row stays; ``restore`` clears the flag)."""
        return self.model_copy(update={"is_deleted": True, "deleted_at": utc_now(), "deleted_by": by})

    def restored(self) -> Self:
        """A copy with the delete flag cleared."""
        return self.model_copy(update={"is_deleted": False, "deleted_at": None, "deleted_by": None})


class BaseValueObject(BaseSchema):
    """Immutable object defined only by its values (no id), e.g. an address or a parsed Excel row."""

    model_config = ConfigDict(frozen=True)
