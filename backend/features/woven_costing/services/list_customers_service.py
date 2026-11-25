"""UC-35 Tra cứu khách hàng."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.dto_builders import MasterRowsBuilder
from backend.features.woven_costing.dto.master_dto import CustomerListResponse, ListCustomersRequest
from backend.features.woven_costing.repositories.master_repository import CustomerRepository
from backend.shared.utils import strip_accents


class ListCustomersService(BaseService[ListCustomersRequest, CustomerListResponse]):
    def __init__(self, repository: CustomerRepository | None = None) -> None:
        self.repository = repository or CustomerRepository()

    def execute(self, request: ListCustomersRequest) -> CustomerListResponse:
        keyword = strip_accents(request.keyword.strip()).casefold()
        customers = [
            c
            for c in self.repository.sorted_by_name()
            if not keyword or keyword in strip_accents(f"{c.customer_code} {c.name}").casefold()
        ]
        self.logger.info("UC-35 keyword=%r -> %s customers", request.keyword, len(customers))
        return CustomerListResponse(rows=MasterRowsBuilder().customers(customers))
