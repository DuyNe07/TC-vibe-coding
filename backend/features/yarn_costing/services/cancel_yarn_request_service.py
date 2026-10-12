"""UC-17 Huỷ yêu cầu (mã không dùng lại)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import yarn_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.request_business import RequestBusiness
from backend.features.yarn_costing.dto.request_dto import CancelYarnRequestRequest, YarnResponse
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.models.enums import YarnStatus
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.user_group_repository import UserGroupRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class CancelYarnRequestService(BaseService[CancelYarnRequestRequest, YarnResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.access = AccessBusiness()
        self.requests = RequestBusiness()

    def execute(self, request: CancelYarnRequestRequest) -> YarnResponse:
        a = request.actor
        yarns = self.repository.list_all()
        yarn = next((y for y in yarns if y.yarn_code == request.yarn_code), None)
        if yarn is None:
            raise YarnNotFoundError(f"Không tìm thấy yêu cầu {request.yarn_code}.")
        group = self.access.verify(
            a.group_code,
            a.access_code,
            a.person_name,
            UserGroupRepository().list_all(),
            "UC-17",
            yarn.factory_code.value,
        )
        self.requests.ensure_pending(yarn)
        updated = yarn.model_copy(update={"status": YarnStatus.DA_HUY})
        self.repository.store(yarns, [updated])
        AuditLogRepository().add(
            self.access.audit_entry(group, a.person_name, "UC-17", yarn.yarn_code, "Chờ xưởng xem → Đã huỷ")
        )
        self.logger.info("Yarn request %s cancelled", yarn.yarn_code)
        return YarnResponse(message=f"Đã huỷ yêu cầu {yarn.yarn_code}.", yarn=yarn_dto(updated))
