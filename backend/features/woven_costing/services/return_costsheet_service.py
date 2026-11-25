"""UC-22 Trả lại costsheet."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.costsheet_response_builder import CostsheetResponseBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.costsheet_business import CostsheetBusiness
from backend.features.woven_costing.business.workflow_business import WorkflowBusiness
from backend.features.woven_costing.dto.costsheet_dto import CostsheetActionRequest, CostsheetResponse
from backend.features.woven_costing.exceptions import CostsheetNotFoundError
from backend.features.woven_costing.models.costsheet import CostsheetHistory
from backend.features.woven_costing.models.enums import CostsheetStatus, HistoryAction
from backend.features.woven_costing.repositories.costing_data import load_costsheet_view
from backend.features.woven_costing.repositories.costsheet_repository import (
    CostsheetHistoryRepository,
    CostsheetRepository,
)


class ReturnCostsheetService(BaseService[CostsheetActionRequest, CostsheetResponse]):
    def __init__(self, repository: CostsheetRepository | None = None) -> None:
        self.repository = repository or CostsheetRepository()

    def execute(self, request: CostsheetActionRequest) -> CostsheetResponse:
        access = AccessBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-22")
        sheet = self.repository.get(request.costsheet_id)
        if sheet is None:
            raise CostsheetNotFoundError("Không tìm thấy costsheet.")
        workflow = WorkflowBusiness()
        workflow.ensure_pending(sheet)
        access.ensure_approve(user, sheet)
        reason = (request.reason or "").strip()
        workflow.ensure_return_reason(reason)
        workflow.ensure_transition(sheet, CostsheetStatus.TRA_LAI)
        sheet = self.repository.update(
            sheet.model_copy(update={"status": CostsheetStatus.TRA_LAI, "return_reason": reason})
        )
        CostsheetHistoryRepository().add(
            CostsheetHistory(
                costsheet_no=sheet.costsheet_no,
                version=sheet.version,
                action=HistoryAction.RETURN,
                by=access.username(user),
                by_name=access.display_name(user),
                comment=reason,
            )  # fmt: skip
        )
        self.logger.info("UC-22 %s returned: %s", sheet.label, reason)
        business = CostsheetBusiness()
        view = load_costsheet_view(sheet)
        return CostsheetResponseBuilder(
            sheet,
            view,
            actions=business.allowed_actions(sheet, user, view.versions, view.fabric_source),
            message=f"Đã trả lại costsheet {sheet.costsheet_no} v{sheet.version}.",
        ).build()
