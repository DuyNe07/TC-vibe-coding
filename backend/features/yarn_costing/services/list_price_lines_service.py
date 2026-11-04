"""UC-27 Tra cứu bảng giá."""

from datetime import date

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.price_rows_builder import PriceLineRowsBuilder
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.dto.price_dto import ListPriceLinesRequest, PriceLineListResponse
from backend.features.yarn_costing.models.enums import YarnStatus
from backend.features.yarn_costing.repositories.exchange_rate_repository import (
    ExchangeRateRepository,
    SettingsRepository,
)
from backend.features.yarn_costing.repositories.packaging_type_repository import PackagingTypeRepository
from backend.features.yarn_costing.repositories.stage_repository import StageRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class ListPriceLinesService(BaseService[ListPriceLinesRequest, PriceLineListResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.costing = CostingBusiness()

    def execute(self, request: ListPriceLinesRequest) -> PriceLineListResponse:
        rate = self.costing.current_exchange_rate(ExchangeRateRepository().list_all(), date.today())
        yarns = self.repository.list_all()
        names = {(p.factory_code.value, p.code): p.name for p in PackagingTypeRepository().list_all()}
        rows = PriceLineRowsBuilder(
            yarns, request, rate.rate if rate else None, names, StageRepository().list_all()
        ).build()
        scoped = [y for y in yarns if request.factory_code is None or y.factory_code == request.factory_code]
        self.logger.info(
            "Price lines: %s rows (factory=%s, keyword=%r)", len(rows), request.factory_code, request.keyword
        )
        return PriceLineListResponse(
            items=rows,
            total_count=len(rows),
            with_accounting_code_count=sum(1 for r in rows if r.accounting_code),
            not_priced_count=sum(1 for y in scoped if y.status == YarnStatus.CHUA_TINH_DUOC),
            waiting_count=sum(1 for y in scoped if y.status == YarnStatus.CHO_XUONG_XEM),
            exchange_rate=rate.rate if rate else None,
            exchange_rate_date=rate.effective_date if rate else None,
            trial_factor=SettingsRepository().get_settings().trial_factor,
        )
