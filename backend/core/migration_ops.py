"""Helpers for migration revisions (``backend/core/migrations``, ``backend/features/<key>/migrations``).

Every table is ``id`` + ``data`` (one JSON document per entity), so most changes are document changes::

    from backend.core import migration_ops as ops

    def upgrade() -> None:
        audit = ops.feature_table("yarn_costing", "audit_log")
        ops.update_documents(audit, lambda doc: {**doc, "username": ""})   # add / rename / drop fields
        ops.drop_table(ops.feature_table("yarn_costing", "user_group"))   # table no longer used
"""

from collections.abc import Callable
from typing import Any

import sqlalchemy as sa
from alembic import op

from backend.core.base.base_repository import feature_developer
from backend.core.db import document_table


def feature_table(feature_key: str, name: str) -> str:
    """Full table name of a feature's repository: ``<developer>__<feature_key>__<name>``."""
    return f"{feature_developer(feature_key)}__{feature_key}__{name}"


def has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def create_document_table(name: str) -> None:
    """Create a JSON-document table if it does not exist yet."""
    document_table(name).create(op.get_bind(), checkfirst=True)


def drop_table(name: str) -> None:
    if has_table(name):
        op.drop_table(name)


def rename_table(old: str, new: str) -> None:
    if has_table(old) and not has_table(new):
        op.rename_table(old, new)


def update_documents(name: str, change: Callable[[dict[str, Any]], dict[str, Any] | None]) -> int:
    """Apply ``change`` to every document of a table: return the new document, or None to delete the row.
    Returns how many rows changed. Missing table: nothing to do."""
    if not has_table(name):
        return 0
    table = document_table(name)
    bind = op.get_bind()
    changed = 0
    for row_id, data in bind.execute(sa.select(table.c.id, table.c.data)).all():
        new = change(dict(data))
        if new is None:
            bind.execute(sa.delete(table).where(table.c.id == row_id))
        elif new != data:
            bind.execute(sa.update(table).where(table.c.id == row_id).values(data=new))
        else:
            continue
        changed += 1
    return changed
