"""UC-08 Cập nhật tỷ giá (không tính lại giá VND)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.display_business import format_vnd
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.dto.common_dto import SaveCountResponse
from backend.features.yarn_costing.dto.master_dto import AddExchangeRateRequest
from backend.features.yarn_costing.models.exchange_rate import ExchangeRate
from backend.features.yarn_costing.repositories.exchange_rate_repository import ExchangeRateRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository


class AddExchangeRateService(BaseService[AddExchangeRateRequest, SaveCountResponse]):
    def __init__(self, repository: ExchangeRateRepository | None = None) -> None:
        self.repository = repository or ExchangeRateRepository()
        self.access = AccessBusiness()
        self.master = MasterBusiness()

    def execute(self, request: AddExchangeRateRequest) -> SaveCountResponse:
        self.access.ensure_allowed(self.current_user, "UC-08")
        self.master.ensure_positive(request.rate, "Tỷ giá phải lớn hơn 0.")
        rate = ExchangeRate(
            effective_date=request.effective_date,
            rate=request.rate,
            note=request.note.strip(),  # type: ignore[arg-type]
            created_by=self.access.user_label(self.current_user),
        )
        self.repository.add(rate)
        day = rate.effective_date.strftime("%d/%m/%Y")
        AuditLogRepository().add(self.access.audit_entry(self.current_user, "UC-08", "Tỷ giá", f"{rate.rate} từ {day}"))
        self.logger.info("Exchange rate %s from %s added", rate.rate, rate.effective_date)
        return SaveCountResponse(message=f"Đã thêm tỷ giá {format_vnd(rate.rate)} từ ngày {day}.", saved_count=1)
