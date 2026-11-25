"""UC-43 Gửi duyệt phiếu gia công nhuộm (the typed cells are saved first; 2026-11-25)."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.dyeing_job_builders import DyeingJobResponseBuilder, apply_input
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.dyeing_job_business import DyeingJobBusiness
from backend.features.woven_costing.business.workflow_business import WorkflowBusiness
from backend.features.woven_costing.dto.dyeing_job_dto import DyeingJobActionRequest, DyeingJobResponse
from backend.features.woven_costing.exceptions import CostsheetNotFoundError
from backend.features.woven_costing.models.access import SO_TEAM
from backend.features.woven_costing.models.enums import CostsheetStatus
from backend.features.woven_costing.repositories.costing_data import load_costing_data
from backend.features.woven_costing.repositories.dyeing_job_repository import DyeingJobRepository


class SubmitDyeingJobService(BaseService[DyeingJobActionRequest, DyeingJobResponse]):
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
        business = DyeingJobBusiness()
        business.ensure_editable(job)
        if request.input is not None:
            job = apply_input(job, request.input)
        business.check_lines(job.lines)
        job = self.repository.update(business.recalculate(job, load_costing_data("")))
        business.ensure_submittable(job)  # BR-98 (the typed cells stay saved)
        WorkflowBusiness().ensure_transition(job, CostsheetStatus.CHO_DUYET)
        job = self.repository.update(job.model_copy(update={"status": CostsheetStatus.CHO_DUYET}))
        approver = "Phòng SO" if job.team == SO_TEAM else f"trưởng team {job.team}"  # BR-53
        self.logger.info("UC-43 dyeing job %s submitted", job.job_no)
        message = f"Đã gửi duyệt phiếu gia công {job.job_no}. Người duyệt: {approver} hoặc trưởng đơn vị."
        return DyeingJobResponseBuilder(job, business.allowed_actions(job, user), business.is_editable(job, user),
                                        message).build()  # fmt: skip
