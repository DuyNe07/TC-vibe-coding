"""UC-28 Xuất danh sách costsheet ra Excel."""

from datetime import date

from backend.core.base import BaseService, FileDownloadDTO
from backend.features.woven_costing.builders.document_builders import CostsheetExportBuilder
from backend.features.woven_costing.builders.dto_builders import CostsheetRowsBuilder
from backend.features.woven_costing.business.list_business import ListBusiness
from backend.features.woven_costing.dto.list_dto import ListCostsheetsRequest
from backend.features.woven_costing.models.list_filter import CostsheetFilter
from backend.features.woven_costing.repositories.costsheet_repository import CostsheetRepository


class ExportCostsheetsService(BaseService[ListCostsheetsRequest, FileDownloadDTO]):
    def __init__(self, repository: CostsheetRepository | None = None, today: date | None = None) -> None:
        self.repository = repository or CostsheetRepository()
        self.today = today or date.today()

    def execute(self, request: ListCostsheetsRequest) -> FileDownloadDTO:
        business = ListBusiness()
        rows = business.filter(self.repository.list_all(), CostsheetFilter(**request.model_dump()), self.current_user)
        dtos = CostsheetRowsBuilder(rows, {s.id: business.warning_text(s) for s in rows}).build()
        self.logger.info("UC-28 export of %s costsheets", len(dtos))
        return CostsheetExportBuilder(dtos, f"danh-sach-costsheet-{self.today:%Y%m%d}.xlsx").build()
