"""UC-05 Cập nhật tỷ giá tháng."""

from backend.core.base import BaseService
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.master_business import MasterBusiness
from backend.features.woven_costing.dto.common_dto import MessageResponse
from backend.features.woven_costing.dto.master_dto import SaveExchangeRateRequest
from backend.features.woven_costing.models.master import ExchangeRate
from backend.features.woven_costing.repositories.master_repository import ExchangeRateRepository


class SaveExchangeRateService(BaseService[SaveExchangeRateRequest, MessageResponse]):
    def __init__(self, repository: ExchangeRateRepository | None = None) -> None:
        self.repository = repository or ExchangeRateRepository()

    def execute(self, request: SaveExchangeRateRequest) -> MessageResponse:
        access = AccessBusiness()
        access.ensure_use_case(self.current_user, "UC-05")
        MasterBusiness().ensure_rate(request.rate)
        user = access.display_name(self.current_user)
        stored = self.repository.for_month(request.month, request.year)
        if stored is None:
            self.repository.add(
                ExchangeRate(month=request.month, year=request.year, rate=request.rate, updated_by=user)
            )
        else:
            self.repository.update(stored.model_copy(update={"rate": request.rate, "updated_by": user}))
        self.logger.info("UC-05 rate %02d/%s = %s (new=%s)", request.month, request.year, request.rate, stored is None)
        rate = f"{request.rate:,.0f}".replace(",", ".")
        return MessageResponse(message=f"Đã lưu tỷ giá tháng {request.month:02d}/{request.year}: {rate}.")
