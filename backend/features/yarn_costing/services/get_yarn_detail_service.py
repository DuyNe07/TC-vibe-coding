"""UC-22 Xem chi tiết tính giá và lịch sử."""

from datetime import date

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import (
    component_dto,
    history_dto,
    line_dto,
    stage_cost_dto,
    summary_dto,
    yarn_dto,
)
from backend.features.yarn_costing.business.analysis_business import AnalysisBusiness
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.business.price_line_business import PriceLineBusiness
from backend.features.yarn_costing.business.pricing_business import PricingBusiness
from backend.features.yarn_costing.dto.pricing_dto import GetYarnDetailRequest, StageInputDTO, YarnDetailResponse
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.repositories.exchange_rate_repository import ExchangeRateRepository
from backend.features.yarn_costing.repositories.factory_data_loader import load_factory_data
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class GetYarnDetailService(BaseService[GetYarnDetailRequest, YarnDetailResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.costing = CostingBusiness()
        self.analysis = AnalysisBusiness()
        self.lines = PriceLineBusiness()
        self.pricing = PricingBusiness()

    def execute(self, request: GetYarnDetailRequest) -> YarnDetailResponse:
        yarns = self.repository.list_all()
        yarn = None
        if request.line_code:
            yarn = next((y for y in yarns if y.line(request.line_code) is not None), None)
        if yarn is None and request.yarn_code:
            yarn = next((y for y in yarns if y.yarn_code == request.yarn_code), None)
        if yarn is None:
            raise YarnNotFoundError(f"Không tìm thấy mã {request.line_code or request.yarn_code or ''}.")
        data = load_factory_data(yarn.factory_code)
        rate = self.costing.current_exchange_rate(ExchangeRateRepository().list_all(), date.today())
        rate_value = rate.rate if rate else None
        reference = next(
            (y for y in yarns if y.yarn_code == yarn.reference_yarn_code), None
        ) or self.analysis.reference_yarn(yarn, yarns)
        stages = [
            StageInputDTO(
                stage_code=s.stage_code,
                stage_name=s.stage_name,
                nsm=None if s.is_packaging else yarn.nsm_at(s.stage_code),
                reference_nsm=reference.nsm_at(s.stage_code) if reference and not s.is_packaging else None,
            )
            for s in self.costing.visible_stages(data, yarn.yarn_group, yarn.technology, yarn.nsm)
            if not s.is_carding
        ]
        reference_carding = self.analysis.carding_nsm(reference) if reference else {}
        own = yarn.components or self.pricing.default_components(yarn, data)
        components = [
            component_dto(c, reference_carding.get(key, ("", None))[1] if (key := self.analysis.pair_key(c)) else None)
            for c in own
        ]
        line_codes = (
            {request.line_code}
            if request.line_code and yarn.line(request.line_code)
            else {x.line_code for x in yarn.lines}
        )
        history = sorted(
            PriceHistoryRepository().find(lambda h: h.yarn_code == yarn.yarn_code and h.line_code in line_codes),
            key=lambda h: h.changed_at,
            reverse=True,
        )
        revisions = sorted(
            (y for y in yarns if y.base_code == yarn.base_code and y.id != yarn.id), key=lambda y: y.revision_no
        )
        packaging = data.packaging.get(yarn.packaging_code or "")
        self.logger.info("Detail of %s: %s lines, %s history rows", yarn.yarn_code, len(yarn.lines), len(history))
        return YarnDetailResponse(
            yarn=yarn_dto(yarn, rate_value, packaging.name if packaging else ""),
            stages=stages,
            stage_details=[stage_cost_dto(d) for d in yarn.stage_details],
            lines=[line_dto(yarn, x, rate_value) for x in self.lines.sorted_lines(yarn.lines)],
            revisions=[summary_dto(y, rate_value) for y in revisions],
            history=[history_dto(h) for h in history],
            carding_stages=data.carding_codes,
            components=components,
            material_options=self.pricing.material_options(yarn, data),
            reference_yarn_code=reference.yarn_code if reference else None,
        )
