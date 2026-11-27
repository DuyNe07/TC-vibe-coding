"""UC-21 Duyệt costsheet."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.costsheet_response_builder import CostsheetResponseBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.approval_business import ApprovalBusiness
from backend.features.woven_costing.business.costsheet_business import CostsheetBusiness
from backend.features.woven_costing.business.workflow_business import WorkflowBusiness
from backend.features.woven_costing.dto.costsheet_dto import CostsheetActionRequest, CostsheetResponse
from backend.features.woven_costing.exceptions import CostsheetNotFoundError
from backend.features.woven_costing.models.enums import CostsheetStatus
from backend.features.woven_costing.repositories.costing_data import load_costsheet_view
from backend.features.woven_costing.repositories.costsheet_repository import (
    CostsheetHistoryRepository,
    CostsheetRepository,
)


class ApproveCostsheetService(BaseService[CostsheetActionRequest, CostsheetResponse]):
    def __init__(self, repository: CostsheetRepository | None = None) -> None:
        self.repository = repository or CostsheetRepository()

    def execute(self, request: CostsheetActionRequest) -> CostsheetResponse:
        access = AccessBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-21")
        sheet = self.repository.get(request.costsheet_id)
        if sheet is None:
            raise CostsheetNotFoundError("Không tìm thấy costsheet.")
        workflow = WorkflowBusiness()
        workflow.ensure_pending(sheet)
        access.ensure_approve(user, sheet)
        workflow.ensure_transition(sheet, CostsheetStatus.DA_DUYET)
        who, name = access.username(user), access.display_name(user)
        approval = ApprovalBusiness()  # 2026-11-27: shared with UC-47 (approving many)
        sheet = approval.approved_sheet(sheet, who, name)
        business = CostsheetBusiness()
        self.repository.save_many([sheet, *business.superseded(sheet, self.repository.versions(sheet.costsheet_no))])
        CostsheetHistoryRepository().add(approval.approve_history(sheet, who, name, request.reason or ""))
        self.logger.info("UC-21 %s approved by %s", sheet.label, who)
        view = load_costsheet_view(sheet)
        return CostsheetResponseBuilder(
            sheet,
            view,
            actions=business.allowed_actions(sheet, user, view.versions, view.fabric_source),
            message=f"Đã duyệt costsheet {sheet.costsheet_no} v{sheet.version}.",
        ).build()
