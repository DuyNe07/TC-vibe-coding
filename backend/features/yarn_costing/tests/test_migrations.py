"""Revision 0001 (migrations/0001_audit_log_by_account.py) on rows written by the previous version of the app."""

import sqlalchemy as sa

from backend.core import db, migrate
from backend.core.migration_ops import feature_table
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository


def test_0001_moves_the_audit_log_to_accounts_and_drops_the_group_table() -> None:
    audit, groups = feature_table("yarn_costing", "audit_log"), feature_table("yarn_costing", "user_group")
    old = {"id": "a1", "created_at": "2026-10-01T08:00:00+00:00", "updated_at": "2026-10-01T08:00:00+00:00",
           "at": "2026-10-01T08:00:00+00:00", "group_code": "SO", "person_name": "Nguyễn A", "action": "Lưu định mức",
           "object_ref": "S1", "detail": "", "reason": ""}  # fmt: skip

    async def seed() -> None:
        async with db.engine().begin() as connection:
            for name in (audit, groups):
                await connection.run_sync(db.document_table(name).create, checkfirst=True)
            await connection.execute(sa.insert(db.document_table(audit)), [{"id": "a1", "data": old}])

    async def tables() -> set[str]:
        async with db.engine().connect() as connection:
            return set(await connection.run_sync(lambda sync: sa.inspect(sync).get_table_names()))

    db.run(seed())
    assert "yarn_costing: trống -> 0001" in migrate.upgrade()
    entry = AuditLogRepository().get("a1")
    assert entry is not None and (entry.username, entry.display_name) == ("", "Phòng SO - Nguyễn A")
    assert groups not in db.run(tables())
    assert migrate.upgrade() == [], "already applied: nothing to do"
