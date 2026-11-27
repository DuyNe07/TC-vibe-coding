"""Load every table of <project>/data/app.db (SQLite) into the dev PostgreSQL database (POSTGRES_* from <project>/.env).
Logs in with DEV_POSTGRES_USER / DEV_POSTGRES_PASSWORD from .env (fallback: POSTGRES_USER / POSTGRES_PASSWORD).

Nothing is destroyed: missing tables are created, rows are INSERTed with ON CONFLICT (id) DO NOTHING, so rows that
already exist on dev (same id) are kept as they are. app.db is only read.

    python sqlite_to_dev.py                                  project = this folder, dev = POSTGRES_DB-dev
    DEV_DB=tc-vibe-coding-dev python sqlite_to_dev.py
    SQLITE=C:/other/app.db    python sqlite_to_dev.py

Run it with a Python that has the project's requirements (asyncpg, pydantic-settings).
"""

import asyncio
import os
import sqlite3
import sys
from pathlib import Path

import asyncpg
from dotenv import dotenv_values  # comes with pydantic-settings

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))
from backend.core.config import get_settings  # noqa: E402  (reads PROJECT/.env)


async def main() -> None:
    s = get_settings()
    sqlite_path = Path(os.environ.get("SQLITE", s.data_dir / "app.db"))
    is_dev = s.postgres_db.endswith("-dev")  # .env may already point at the dev database
    dev_db = os.environ.get("DEV_DB") or (s.postgres_db if is_dev else f"{s.postgres_db}-dev")
    if not sqlite_path.is_file() or not s.postgres_ip or not s.postgres_db:
        sys.exit(f"Need {sqlite_path} and POSTGRES_IP / POSTGRES_DB in {PROJECT / '.env'}.")
    if dev_db == s.postgres_db and not is_dev:
        sys.exit(f"Dev database equals POSTGRES_DB ({dev_db}): refusing to write into prod.")

    src = sqlite3.connect(f"file:{sqlite_path.as_posix()}?mode=ro", uri=True)
    tables = [
        name
        for (name,) in src.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        # accounts / groups / sessions stay per database: a local u-admin with another id duplicates the username
        # on dev, and login then checks whichever row comes first
        if not name.startswith("core__")
        # only the app's document tables (id + data); alembic version tables etc. stay with migrations
        if [c[1] for c in src.execute(f'PRAGMA table_info("{name}")')] == ["id", "data"]
    ]
    env = dotenv_values(PROJECT / ".env")
    user = env.get("DEV_POSTGRES_USER") or s.postgres_user
    password = env.get("DEV_POSTGRES_PASSWORD") or s.postgres_password
    print(f"{sqlite_path}  ->  {dev_db} on {s.postgres_ip}:{s.postgres_port} as {user}  ({len(tables)} tables)")
    if input("Type yes to continue: ").strip() != "yes":
        sys.exit(1)

    dst = await asyncpg.connect(
        host=s.postgres_ip, port=s.postgres_port, user=user, password=password, database=dev_db
    )
    skipped = []
    try:
        for name in tables:
            rows = src.execute(f'SELECT id, data FROM "{name}"').fetchall()
            try:
                async with dst.transaction():  # one table per transaction: a failure rolls back only that table
                    await dst.execute(
                        f'CREATE TABLE IF NOT EXISTS "{name}" (id VARCHAR(64) PRIMARY KEY, data JSONB NOT NULL)'
                    )
                    before = await dst.fetchval(f'SELECT count(*) FROM "{name}"')
                    await dst.executemany(
                        f'INSERT INTO "{name}" (id, data) VALUES ($1, $2::jsonb) ON CONFLICT (id) DO NOTHING', rows
                    )
                    added = await dst.fetchval(f'SELECT count(*) FROM "{name}"') - before
            except asyncpg.PostgresError as error:
                skipped.append(name)
                print(f"  {name}: SKIPPED ({len(rows)} rows not copied) - {error}")
                continue
            print(f"  {name}: {len(rows)} rows, {added} new, {len(rows) - added} already on dev (kept)")
        if skipped:
            print(f"\n{len(skipped)} table(s) skipped, ask the table owner to GRANT SELECT, INSERT to "
                  f"{user} on: {', '.join(skipped)}")  # fmt: skip
    finally:
        await dst.close()
        src.close()


if __name__ == "__main__":
    asyncio.run(main())
