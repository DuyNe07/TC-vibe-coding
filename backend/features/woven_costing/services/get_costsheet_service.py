"""UC-29 Xem costsheet."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.costsheet_response_builder import CostsheetResponseBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.costsheet_business import CostsheetBusiness
from backend.features.woven_costing.dto.costsheet_dto import CostsheetResponse, GetCostsheetRequest
from backend.features.woven_costing.exceptions import CostsheetNotFoundError
from backend.features.woven_costing.repositories.costing_data import load_costsheet_view
from backend.features.woven_costing.repositories.costsheet_repository import CostsheetRepository


class GetCostsheetService(BaseService[GetCostsheetRequest, CostsheetResponse]):
    def __init__(self, repository: CostsheetRepository | None = None) -> None:
        self.repository = repository or CostsheetRepository()

    def execute(self, request: GetCostsheetRequest) -> CostsheetResponse:
        sheet = self.repository.get(request.costsheet_id) if request.costsheet_id else None
        number = (request.costsheet_no or "").strip().upper()
        if sheet is None and number:
            versions = self.repository.versions(number)
            if request.version is not None:
                sheet = next((v for v in versions if v.version == request.version), None)
            elif versions:
                sheet = versions[-1]
        if sheet is None:
            raise CostsheetNotFoundError(f"Không tìm thấy costsheet {number or ''}.".replace("  ", " "))
        user = self.current_user
        AccessBusiness().ensure_view(user, sheet)
        business = CostsheetBusiness()
        view = load_costsheet_view(sheet)
        self.logger.info("UC-29 %s opened (%s)", sheet.label, sheet.status)
        return CostsheetResponseBuilder(
            sheet,
            view,
            actions=business.allowed_actions(sheet, user, view.versions, view.fabric_source),
            editable=business.is_editable(sheet, user),
        ).build()
