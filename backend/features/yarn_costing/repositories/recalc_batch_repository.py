"""Tables xuan2894__yarn_costing__recalc_batch and xuan2894__yarn_costing__audit_log."""

from typing import Any

from backend.features.yarn_costing.models.access import ROLE_LABELS
from backend.features.yarn_costing.models.audit_log import AuditLog
from backend.features.yarn_costing.models.recalc_batch import RecalcBatch
from backend.features.yarn_costing.repositories.yarn_sql_repository import YarnSqlRepository


class RecalcBatchRepository(YarnSqlRepository[RecalcBatch]):
    legacy_file = "recalc_batches.json"

    def newest_first(self) -> list[RecalcBatch]:
        return sorted(self.list_all(), key=lambda b: b.run_at, reverse=True)

    def get_by_code(self, code: str) -> RecalcBatch | None:
        return self.find_one(lambda b: b.batch_code == code)


class AuditLogRepository(YarnSqlRepository[AuditLog]):
    legacy_file = "audit_log.json"

    def _convert(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Rows of the previous app (``group_code`` + ``person_name``) -> ``username`` + ``display_name``."""
        converted = []
        for row in raw:
            if "person_name" not in row and "group_code" not in row:
                converted.append(row)
                continue
            rest = {k: v for k, v in row.items() if k not in ("group_code", "person_name")}
            group = str(row.get("group_code") or "")
            group_label = ROLE_LABELS.get(group, group)  # StrEnum keys equal their text
            display = " - ".join(x for x in (group_label, str(row.get("person_name") or "")) if x)
            converted.append({**rest, "username": "", "display_name": display})
        return converted

    def newest_first(self) -> list[AuditLog]:
        return sorted(self.list_all(), key=lambda e: e.at, reverse=True)
