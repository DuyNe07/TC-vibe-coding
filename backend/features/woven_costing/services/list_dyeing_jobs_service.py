"""UC-44 Danh sách phiếu gia công nhuộm (2026-11-25)."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.dyeing_job_builders import DyeingJobRowsBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.dto.dyeing_job_dto import DyeingJobListResponse, ListDyeingJobsRequest
from backend.features.woven_costing.models.dyeing_job import DyeingJob
from backend.features.woven_costing.repositories.dyeing_job_repository import DyeingJobRepository


class ListDyeingJobsService(BaseService[ListDyeingJobsRequest, DyeingJobListResponse]):
    def __init__(self, repository: DyeingJobRepository | None = None) -> None:
        self.repository = repository or DyeingJobRepository()

    def execute(self, request: ListDyeingJobsRequest) -> DyeingJobListResponse:
        access = AccessBusiness()
        user = self.current_user
        jobs = [j for j in self.repository.list_all() if access.can_view(user, j) and self._matches(j, request)]
        jobs.sort(key=lambda j: (j.costing_date, j.job_no), reverse=True)
        return DyeingJobListResponse(rows=DyeingJobRowsBuilder(jobs).build())

    def _matches(self, job: DyeingJob, request: ListDyeingJobsRequest) -> bool:
        if request.statuses and job.status not in request.statuses:
            return False
        if request.customer_name and job.customer_name != request.customer_name:
            return False
        if request.date_from and job.costing_date < request.date_from:
            return False
        if request.date_to and job.costing_date > request.date_to:
            return False
        word = request.keyword.strip().casefold()
        texts = [job.job_no, job.contract_no] + [x for line in job.lines for x in (line.item_code, line.oc_no)]
        return not word or any(word in t.casefold() for t in texts)
