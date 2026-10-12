"""UC-30 Kiểm tra giá bất thường (BR-39)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.analysis_business import AnalysisBusiness
from backend.features.yarn_costing.dto.dashboard_dto import (
    CheckPriceAnomaliesRequest,
    PriceAnomalyDTO,
    PriceAnomalyResponse,
)
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class CheckPriceAnomaliesService(BaseService[CheckPriceAnomaliesRequest, PriceAnomalyResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.analysis = AnalysisBusiness()

    def execute(self, request: CheckPriceAnomaliesRequest) -> PriceAnomalyResponse:
        yarns = [
            y
            for y in self.repository.list_all()
            if request.factory_code is None or y.factory_code == request.factory_code
        ]
        items = self.analysis.price_anomalies(yarns)
        groups = {(i.factory_code, i.technology, i.yarn_group, i.loss_group_key) for i in items}
        self.logger.info("Price anomalies: %s pairs in %s groups", len(items), len(groups))
        return PriceAnomalyResponse(
            items=[PriceAnomalyDTO(**i.model_dump()) for i in items], group_count=len(groups), pair_count=len(items)
        )
