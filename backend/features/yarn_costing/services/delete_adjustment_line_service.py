"""UC-26 Xoá dòng chiết khấu / phụ phí (BR-35; số thứ tự không dùng lại)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.price_line_business import PriceLineBusiness
from backend.features.yarn_costing.dto.common_dto import SaveCountResponse
from backend.features.yarn_costing.dto.price_dto import DeleteAdjustmentLineRequest
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.user_group_repository import UserGroupRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class DeleteAdjustmentLineService(BaseService[DeleteAdjustmentLineRequest, SaveCountResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.access = AccessBusiness()
        self.lines = PriceLineBusiness()

    def execute(self, request: DeleteAdjustmentLineRequest) -> SaveCountResponse:
        a = request.actor
        yarns = self.repository.list_all()
        yarn = next((y for y in yarns if y.line(request.line_code) is not None), None)
        if yarn is None:
            raise YarnNotFoundError(f"Không tìm thấy dòng {request.line_code}.")
        group = self.access.verify(
            a.group_code,
            a.access_code,
            a.person_name,
            UserGroupRepository().list_all(),
            "UC-26",
            yarn.factory_code.value,
        )
        line = yarn.line(request.line_code)
        self.lines.ensure_deletable(line)  # type: ignore[arg-type]
        updated = yarn.model_copy(update={"lines": [x for x in yarn.lines if x.line_code != request.line_code]})
        self.repository.store(yarns, [updated])
        AuditLogRepository().add(
            self.access.audit_entry(group, a.person_name, "UC-26", request.line_code, "Đã xoá dòng")
        )
        self.logger.info("Adjustment line %s deleted", request.line_code)
        return SaveCountResponse(message=f"Đã xoá dòng {request.line_code}.", saved_count=1)
