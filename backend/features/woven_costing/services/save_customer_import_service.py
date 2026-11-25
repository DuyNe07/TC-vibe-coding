"""UC-12 Tải danh sách khách hàng ban đầu."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.file_readers import CustomerFileReaderBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.customer_business import CustomerBusiness
from backend.features.woven_costing.business.master_business import MasterBusiness
from backend.features.woven_costing.dto.master_dto import (
    CustomerImportRequest,
    CustomerImportResponse,
    CustomerImportRowDTO,
)
from backend.features.woven_costing.models.enums import CustomerImportResult, CustomerTeam
from backend.features.woven_costing.models.master import Customer
from backend.features.woven_costing.repositories.master_repository import CustomerRepository


class SaveCustomerImportService(BaseService[CustomerImportRequest, CustomerImportResponse]):
    def __init__(self, repository: CustomerRepository | None = None) -> None:
        self.repository = repository or CustomerRepository()

    def execute(self, request: CustomerImportRequest) -> CustomerImportResponse:
        access = AccessBusiness()
        access.ensure_use_case(self.current_user, "UC-12")
        master = MasterBusiness()
        master.ensure_file(request.file)
        content = CustomerFileReaderBuilder(request.file).build()
        master.ensure_columns(request.file.filename, content.missing_columns)
        lines = CustomerBusiness().plan_import(content.rows, self.repository.list_all())
        user = access.display_name(self.current_user)
        new = [
            Customer(customer_code=line.customer_code, name=line.name, team=CustomerTeam(line.team), created_by=user)
            for line in lines
            if line.result == CustomerImportResult.ADDED
        ]
        self.repository.save_many(new)
        skipped = len(lines) - len(new)
        self.logger.info("UC-12 added %s customers, skipped %s duplicates", len(new), skipped)
        return CustomerImportResponse(
            added=len(new),
            skipped=skipped,
            rows=[CustomerImportRowDTO(**line.model_dump()) for line in lines],
            message=f"Đã thêm {len(new)} khách hàng, bỏ qua {skipped} tên trùng.",
        )
