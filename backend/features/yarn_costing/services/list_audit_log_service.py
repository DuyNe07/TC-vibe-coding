"""UC-02 Xem nhật ký thay đổi."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.dashboard_business import local_date
from backend.features.yarn_costing.dto.audit_dto import AuditLogDTO, AuditLogListResponse, ListAuditLogRequest
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository


class ListAuditLogService(BaseService[ListAuditLogRequest, AuditLogListResponse]):
    def __init__(self, repository: AuditLogRepository | None = None) -> None:
        self.repository = repository or AuditLogRepository()

    def execute(self, request: ListAuditLogRequest) -> AuditLogListResponse:
        keyword = request.keyword.strip().casefold()
        items = []
        for e in self.repository.newest_first():
            day = local_date(e.at)
            if request.date_from and day < request.date_from or request.date_to and day > request.date_to:
                continue
            if request.group_code and e.group_code != request.group_code:
                continue
            if keyword and keyword not in f"{e.person_name} {e.action} {e.object_ref} {e.detail} {e.reason}".casefold():
                continue
            items.append(AuditLogDTO(**e.model_dump(exclude={"id", "created_at", "updated_at"})))
        self.logger.info("Audit log: %s entries (keyword=%r)", len(items), request.keyword)
        return AuditLogListResponse(items=items)
