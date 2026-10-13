"""Alembic migrations (backend/core/migrate.py) on the throw-away SQLite database of each test."""

import sqlalchemy as sa
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext

from backend.core import db, migrate
from backend.core import migration_ops as ops


def _tables() -> set[str]:
    async def names() -> set[str]:
        async with db.engine().connect() as connection:
            return set(await connection.run_sync(lambda sync: sa.inspect(sync).get_table_names()))

    return db.run(names())


def test_upgrade_applies_every_chain_once() -> None:
    assert migrate.chains()[0].name == "core"
    moved = migrate.upgrade()
    assert "core: trống -> 0001" in moved
    assert {"core__user", "core__user_group", "core__session", "core__alembic_version"} <= _tables()
    assert migrate.upgrade() == [] and migrate.pending() == {}, "a second run changes nothing"


def test_update_documents_changes_and_deletes_json_rows() -> None:
    name = "core__migration_probe"

    def body(sync: sa.Connection) -> None:
        with Operations.context(MigrationContext.configure(sync)):
            ops.create_document_table(name)
            table = db.document_table(name)
            sync.execute(sa.insert(table), [{"id": "1", "data": {"a": 1}}, {"id": "2", "data": {"a": 2, "old": True}}])
            assert ops.update_documents(name, lambda d: None if d.get("old") else {**d, "b": d["a"] * 10}) == 2
            assert [tuple(r) for r in sync.execute(sa.select(table.c.id, table.c.data))] == [("1", {"a": 1, "b": 10})]
            ops.drop_table(name)
            assert not ops.has_table(name)

    async def run() -> None:
        async with db.engine().begin() as connection:
            await connection.run_sync(body)

    db.run(run())
