"""UC-10 Tra cứu tiêu hao."""

from collections import defaultdict

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import loss_group_dto
from backend.features.yarn_costing.business.loss_business import LossBusiness
from backend.features.yarn_costing.dto.loss_dto import ListLossGroupsRequest, LossGroupListResponse
from backend.features.yarn_costing.models.enums import YarnStatus
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.stage_repository import StageRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

CLOSED = (YarnStatus.DA_HUY, YarnStatus.TU_CHOI)


class ListLossGroupsService(BaseService[ListLossGroupsRequest, LossGroupListResponse]):
    def __init__(self, repository: LossGroupRepository | None = None) -> None:
        self.repository = repository or LossGroupRepository()
        self.business = LossBusiness()

    def execute(self, request: ListLossGroupsRequest) -> LossGroupListResponse:
        factory = request.factory_code.value
        groups = self.repository.for_factory(factory)
        index = self.business.parent_index(groups)
        used: dict[str, list[str]] = defaultdict(list)
        locked: dict[str, list[str]] = defaultdict(list)
        affected_statuses = (YarnStatus.DA_TINH_GIA, YarnStatus.CO_MA_KE_TOAN, YarnStatus.CHUA_TINH_DUOC)
        for y in YarnRepository().list_all():
            if y.factory_code.value != factory:
                continue
            if y.status not in CLOSED:
                used[y.loss_group_key].append(y.yarn_code)
            if y.status in affected_statuses and y.is_locked:
                locked[y.loss_group_key].append(y.yarn_code)
        keyword = request.keyword.strip().casefold()
        items = []
        for g in groups:
            if request.level is not None and g.level != request.level:
                continue
            if keyword and keyword not in f"{g.group_key} {g.yarn_group_label} {g.material}".casefold():
                continue
            affected = self.business.affected_from_index(g.group_key, index)
            locked_codes = sorted(code for key in affected for code in locked.get(key, []))
            if request.locked_only and not locked_codes:
                continue
            items.append(
                loss_group_dto(g, sorted(used.get(g.group_key, [])), locked_codes, sorted(index.get(g.group_key, [])))
            )
        stage_codes = [s.stage_code for s in StageRepository().for_factory(factory) if not s.is_packaging]
        self.logger.info(
            "Loss groups %s: %s of %s (level=%s, keyword=%r)",
            factory,
            len(items),
            len(groups),
            request.level,
            request.keyword,
        )
        return LossGroupListResponse(items=items, stage_codes=stage_codes)
