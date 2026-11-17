"""UC-51 (xem): tên theo khách của một sợi (mã gốc). Không lưu gì."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import customer_name_dto
from backend.features.yarn_costing.business.customer_name_business import CustomerNameBusiness
from backend.features.yarn_costing.dto.sales_dto import CustomerNameListResponse, ListCustomerNamesRequest
from backend.features.yarn_costing.repositories.customer_name_repository import CustomerYarnNameRepository


class ListCustomerNamesService(BaseService[ListCustomerNamesRequest, CustomerNameListResponse]):
    def __init__(self, repository: CustomerYarnNameRepository | None = None) -> None:
        self.repository = repository or CustomerYarnNameRepository()

    def execute(self, request: ListCustomerNamesRequest) -> CustomerNameListResponse:
        if not request.base_code:
            every = sorted(self.repository.list_all(), key=lambda a: (a.customer_name.casefold(), a.base_code))
            return CustomerNameListResponse(items=[customer_name_dto(a) for a in every])
        items = CustomerNameBusiness().by_base(self.repository.find_by(base_code=request.base_code))
        return CustomerNameListResponse(items=[customer_name_dto(a) for a in items.get(request.base_code, [])])
