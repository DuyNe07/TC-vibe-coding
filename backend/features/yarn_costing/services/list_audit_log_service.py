"""UC-02 Xem nhật ký thao tác."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.dashboard_business import local_date
from backend.features.yarn_costing.dto.audit_dto import AuditLogDTO, AuditLogListResponse, ListAuditLogRequest
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository


class ListAuditLogService(BaseService[ListAuditLogRequest, AuditLogListResponse]):
    def __init__(self, repository: AuditLogRepository | None = None) -> None:
        self.repository = repository or AuditLogRepository()

    def execute(self, request: ListAuditLogRequest) -> AuditLogListResponse:
        keyword = request.keyword.strip().casefold()
        in_range = [
            e
            for e in self.repository.newest_first()
            if not (request.date_from and local_date(e.at) < request.date_from)
            and not (request.date_to and local_date(e.at) > request.date_to)
        ]
        items = []
        for e in in_range:
            if request.username and e.username != request.username:
                continue
            if request.action and e.action != request.action:
                continue
            haystack = f"{e.username} {e.display_name} {e.action} {e.object_ref} {e.detail} {e.reason}".casefold()
            if keyword and keyword not in haystack:
                continue
            items.append(AuditLogDTO(**e.model_dump(exclude={"id", "created_at", "updated_at"})))
        self.logger.info("Audit log: %s of %s entries (keyword=%r)", len(items), len(in_range), request.keyword)
        return AuditLogListResponse(
            items=items,
            usernames=sorted({e.username for e in in_range if e.username}),
            actions=sorted({e.action for e in in_range}),
        )
