"""UC-43 Trả lại phiếu gia công nhuộm (lý do bắt buộc; 2026-11-25)."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.dyeing_job_builders import DyeingJobResponseBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.dyeing_job_business import DyeingJobBusiness
from backend.features.woven_costing.business.workflow_business import WorkflowBusiness
from backend.features.woven_costing.dto.dyeing_job_dto import DyeingJobActionRequest, DyeingJobResponse
from backend.features.woven_costing.exceptions import CostsheetNotFoundError
from backend.features.woven_costing.models.enums import CostsheetStatus
from backend.features.woven_costing.repositories.dyeing_job_repository import DyeingJobRepository


class ReturnDyeingJobService(BaseService[DyeingJobActionRequest, DyeingJobResponse]):
    def __init__(self, repository: DyeingJobRepository | None = None) -> None:
        self.repository = repository or DyeingJobRepository()

    def execute(self, request: DyeingJobActionRequest) -> DyeingJobResponse:
        access = AccessBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-22")
        job = self.repository.get(request.job_id)
        if job is None:
            raise CostsheetNotFoundError("Không tìm thấy phiếu gia công.")
        workflow = WorkflowBusiness()
        workflow.ensure_pending(job)
        access.ensure_approve(user, job)
        reason = request.reason.strip()
        workflow.ensure_return_reason(reason)
        workflow.ensure_transition(job, CostsheetStatus.TRA_LAI)
        job = self.repository.update(
            job.model_copy(update={"status": CostsheetStatus.TRA_LAI, "return_reason": reason})
        )
        business = DyeingJobBusiness()
        self.logger.info("UC-43 dyeing job %s returned", job.job_no)
        return DyeingJobResponseBuilder(job, business.allowed_actions(job, user), business.is_editable(job, user),
                                        f"Đã trả lại phiếu gia công {job.job_no}.").build()  # fmt: skip
