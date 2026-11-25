"""UC-31 Xem danh sách tỷ giá."""

from backend.core.base import BaseService, EmptyRequest
from backend.features.woven_costing.builders.dto_builders import MasterRowsBuilder
from backend.features.woven_costing.dto.master_dto import ExchangeRateListResponse
from backend.features.woven_costing.repositories.master_repository import ExchangeRateRepository


class ListExchangeRatesService(BaseService[EmptyRequest, ExchangeRateListResponse]):
    def __init__(self, repository: ExchangeRateRepository | None = None) -> None:
        self.repository = repository or ExchangeRateRepository()

    def execute(self, request: EmptyRequest) -> ExchangeRateListResponse:
        rates = self.repository.newest_first()
        self.logger.info("UC-31 %s exchange rates", len(rates))
        return ExchangeRateListResponse(rows=MasterRowsBuilder().rates(rates))
