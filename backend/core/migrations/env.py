"""Alembic environment shared by every chain (``backend/core/migrate.py`` passes the chain's version table).

Runs on the app's own database loop and engine (``backend.core.db``), so it uses the same URL as the app:
APP_DATABASE_URL, else POSTGRES_* from .env, else the local SQLite file.
"""

from alembic import context

from backend.core import db


def _run(connection) -> None:  # type: ignore[no-untyped-def]
    context.configure(
        connection=connection,
        version_table=context.config.attributes["version_table"],
        render_as_batch=True,  # SQLite can alter tables too
    )
    with context.begin_transaction():
        context.run_migrations()


async def _main() -> None:
    async with db.engine().connect() as connection:
        await connection.run_sync(_run)
        await connection.commit()


db.run(_main())
