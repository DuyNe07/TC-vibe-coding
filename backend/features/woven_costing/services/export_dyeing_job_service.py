"""UC-46 Xuất bảng giá gia công nhuộm ra Excel (F-09, 2026-11-25)."""

from backend.core.base import BaseService, FileDownloadDTO
from backend.features.woven_costing.builders.dyeing_job_builders import DyeingJobExcelBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.dto.dyeing_job_dto import GetDyeingJobRequest
from backend.features.woven_costing.exceptions import CostsheetNotFoundError
from backend.features.woven_costing.repositories.dyeing_job_repository import DyeingJobRepository


class ExportDyeingJobService(BaseService[GetDyeingJobRequest, FileDownloadDTO]):
    def __init__(self, repository: DyeingJobRepository | None = None) -> None:
        self.repository = repository or DyeingJobRepository()

    def execute(self, request: GetDyeingJobRequest) -> FileDownloadDTO:
        job = self.repository.get(request.job_id)
        if job is None:
            raise CostsheetNotFoundError("Không tìm thấy phiếu gia công.")
        AccessBusiness().ensure_view(self.current_user, job)
        self.logger.info("UC-46 dyeing job %s exported", job.job_no)
        return DyeingJobExcelBuilder(job).build()
