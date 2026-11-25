"""UC-25 Hủy costsheet."""

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


class CancelCostsheetService(BaseService[CostsheetActionRequest, CostsheetResponse]):
    def __init__(self, repository: CostsheetRepository | None = None) -> None:
        self.repository = repository or CostsheetRepository()

    def execute(self, request: CostsheetActionRequest) -> CostsheetResponse:
        access = AccessBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-25")
        sheet = self.repository.get(request.costsheet_id)
        if sheet is None:
            raise CostsheetNotFoundError("Không tìm thấy costsheet.")
        access.ensure_owner(user, sheet)
        workflow = WorkflowBusiness()
        reason = (request.reason or "").strip()
        workflow.ensure_cancel(sheet, reason)
        workflow.ensure_transition(sheet, CostsheetStatus.HUY)
        sheet = self.repository.update(
            sheet.model_copy(update={"status": CostsheetStatus.HUY, "cancel_reason": reason})
        )
        CostsheetHistoryRepository().add(
            CostsheetHistory(
                costsheet_no=sheet.costsheet_no,
                version=sheet.version,
                action=HistoryAction.CANCEL,
                by=access.username(user),
                by_name=access.display_name(user),
                comment=reason,
            )  # fmt: skip
        )
        self.logger.info("UC-25 %s cancelled: %s", sheet.label, reason)
        business = CostsheetBusiness()
        view = load_costsheet_view(sheet)
        return CostsheetResponseBuilder(
            sheet,
            view,
            actions=business.allowed_actions(sheet, user, view.versions, view.fabric_source),
            message=f"Đã hủy costsheet {sheet.costsheet_no} v{sheet.version}.",
        ).build()
