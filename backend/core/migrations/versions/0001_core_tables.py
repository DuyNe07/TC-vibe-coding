"""Framework tables: accounts, groups, login sessions.

Revision 0001 (first of the framework chain). Idempotent: on a database where the app already created them on
first use (APP_DB_AUTO_CREATE), nothing changes.
"""

from backend.core import migration_ops as ops

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

TABLES = ("core__user", "core__user_group", "core__session")


def upgrade() -> None:
    for name in TABLES:
        ops.create_document_table(name)


def downgrade() -> None:
    for name in TABLES:
        ops.drop_table(name)
