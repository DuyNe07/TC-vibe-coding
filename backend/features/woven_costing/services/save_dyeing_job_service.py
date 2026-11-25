"""UC-42 Lưu nháp phiếu gia công nhuộm (2026-11-25)."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.dyeing_job_builders import DyeingJobResponseBuilder, apply_input
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.dyeing_job_business import DyeingJobBusiness
from backend.features.woven_costing.dto.dyeing_job_dto import DyeingJobInputRequest, DyeingJobResponse
from backend.features.woven_costing.exceptions import CostsheetNotFoundError
from backend.features.woven_costing.models.enums import CostsheetStatus
from backend.features.woven_costing.repositories.costing_data import load_costing_data
from backend.features.woven_costing.repositories.dyeing_job_repository import DyeingJobRepository


class SaveDyeingJobService(BaseService[DyeingJobInputRequest, DyeingJobResponse]):
    def __init__(self, repository: DyeingJobRepository | None = None) -> None:
        self.repository = repository or DyeingJobRepository()

    def execute(self, request: DyeingJobInputRequest) -> DyeingJobResponse:
        access = AccessBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-42")
        job = self.repository.get(request.job_id)
        if job is None:
            raise CostsheetNotFoundError("Không tìm thấy phiếu gia công.")
        access.ensure_owner(user, job)
        business = DyeingJobBusiness()
        business.ensure_editable(job)
        job = apply_input(job, request)
        business.check_lines(job.lines)
        job = business.recalculate(job, load_costing_data(""))
        job = self.repository.update(job.model_copy(update={"status": CostsheetStatus.NHAP}))  # BR-34
        self.logger.info("UC-42 dyeing job %s saved (%s lines)", job.job_no, len(job.lines))
        return DyeingJobResponseBuilder(job, business.allowed_actions(job, user), business.is_editable(job, user),
                                        f"Đã lưu phiếu gia công {job.job_no}.").build()  # fmt: skip
