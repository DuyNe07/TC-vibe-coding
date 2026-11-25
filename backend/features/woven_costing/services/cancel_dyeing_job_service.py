"""UC-43 Hủy phiếu gia công nhuộm (lý do bắt buộc; 2026-11-25)."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.dyeing_job_builders import DyeingJobResponseBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.dyeing_job_business import DyeingJobBusiness
from backend.features.woven_costing.business.workflow_business import WorkflowBusiness
from backend.features.woven_costing.dto.dyeing_job_dto import DyeingJobActionRequest, DyeingJobResponse
from backend.features.woven_costing.exceptions import CostsheetNotFoundError
from backend.features.woven_costing.models.enums import CostsheetStatus
from backend.features.woven_costing.repositories.dyeing_job_repository import DyeingJobRepository


class CancelDyeingJobService(BaseService[DyeingJobActionRequest, DyeingJobResponse]):
    def __init__(self, repository: DyeingJobRepository | None = None) -> None:
        self.repository = repository or DyeingJobRepository()

    def execute(self, request: DyeingJobActionRequest) -> DyeingJobResponse:
        access = AccessBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-43")
        job = self.repository.get(request.job_id)
        if job is None:
            raise CostsheetNotFoundError("Không tìm thấy phiếu gia công.")
        access.ensure_owner(user, job)
        workflow = WorkflowBusiness()
        reason = request.reason.strip()
        workflow.ensure_cancel(job, reason)
        workflow.ensure_transition(job, CostsheetStatus.HUY)
        job = self.repository.update(job.model_copy(update={"status": CostsheetStatus.HUY, "cancel_reason": reason}))
        business = DyeingJobBusiness()
        self.logger.info("UC-43 dyeing job %s cancelled", job.job_no)
        return DyeingJobResponseBuilder(job, business.allowed_actions(job, user), business.is_editable(job, user),
                                        f"Đã hủy phiếu gia công {job.job_no}.").build()  # fmt: skip
