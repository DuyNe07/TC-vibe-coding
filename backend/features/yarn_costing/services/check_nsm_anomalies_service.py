"""UC-31 Kiểm tra NSM bất thường (BR-54)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.analysis_business import AnalysisBusiness
from backend.features.yarn_costing.dto.dashboard_dto import CheckNsmAnomaliesRequest, NsmAnomalyDTO, NsmAnomalyResponse
from backend.features.yarn_costing.models.enums import FactoryCode
from backend.features.yarn_costing.repositories.stage_repository import StageRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class CheckNsmAnomaliesService(BaseService[CheckNsmAnomaliesRequest, NsmAnomalyResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.analysis = AnalysisBusiness()

    def execute(self, request: CheckNsmAnomaliesRequest) -> NsmAnomalyResponse:
        yarns = [
            y
            for y in self.repository.list_all()
            if request.factory_code is None or y.factory_code == request.factory_code
        ]
        stages = StageRepository()
        by_factory = {f.value: stages.for_factory(f.value) for f in FactoryCode}
        items = self.analysis.nsm_anomalies(yarns, by_factory)
        self.logger.info("NSM anomalies: %s rows", len(items))
        return NsmAnomalyResponse(items=[NsmAnomalyDTO(**i.model_dump()) for i in items])
