"""UC-30 Việc chờ tôi."""

from datetime import date

from backend.core.base import BaseService, EmptyRequest
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.list_business import ListBusiness
from backend.features.woven_costing.business.submission_business import SubmissionBusiness
from backend.features.woven_costing.dto.list_dto import MyTasksResponse, TaskGroupDTO, TaskRowDTO
from backend.features.woven_costing.models.costsheet import Costsheet
from backend.features.woven_costing.models.dyeing_job import DyeingJob
from backend.features.woven_costing.models.enums import CostsheetStatus, RoleCode
from backend.features.woven_costing.repositories.costsheet_repository import CostsheetRepository
from backend.features.woven_costing.repositories.dyeing_job_repository import DyeingJobRepository
from backend.features.woven_costing.repositories.fabric_repository import FabricRepository
from backend.features.woven_costing.repositories.master_repository import ExchangeRateRepository, HolidayRepository
from backend.features.woven_costing.repositories.norm_repository import ParameterSetRepository

S = CostsheetStatus


def _row(sheet: Costsheet, reason: str = "") -> TaskRowDTO:
    return TaskRowDTO(
        costsheet_id=sheet.id, costsheet_no=sheet.costsheet_no, version=sheet.version, customer_name=sheet.customer_name,
        tcfno=sheet.tcfno, sales_name=sheet.sales_name, costing_date=sheet.costing_date, gp_pct=sheet.result.gp_pct,
        op_pct=sheet.result.op_pct, reason=reason or None,
    )  # fmt: skip


def _job_row(job: DyeingJob, reason: str = "") -> TaskRowDTO:
    return TaskRowDTO(
        costsheet_id=job.id, costsheet_no=job.job_no, customer_name=job.customer_name, sales_name=job.sales_name,
        costing_date=job.costing_date, gp_pct=job.result.gp_pct, reason=reason or None,
    )  # fmt: skip


class ListMyTasksService(BaseService[EmptyRequest, MyTasksResponse]):
    def __init__(self, repository: CostsheetRepository | None = None, today: date | None = None) -> None:
        self.repository = repository or CostsheetRepository()
        self.today = today or date.today()

    def execute(self, request: EmptyRequest) -> MyTasksResponse:
        user = self.current_user
        access = AccessBusiness()
        sheets = ListBusiness().visible(self.repository.latest_versions(), user)
        mine = [s for s in sheets if access.is_owner(user, s)]
        groups: list[TaskGroupDTO] = []
        to_approve = [_row(s) for s in sheets if s.status == S.CHO_DUYET and access.can_approve(user, s)]
        groups.append(TaskGroupDTO(code="approve", title="Chờ tôi duyệt", rows=to_approve))
        groups.append(TaskGroupDTO(code="returned", title="Bị trả lại",
                                   rows=[_row(s, s.return_reason) for s in mine if s.status == S.TRA_LAI]))  # fmt: skip
        groups.append(TaskGroupDTO(code="no_oc", title="Đã duyệt chưa có OC",
                                   rows=[_row(s) for s in mine if s.status == S.DA_DUYET and not s.oc_no]))  # fmt: skip
        holidays = {h.date for h in HolidayRepository().list_all()}
        submission = SubmissionBusiness()
        expired = []
        for sheet in [s for s in mine if s.status == S.NHAP]:
            params = ParameterSetRepository().effective_on(sheet.costing_date)
            days = int(params.values.yarn_price_valid_days) if params else 5
            messages = submission.expired_prices(sheet, self.today, holidays, days)
            if messages:
                expired.append(_row(sheet, messages[0]))
        groups.append(TaskGroupDTO(code="expired_prices", title="Giá sợi hết hiệu lực", rows=expired))
        # 2026-11-25 dyeing job orders (Screen 8)
        jobs = [j for j in DyeingJobRepository().list_all() if access.can_view(user, j)]
        job_approve = [_job_row(j) for j in jobs if j.status == S.CHO_DUYET and access.can_approve(user, j)]
        job_returned = [
            _job_row(j, j.return_reason) for j in jobs if j.status == S.TRA_LAI and access.is_owner(user, j)
        ]
        groups.append(TaskGroupDTO(code="job_approve", title="Phiếu gia công chờ tôi duyệt", kind="dyeing_job",
                                   rows=job_approve))  # fmt: skip
        groups.append(TaskGroupDTO(code="job_returned", title="Phiếu gia công bị trả lại", kind="dyeing_job",
                                   rows=job_returned))  # fmt: skip
        if RoleCode.SO.value in access.roles(user):
            rate = ExchangeRateRepository().for_month(self.today.month, self.today.year)
            rate_rows = [] if rate else [TaskRowDTO(reason=f"Chưa có tỷ giá tháng {self.today:%m/%Y}.")]
            groups.append(TaskGroupDTO(code="exchange_rate", title="Tỷ giá tháng này", kind="exchange_rate",
                                       rows=rate_rows))  # fmt: skip
            missing = [f for f in FabricRepository().list_all() if not f.yarns]
            fabric_rows = [TaskRowDTO(tcfno=f.tcfno, reason=f"{f.fabric_name}: thiếu dòng sợi") for f in missing]
            groups.append(TaskGroupDTO(code="missing_yarn", title="Mã vải thiếu sợi", kind="fabric", rows=fabric_rows))
        self.logger.info("UC-30 tasks: %s", {g.code: len(g.rows) for g in groups})
        return MyTasksResponse(groups=groups)
