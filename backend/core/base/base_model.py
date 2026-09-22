"""Base classes for data models (``models/`` folder of every feature)."""

from datetime import UTC, datetime
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

    def touch(self) -> None:
        """Mark the entity as modified. Repositories call it on update."""
        self.updated_at = utc_now()


class BaseValueObject(BaseSchema):
    """Immutable object defined only by its values (no id), e.g. an address or a parsed Excel row."""

    model_config = ConfigDict(frozen=True)
