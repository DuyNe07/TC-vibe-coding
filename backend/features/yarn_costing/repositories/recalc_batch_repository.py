"""Stored in data/yarn_costing/recalc_batches.json and audit_log.json."""

from backend.features.yarn_costing.models.audit_log import AuditLog
from backend.features.yarn_costing.models.recalc_batch import RecalcBatch
from backend.features.yarn_costing.repositories.safe_json_repository import SafeJsonRepository


class RecalcBatchRepository(SafeJsonRepository[RecalcBatch]):
    storage_file = "recalc_batches.json"

    def newest_first(self) -> list[RecalcBatch]:
        return sorted(self.list_all(), key=lambda b: b.run_at, reverse=True)

    def get_by_code(self, code: str) -> RecalcBatch | None:
        return self.find_one(lambda b: b.batch_code == code)


class AuditLogRepository(SafeJsonRepository[AuditLog]):
    storage_file = "audit_log.json"

    def newest_first(self) -> list[AuditLog]:
        return sorted(self.list_all(), key=lambda e: e.at, reverse=True)
