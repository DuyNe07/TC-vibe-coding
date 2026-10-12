"""UC-11 Khai báo nhóm tiêu hao sơ cấp (+ tính lại mã đang chờ tiêu hao, BR-40)."""

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.dto_builders import loss_group_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.loss_business import LossBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.name_business import collapse_spaces, group_key_of
from backend.features.yarn_costing.business.recalc_business import RecalcBusiness
from backend.features.yarn_costing.dto.loss_dto import CreatePrimaryLossGroupRequest, LossGroupSaveResponse
from backend.features.yarn_costing.models.enums import LossGroupLevel
from backend.features.yarn_costing.models.loss_group import LossGroup
from backend.features.yarn_costing.repositories.factory_data_loader import load_factory_data
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.user_group_repository import UserGroupRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class CreatePrimaryLossGroupService(BaseService[CreatePrimaryLossGroupRequest, LossGroupSaveResponse]):
    def __init__(self, repository: LossGroupRepository | None = None) -> None:
        self.repository = repository or LossGroupRepository()
        self.access = AccessBusiness()
        self.business = LossBusiness()
        self.master = MasterBusiness()
        self.recalc = RecalcBusiness()

    def execute(self, request: CreatePrimaryLossGroupRequest) -> LossGroupSaveResponse:
        a, factory = request.actor, request.factory_code
        group = self.access.verify(
            a.group_code, a.access_code, a.person_name, UserGroupRepository().list_all(), "UC-11", factory.value
        )
        key = group_key_of(request.yarn_group_label)
        self.master.require(bool(key), "Vui lòng nhập nhóm sợi.")
        data = load_factory_data(factory)
        losses = self.business.manual_losses(request.losses, data.nsm_stage_codes)
        self.business.ensure_valid_group(
            key, factory.value, key in data.loss_groups, {k: v for k, v in request.losses.items() if v is not None}
        )
        label = self.access.actor_label(group, a.person_name)
        new_group = LossGroup(
            factory_code=factory,
            group_key=key,
            yarn_group_label=collapse_spaces(request.yarn_group_label),
            material=collapse_spaces(request.material),
            technology=request.technology,
            level=LossGroupLevel.SO_CAP,
            losses=losses,
            updated_by=label,
        )
        self.repository.add(new_group)
        data = data.model_copy(update={"loss_groups": {**data.loss_groups, key: new_group}})
        yarn_repo = YarnRepository()
        yarns = yarn_repo.list_all()
        outcome = self.recalc.recalculate_waiting(yarns, data, key, utc_now(), changed_by=label)
        yarn_repo.store(yarns, outcome.yarns)
        PriceHistoryRepository().add_many(outcome.history)
        AuditLogRepository().add(
            self.access.audit_entry(group, a.person_name, "UC-11", f"{factory.value} / {key}", f"Tiêu hao: {losses}")
        )
        self.logger.info(
            "Primary loss group %s/%s created; %s waiting yarns recalculated", factory, key, outcome.yarn_count
        )
        return LossGroupSaveResponse(
            message=f"Đã thêm nhóm tiêu hao '{key}'. Đã tính lại {outcome.yarn_count} mã đang chờ tiêu hao.",
            group=loss_group_dto(new_group, [], [], []),
            recalculated_count=outcome.yarn_count,
        )
