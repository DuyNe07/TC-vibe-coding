"""Database migrations with Alembic: ``python scripts/migrate.py`` (run.ps1 and the Docker image run it on start).

One independent chain for the framework and one per feature, each with ITS OWN version table:

    framework                         backend/core/migrations/versions/     version table core__alembic_version
    feature <key> (only if it has     backend/features/<key>/migrations/    version table <developer>__<key>__alembic_version
    revisions)

Every developer's branch shares one database but contains only its own feature's revisions, so the chains never see
each other. Revisions change data with the helpers of ``backend.core.migration_ops`` (tables hold JSON documents).

Until the schema is frozen ("chốt"), ``APP_DB_AUTO_CREATE=true`` (default) also lets repositories create missing
tables on first use. Afterwards set it to false: then only revisions create or change tables.
"""

from dataclasses import dataclass
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from backend.core import db
from backend.core.base.base_repository import feature_developer

CORE = "core"
_ENV_DIR = Path(__file__).parent / "migrations"
_FEATURES = Path(__file__).resolve().parents[1] / "features"


@dataclass(frozen=True)
class Chain:
    name: str  # "core" or a feature key
    versions: Path
    version_table: str


def chains() -> list[Chain]:
    found = [Chain(CORE, _ENV_DIR / "versions", "core__alembic_version")]
    for folder in sorted(_FEATURES.glob("*/migrations")):
        if any(p.name != "__init__.py" for p in folder.glob("*.py")):
            key = folder.parent.name
            found.append(Chain(key, folder, f"{feature_developer(key)}__{key}__alembic_version"))
    return found


def chain(name: str) -> Chain:
    """The chain of the framework ("core") or of a feature (its folder is created if needed)."""
    if name == CORE:
        return chains()[0]
    folder = _FEATURES / name / "migrations"
    if not folder.parent.is_dir():
        raise ValueError(f"Unknown feature {name!r}")
    folder.mkdir(exist_ok=True)
    (folder / "__init__.py").touch()
    return Chain(name, folder, f"{feature_developer(name)}__{name}__alembic_version")


def config(item: Chain) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(_ENV_DIR))
    cfg.set_main_option("version_locations", str(item.versions))
    cfg.set_main_option("path_separator", "os")
    cfg.attributes["version_table"] = item.version_table
    return cfg


def upgrade() -> list[str]:
    """Apply every pending revision of every chain. Returns "<chain>: <old> -> <new>" for the chains that moved."""
    moved = []
    for item in chains():
        before = current(item)
        command.upgrade(config(item), "head")
        after = current(item)
        if after != before:
            moved.append(f"{item.name}: {before or 'trống'} -> {after}")
    return moved


def pending() -> dict[str, str]:
    """Chains not at their latest revision: {chain: "<current> -> <head>"}."""
    out = {}
    for item in chains():
        head = ScriptDirectory.from_config(config(item)).get_current_head()
        now = current(item)
        if now != head:
            out[item.name] = f"{now or 'trống'} -> {head}"
    return out


def current(item: Chain) -> str | None:
    async def read() -> str | None:
        async with db.engine().connect() as connection:
            return await connection.run_sync(
                lambda sync: MigrationContext.configure(
                    sync, opts={"version_table": item.version_table}
                ).get_current_revision()
            )

    return db.run(read())


def new_revision(name: str, message: str) -> Path:
    """Create the next empty revision file (0001, 0002...) of a chain and return its path."""
    item = chain(name)
    number = 1 + max((int(p.name[:4]) for p in item.versions.glob("[0-9][0-9][0-9][0-9]_*.py")), default=0)
    script = command.revision(config(item), message=message, rev_id=f"{number:04d}")
    return Path(script.path)  # type: ignore[union-attr]
