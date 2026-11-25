"""UC-36 Xem trước danh sách khách hàng (chưa lưu)."""

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
from backend.features.woven_costing.models.enums import CustomerImportResult
from backend.features.woven_costing.repositories.master_repository import CustomerRepository


class PreviewCustomerImportService(BaseService[CustomerImportRequest, CustomerImportResponse]):
    def __init__(self, repository: CustomerRepository | None = None) -> None:
        self.repository = repository or CustomerRepository()

    def execute(self, request: CustomerImportRequest) -> CustomerImportResponse:
        AccessBusiness().ensure_use_case(self.current_user, "UC-36")
        master = MasterBusiness()
        master.ensure_file(request.file)
        content = CustomerFileReaderBuilder(request.file).build()
        master.ensure_columns(request.file.filename, content.missing_columns)
        lines = CustomerBusiness().plan_import(content.rows, self.repository.list_all())
        added = sum(1 for line in lines if line.result == CustomerImportResult.ADDED)
        self.logger.info("UC-36 %s rows read, %s to add, %s duplicates", len(content.rows), added, len(lines) - added)
        return CustomerImportResponse(
            added=added,
            skipped=len(lines) - added,
            rows=[CustomerImportRowDTO(**line.model_dump()) for line in lines],
            message=f"Sẽ thêm {added} khách hàng, bỏ qua {len(lines) - added} tên trùng.",
        )
