"""Audit log by logged-in account; drop the old user-group table (the "người thao tác" block is gone).

Revision 0001, created 2026-10-13.
- xuan2894__yarn_costing__audit_log: group_code + person_name -> username "" + display_name "<Nhóm> - <Tên>"
  (same rule as AuditLogRepository._convert for legacy JSON rows).
- xuan2894__yarn_costing__user_group: no longer used (accounts and roles are managed on /admin).
"""

from backend.core import migration_ops as ops

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

GROUP_LABELS = {"SALES": "Sales", "XS1": "Xưởng S1", "XS4": "Xưởng S4", "KT": "Kế toán", "SO": "Phòng SO"}


def _by_account(doc: dict) -> dict:
    if "username" in doc:
        return doc  # already converted
    group = doc.pop("group_code", "") or ""
    person = doc.pop("person_name", "") or ""
    label = " - ".join(x for x in (GROUP_LABELS.get(group, group), person) if x)
    return {**doc, "username": "", "display_name": label}


def upgrade() -> None:
    ops.update_documents(ops.feature_table("yarn_costing", "audit_log"), _by_account)
    ops.drop_table(ops.feature_table("yarn_costing", "user_group"))


def downgrade() -> None:
    raise NotImplementedError("The old group / access-code data is not kept: restore a database backup instead")
