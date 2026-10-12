"""UC-19 Xem danh sách yêu cầu / mã cần xử lý."""

from collections import Counter
from datetime import date

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import summary_dto
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.business.dashboard_business import local_date
from backend.features.yarn_costing.dto.request_dto import ListYarnsRequest, YarnListResponse
from backend.features.yarn_costing.repositories.exchange_rate_repository import ExchangeRateRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class ListYarnsService(BaseService[ListYarnsRequest, YarnListResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.costing = CostingBusiness()

    def execute(self, request: ListYarnsRequest) -> YarnListResponse:
        rate = self.costing.current_exchange_rate(ExchangeRateRepository().list_all(), date.today())
        yarns = [
            y
            for y in self.repository.list_all()
            if request.factory_code is None or y.factory_code == request.factory_code
        ]
        counts = Counter(y.status.value for y in yarns)
        keyword = request.keyword.strip().casefold()
        items = []
        for y in yarns:
            day = local_date(y.requested_at)
            if request.statuses and y.status not in request.statuses:
                continue
            if request.date_from and day < request.date_from or request.date_to and day > request.date_to:
                continue
            if request.origin and y.origin.value != request.origin:
                continue
            if keyword and keyword not in f"{y.yarn_code} {y.yarn_name}".casefold():
                continue
            items.append(y)
        items.sort(key=lambda y: y.requested_at, reverse=not request.oldest_first)
        self.logger.info(
            "Yarn list: %s of %s (factory=%s, statuses=%s)",
            len(items),
            len(yarns),
            request.factory_code,
            request.statuses,
        )
        return YarnListResponse(
            items=[summary_dto(y, rate.rate if rate else None) for y in items], status_counts=dict(counts)
        )
