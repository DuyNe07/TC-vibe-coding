"""UC-18 Thêm khách hàng mới (similar names first, then "Xác nhận tạo mới")."""

from backend.core.base import BaseService
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.customer_business import CustomerBusiness
from backend.features.woven_costing.dto.list_dto import AddCustomerRequest, AddCustomerResponse, CustomerOptionDTO
from backend.features.woven_costing.exceptions import WovenCostingError
from backend.features.woven_costing.models.enums import CustomerTeam
from backend.features.woven_costing.models.master import Customer
from backend.features.woven_costing.repositories.master_repository import CustomerRepository


class AddCustomerService(BaseService[AddCustomerRequest, AddCustomerResponse]):
    def __init__(self, repository: CustomerRepository | None = None) -> None:
        self.repository = repository or CustomerRepository()

    def execute(self, request: AddCustomerRequest) -> AddCustomerResponse:
        access = AccessBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-18")
        business = CustomerBusiness()
        name = business.clean_name(request.name)
        if len(name) < 2:
            raise WovenCostingError("Tên khách hàng cần ít nhất 2 ký tự.")
        customers = self.repository.list_all()
        business.ensure_name_free(name, customers)
        suggested = business.suggest_code(name, {c.customer_code for c in customers})
        similar = [CustomerOptionDTO(name=c.name, customer_code=c.customer_code, team=c.team.value)
                   for c in business.similar(name, customers)]  # fmt: skip
        if not request.confirm_new:
            self.logger.info("UC-18 %r: %s similar names, code %s suggested", name, len(similar), suggested)
            message = "Có tên tương tự, hãy kiểm tra trước khi tạo mới." if similar else "Chưa có khách hàng này."
            return AddCustomerResponse(customer_name=name, suggested_code=suggested, similar=similar, message=message)
        code = (request.customer_code or suggested).strip().upper()
        business.ensure_code(code, customers)
        team = access.team(user)  # "SO" (BR-51) is not a customer team: such customers are "Chung"
        known = {t.value for t in CustomerTeam}
        customer = Customer(customer_code=code, name=name, team=CustomerTeam(team) if team in known else CustomerTeam.CHUNG,
                            created_by=access.display_name(user))  # fmt: skip
        self.repository.add(customer)
        self.logger.info("UC-18 customer %s (%s) created", name, code)
        return AddCustomerResponse(created=True, customer_name=name, customer_code=code, suggested_code=suggested,
                                   similar=similar, message=f"Đã thêm khách hàng {name}.")  # fmt: skip
