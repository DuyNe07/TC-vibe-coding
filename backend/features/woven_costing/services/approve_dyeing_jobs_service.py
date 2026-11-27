"""UC-48 Duyệt nhiều phiếu gia công nhuộm một lần (2026-11-27, BR-102)."""

from backend.core.base import BaseService
from backend.core.exceptions import AppError
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.approval_business import ApprovalBusiness, failed_text
from backend.features.woven_costing.business.workflow_business import WorkflowBusiness
from backend.features.woven_costing.dto.list_dto import BulkApproveRequest, BulkApproveResponse
from backend.features.woven_costing.models.enums import CostsheetStatus
from backend.features.woven_costing.repositories.dyeing_job_repository import DyeingJobRepository


class ApproveDyeingJobsService(BaseService[BulkApproveRequest, BulkApproveResponse]):
    def __init__(self, repository: DyeingJobRepository | None = None) -> None:
        self.repository = repository or DyeingJobRepository()

    def execute(self, request: BulkApproveRequest) -> BulkApproveResponse:
        access, workflow, approval = AccessBusiness(), WorkflowBusiness(), ApprovalBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-21")
        who, name = access.username(user), access.display_name(user)
        approved: list[str] = []
        failed: list[str] = []
        for job_id in dict.fromkeys(request.ids):
            job = self.repository.get(job_id)
            if job is None:
                failed.append(failed_text(job_id, "Không tìm thấy phiếu gia công."))
                continue
            try:  # BR-102 / BR-99: each order is checked like UC-43
                workflow.ensure_pending(job)
                access.ensure_approve(user, job)
                workflow.ensure_transition(job, CostsheetStatus.DA_DUYET)
            except AppError as exc:
                failed.append(failed_text(job.job_no, exc.message))
                continue
            self.repository.update(approval.approved_job(job, who, name))
            approved.append(job.job_no)
        self.logger.info("UC-48 %s approved %d dyeing jobs, %d refused", who, len(approved), len(failed))
        return BulkApproveResponse(
            approved=approved, failed=failed, message=approval.summary(len(approved), len(failed), "phiếu gia công")
        )
