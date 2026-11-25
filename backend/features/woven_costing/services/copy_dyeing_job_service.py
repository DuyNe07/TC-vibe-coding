"""UC-45 Sao chép phiếu gia công nhuộm (2026-11-25)."""

from datetime import date

from backend.core.base import BaseService
from backend.features.woven_costing.builders.dyeing_job_builders import DyeingJobResponseBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.dyeing_job_business import DyeingJobBusiness
from backend.features.woven_costing.dto.dyeing_job_dto import DyeingJobActionRequest, DyeingJobResponse
from backend.features.woven_costing.exceptions import CostsheetNotFoundError
from backend.features.woven_costing.models.dyeing_job import DyeingJob
from backend.features.woven_costing.repositories.costing_data import load_costing_data
from backend.features.woven_costing.repositories.dyeing_job_repository import DyeingJobRepository
from backend.features.woven_costing.repositories.master_repository import CustomerRepository


class CopyDyeingJobService(BaseService[DyeingJobActionRequest, DyeingJobResponse]):
    def __init__(self, repository: DyeingJobRepository | None = None, today: date | None = None) -> None:
        self.repository = repository or DyeingJobRepository()
        self.today = today or date.today()

    def execute(self, request: DyeingJobActionRequest) -> DyeingJobResponse:
        access = AccessBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-45")
        team = access.ensure_team(user)
        source = self.repository.get(request.job_id)
        if source is None:
            raise CostsheetNotFoundError("Không tìm thấy phiếu gia công.")
        access.ensure_view(user, source)
        business = DyeingJobBusiness()
        customer = next((c for c in CustomerRepository().list_all() if c.name == source.customer_name), None)
        code = customer.customer_code if customer else source.job_no.split("-")[1]
        number = business.job_number(code, self.today.year, self.repository.numbers())
        job = DyeingJob(
            job_no=number,
            copied_from=source.job_no,
            contract_no=source.contract_no,
            customer_name=source.customer_name,
            dye_plant=source.dye_plant,
            costing_date=self.today,
            note=source.note,
            sales_username=access.username(user),
            sales_name=access.display_name(user),
            team=team,
            lines=business.copy_lines(source),
            created_by=access.username(user),
        )
        job = self.repository.add(business.recalculate(job, load_costing_data("")))
        self.logger.info("UC-45 dyeing job %s copied to %s", source.job_no, number)
        return DyeingJobResponseBuilder(job, business.allowed_actions(job, user), business.is_editable(job, user),
                                        f"Đã sao chép thành phiếu gia công {number}.").build()  # fmt: skip
