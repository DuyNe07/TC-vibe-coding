"""UC-27 Danh sách costsheet."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.dto_builders import CostsheetRowsBuilder
from backend.features.woven_costing.business.list_business import ListBusiness
from backend.features.woven_costing.dto.list_dto import CostsheetKpiDTO, CostsheetListResponse, ListCostsheetsRequest
from backend.features.woven_costing.models.list_filter import CostsheetFilter
from backend.features.woven_costing.repositories.costsheet_repository import CostsheetRepository


class ListCostsheetsService(BaseService[ListCostsheetsRequest, CostsheetListResponse]):
    def __init__(self, repository: CostsheetRepository | None = None) -> None:
        self.repository = repository or CostsheetRepository()

    def execute(self, request: ListCostsheetsRequest) -> CostsheetListResponse:
        business = ListBusiness()
        rows = business.filter(self.repository.list_all(), CostsheetFilter(**request.model_dump()), self.current_user)
        warnings = {s.id: business.warning_text(s) for s in rows}
        kpis = business.kpis(rows)
        self.logger.info("UC-27 %s costsheets listed (keyword=%r)", len(rows), request.keyword)
        return CostsheetListResponse(
            rows=CostsheetRowsBuilder(rows, warnings).build(), kpis=CostsheetKpiDTO(**kpis.model_dump())
        )
