"""UC-20 Lấy NSM gợi ý từ sợi cùng nhóm (BR-37, BR-13)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import component_dto
from backend.features.yarn_costing.business.analysis_business import AnalysisBusiness
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.dto.pricing_dto import NsmSuggestionResponse, SuggestNsmRequest
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.repositories.factory_data_loader import load_factory_data
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

NOT_FOUND = "Chưa có sợi cùng nhóm để tự điền. Vui lòng nhập NSM."


class SuggestNsmService(BaseService[SuggestNsmRequest, NsmSuggestionResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.analysis = AnalysisBusiness()
        self.costing = CostingBusiness()

    def execute(self, request: SuggestNsmRequest) -> NsmSuggestionResponse:
        yarns = self.repository.list_all()
        yarn = next((y for y in yarns if y.yarn_code == request.yarn_code), None)
        if yarn is None:
            raise YarnNotFoundError(f"Không tìm thấy mã {request.yarn_code}.")
        reference = self.analysis.reference_yarn(yarn, yarns)
        if reference is None:
            self.logger.info("No reference yarn for %s", yarn.yarn_code)
            return NsmSuggestionResponse(found=False, message=NOT_FOUND)
        data = load_factory_data(yarn.factory_code)
        visible = {
            s.stage_code
            for s in self.costing.visible_stages(data, yarn.yarn_group, yarn.technology, yarn.nsm)
            if not s.is_carding
        }
        nsm = {code: value for code, value in reference.nsm.items() if code in visible}
        self.logger.info("Reference yarn for %s: %s (%s stages)", yarn.yarn_code, reference.yarn_code, len(nsm))
        return NsmSuggestionResponse(
            found=True,
            message=f"Đã điền NSM từ sợi {reference.yarn_code} - {reference.yarn_name}.",
            reference_yarn_code=reference.yarn_code,
            reference_yarn_name=reference.yarn_name,
            reference_count=reference.count,
            nsm=nsm,
            components=[component_dto(c, c.nsm_carding) for c in reference.components],
        )
