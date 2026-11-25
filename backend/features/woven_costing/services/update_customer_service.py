"""UC-13 Sửa khách hàng."""

from backend.core.base import BaseService
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.customer_business import CustomerBusiness
from backend.features.woven_costing.dto.common_dto import MessageResponse
from backend.features.woven_costing.dto.master_dto import UpdateCustomerRequest
from backend.features.woven_costing.models.costsheet import EDITABLE_STATUSES
from backend.features.woven_costing.repositories.costsheet_repository import CostsheetRepository
from backend.features.woven_costing.repositories.master_repository import CustomerRepository


class UpdateCustomerService(BaseService[UpdateCustomerRequest, MessageResponse]):
    def __init__(
        self, repository: CustomerRepository | None = None, costsheets: CostsheetRepository | None = None
    ) -> None:
        self.repository = repository or CustomerRepository()
        self.costsheets = costsheets or CostsheetRepository()

    def execute(self, request: UpdateCustomerRequest) -> MessageResponse:
        AccessBusiness().ensure_use_case(self.current_user, "UC-13")
        business = CustomerBusiness()
        stored = self.repository.get_or_raise(request.id)
        customers = self.repository.list_all()
        name = business.clean_name(request.name)
        code = request.customer_code.strip().upper()
        business.ensure_name_free(name, customers, excluding_id=stored.id)
        business.ensure_code(code, customers, excluding_id=stored.id)
        self.repository.update(
            stored.model_copy(
                update={"name": name, "customer_code": code, "team": request.team, "active": request.active}
            )
        )
        renamed = []
        if name != stored.name:
            for sheet in self.costsheets.find_by(customer_name=stored.name):
                if sheet.status in EDITABLE_STATUSES:
                    renamed.append(sheet.model_copy(update={"customer_name": name}))
            self.costsheets.save_many(renamed)
        self.logger.info(
            "UC-13 customer %s -> %s (%s), %s draft costsheets renamed", stored.name, name, code, len(renamed)
        )
        return MessageResponse(message=f"Đã cập nhật khách hàng {name}.")
