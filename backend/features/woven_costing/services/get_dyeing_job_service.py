"""UC-44 Xem phiếu gia công nhuộm (2026-11-25)."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.dyeing_job_builders import DyeingJobResponseBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.dyeing_job_business import DyeingJobBusiness
from backend.features.woven_costing.dto.dyeing_job_dto import DyeingJobResponse, GetDyeingJobRequest
from backend.features.woven_costing.exceptions import CostsheetNotFoundError
from backend.features.woven_costing.repositories.dyeing_job_repository import DyeingJobRepository


class GetDyeingJobService(BaseService[GetDyeingJobRequest, DyeingJobResponse]):
    def __init__(self, repository: DyeingJobRepository | None = None) -> None:
        self.repository = repository or DyeingJobRepository()

    def execute(self, request: GetDyeingJobRequest) -> DyeingJobResponse:
        access = AccessBusiness()
        user = self.current_user
        job = self.repository.get(request.job_id)
        if job is None:
            raise CostsheetNotFoundError("Không tìm thấy phiếu gia công.")
        access.ensure_view(user, job)
        business = DyeingJobBusiness()
        return DyeingJobResponseBuilder(
            job, business.allowed_actions(job, user), business.is_editable(job, user)
        ).build()
