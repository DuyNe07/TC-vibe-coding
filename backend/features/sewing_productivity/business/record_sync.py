"""Which rows must be written so that a table matches what the user just saved (BR-07, catalogs). Pure."""

from collections.abc import Callable
from typing import TypeVar

from backend.features.sewing_productivity.models.stored_record import StoredRecord

TRecord = TypeVar("TRecord", bound=StoredRecord)


def rows_to_write(
    stored: list[TRecord],
    deleted: list[TRecord],
    incoming: list[TRecord],
    in_scope: Callable[[TRecord], bool],
    deleted_by: str | None,
) -> list[TRecord]:
    """New or changed rows, plus a flagged copy of each stored row in scope that is no longer present.

    An unchanged row is not written at all: saving the same content twice writes nothing."""
    active = {row.id: row for row in stored}
    flagged = {row.id: row for row in deleted}
    incoming_ids = {row.id for row in incoming}
    writes: list[TRecord] = []
    for row in incoming:
        previous = active.get(row.id) or flagged.get(row.id)
        if row.id in active and previous.same_content(row):
            continue
        writes.append(row if previous is None else row.model_copy(update={"created_at": previous.created_at}))
    writes.extend(row.marked_deleted(deleted_by) for row in stored if row.id not in incoming_ids and in_scope(row))
    return writes
