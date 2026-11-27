"""UC-47 Duyệt nhiều costsheet một lần (2026-11-27, BR-102)."""

from backend.core.base import BaseService
from backend.core.exceptions import AppError
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.approval_business import ApprovalBusiness, failed_text
from backend.features.woven_costing.business.costsheet_business import CostsheetBusiness
from backend.features.woven_costing.business.workflow_business import WorkflowBusiness
from backend.features.woven_costing.dto.list_dto import BulkApproveRequest, BulkApproveResponse
from backend.features.woven_costing.models.enums import CostsheetStatus
from backend.features.woven_costing.repositories.costsheet_repository import (
    CostsheetHistoryRepository,
    CostsheetRepository,
)


class ApproveCostsheetsService(BaseService[BulkApproveRequest, BulkApproveResponse]):
    def __init__(self, repository: CostsheetRepository | None = None) -> None:
        self.repository = repository or CostsheetRepository()

    def execute(self, request: BulkApproveRequest) -> BulkApproveResponse:
        access, workflow, approval = AccessBusiness(), WorkflowBusiness(), ApprovalBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-21")
        who, name = access.username(user), access.display_name(user)
        approved: list[str] = []
        failed: list[str] = []
        for costsheet_id in dict.fromkeys(request.ids):
            sheet = self.repository.get(costsheet_id)
            if sheet is None:
                failed.append(failed_text(costsheet_id, "Không tìm thấy costsheet."))
                continue
            try:  # BR-102: each costsheet is checked like UC-21; one refusal does not stop the others
                workflow.ensure_pending(sheet)
                access.ensure_approve(user, sheet)
                workflow.ensure_transition(sheet, CostsheetStatus.DA_DUYET)
            except AppError as exc:
                failed.append(failed_text(sheet.label, exc.message))
                continue
            done = approval.approved_sheet(sheet, who, name)
            versions = self.repository.versions(done.costsheet_no)
            self.repository.save_many([done, *CostsheetBusiness().superseded(done, versions)])
            CostsheetHistoryRepository().add(approval.approve_history(done, who, name))
            approved.append(done.label)
        self.logger.info("UC-47 %s approved %d costsheets, %d refused", who, len(approved), len(failed))
        return BulkApproveResponse(
            approved=approved, failed=failed, message=approval.summary(len(approved), len(failed), "costsheet")
        )
