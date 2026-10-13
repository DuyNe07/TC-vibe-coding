"""UC-18 Từ chối yêu cầu (BR-08)."""

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.dto_builders import yarn_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.request_business import RejectReasonRule
from backend.features.yarn_costing.dto.request_dto import RejectYarnRequestRequest, YarnResponse
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.models.enums import YarnStatus
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class RejectYarnRequestService(BaseService[RejectYarnRequestRequest, YarnResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.access = AccessBusiness()
        self.master = MasterBusiness()

    def execute(self, request: RejectYarnRequestRequest) -> YarnResponse:
        yarns = self.repository.list_all()
        yarn = next((y for y in yarns if y.yarn_code == request.yarn_code), None)
        if yarn is None:
            raise YarnNotFoundError(f"Không tìm thấy yêu cầu {request.yarn_code}.")
        self.access.ensure_allowed(self.current_user, "UC-18", yarn.factory_code.value)
        RejectReasonRule().check(request.reason)
        self.master.require(
            yarn.status == YarnStatus.CHO_XUONG_XEM, f"Yêu cầu {yarn.yarn_code} không còn ở trạng thái 'Chờ xưởng xem'."
        )
        label = self.access.user_label(self.current_user)
        updated = yarn.model_copy(
            update={
                "status": YarnStatus.TU_CHOI,
                "reject_reason": request.reason.strip(),
                "handled_by": label,
                "handled_at": utc_now(),
            }
        )
        self.repository.store(yarns, [updated])
        AuditLogRepository().add(
            self.access.audit_entry(
                self.current_user, "UC-18", yarn.yarn_code, "Chờ xưởng xem → Từ chối", request.reason
            )
        )
        self.logger.info("Yarn request %s rejected", yarn.yarn_code)
        return YarnResponse(message=f"Đã từ chối yêu cầu {yarn.yarn_code}.", yarn=yarn_dto(updated))
