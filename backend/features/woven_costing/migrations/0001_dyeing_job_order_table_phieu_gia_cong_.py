"""Dyeing job order table ("phiếu gia công nhuộm", 4.21-4.23, extension 2026-11-25).

Revision 0001, created 2026-11-25.
- xuan2894__woven_costing__dyeing_job: new table, one JSON document per job order (lines and result inside).
Tables hold one JSON document per row: change them with ``from backend.core import migration_ops as ops``. Never
import feature models here: they change later, and a revision must keep working on the data as it was.
"""

from backend.core import migration_ops as ops

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    ops.create_document_table(ops.feature_table("woven_costing", "dyeing_job"))


def downgrade() -> None:
    raise NotImplementedError("Stored job orders are never dropped: restore a database backup instead")
