"""UC-46 Kiểm tra Siro / Compact bất thường (BR-71)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.siro_compact_business import SiroCompactBusiness
from backend.features.yarn_costing.dto.dashboard_dto import (
    CheckSiroAnomaliesRequest,
    SiroAnomalyResponse,
    SiroNsmAnomalyDTO,
    SiroPriceAnomalyDTO,
)
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

EMPTY = "Không có mã Siro / Compact bất thường."


class CheckSiroAnomaliesService(BaseService[CheckSiroAnomaliesRequest, SiroAnomalyResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.business = SiroCompactBusiness()

    def execute(self, request: CheckSiroAnomaliesRequest) -> SiroAnomalyResponse:
        yarns = [
            y
            for y in self.repository.list_all()
            if request.factory_code is None or y.factory_code == request.factory_code
        ]
        nsm = self.business.nsm_anomalies(yarns)
        price = self.business.price_anomalies(yarns)
        self.logger.info("Siro / Compact anomalies: %s NSM rows, %s price rows", len(nsm), len(price))
        return SiroAnomalyResponse(
            nsm_items=[SiroNsmAnomalyDTO(**i.model_dump()) for i in nsm],
            price_items=[SiroPriceAnomalyDTO(**i.model_dump()) for i in price],
            empty_message="" if nsm or price else EMPTY,
        )
