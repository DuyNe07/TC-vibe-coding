"""UC-40 Tạo phiếu gia công nhuộm (2026-11-25)."""

from datetime import date

from backend.core.base import BaseService
from backend.features.woven_costing.builders.dyeing_job_builders import DyeingJobResponseBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.dyeing_job_business import DyeingJobBusiness
from backend.features.woven_costing.dto.dyeing_job_dto import CreateDyeingJobRequest, DyeingJobResponse
from backend.features.woven_costing.exceptions import WovenCostingError
from backend.features.woven_costing.models.dyeing_job import DyeingJob, DyeingJobLine
from backend.features.woven_costing.repositories.costing_data import load_costing_data
from backend.features.woven_costing.repositories.dyeing_job_repository import DyeingJobRepository
from backend.features.woven_costing.repositories.master_repository import CustomerRepository


class CreateDyeingJobService(BaseService[CreateDyeingJobRequest, DyeingJobResponse]):
    def __init__(self, repository: DyeingJobRepository | None = None, today: date | None = None) -> None:
        self.repository = repository or DyeingJobRepository()
        self.today = today or date.today()

    def execute(self, request: CreateDyeingJobRequest) -> DyeingJobResponse:
        access = AccessBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-40")
        team = access.ensure_team(user)
        customer = next((c for c in CustomerRepository().list_all() if c.name == request.customer_name.strip()), None)
        if customer is None:
            raise WovenCostingError("Vui lòng chọn khách hàng có trong danh sách (hoặc bấm Thêm khách hàng).")
        business = DyeingJobBusiness()
        number = business.job_number(customer.customer_code, self.today.year, self.repository.numbers())
        job = DyeingJob(
            job_no=number,
            contract_no=request.contract_no.strip()[:60],
            customer_name=customer.name,
            dye_plant=request.dye_plant,
            costing_date=request.costing_date or self.today,
            sales_username=access.username(user),
            sales_name=access.display_name(user),
            team=team,
            lines=[DyeingJobLine()],
            created_by=access.username(user),
        )
        job = self.repository.add(business.recalculate(job, load_costing_data("")))
        self.logger.info("UC-40 dyeing job %s created", number)
        return DyeingJobResponseBuilder(job, business.allowed_actions(job, user), business.is_editable(job, user),
                                        f"Đã tạo phiếu gia công {number}.").build()  # fmt: skip
