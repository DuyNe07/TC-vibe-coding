"""Tables xuan2894__yarn_costing__recalc_batch and xuan2894__yarn_costing__audit_log."""

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

    def newest_first(self) -> list[AuditLog]:
        return sorted(self.list_all(), key=lambda e: e.at, reverse=True)
