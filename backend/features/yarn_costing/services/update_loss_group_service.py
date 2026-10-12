"""UC-13 Sửa nhóm tiêu hao (BR-24: nhóm khoá chỉ Phòng SO; tính lại nhóm thứ cấp và mã bị ảnh hưởng)."""

from datetime import date

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.dto_builders import loss_group_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.display_business import format_percent
from backend.features.yarn_costing.business.loss_business import LossBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.name_business import collapse_spaces
from backend.features.yarn_costing.business.recalc_business import RecalcBusiness
from backend.features.yarn_costing.dto.loss_dto import LossGroupSaveResponse, UpdateLossGroupRequest
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.models.enums import GroupCode, LossGroupLevel, PriceEvent
from backend.features.yarn_costing.repositories.factory_data_loader import load_factory_data
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository, RecalcBatchRepository
from backend.features.yarn_costing.repositories.user_group_repository import UserGroupRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class UpdateLossGroupService(BaseService[UpdateLossGroupRequest, LossGroupSaveResponse]):
    def __init__(self, repository: LossGroupRepository | None = None) -> None:
        self.repository = repository or LossGroupRepository()
        self.access = AccessBusiness()
        self.business = LossBusiness()
        self.master = MasterBusiness()
        self.recalc = RecalcBusiness()

    def execute(self, request: UpdateLossGroupRequest) -> LossGroupSaveResponse:
        a, factory = request.actor, request.factory_code
        group = self.access.verify(
            a.group_code, a.access_code, a.person_name, UserGroupRepository().list_all(), "UC-13", factory.value
        )
        data = load_factory_data(factory)
        current = data.loss_groups.get(request.group_key)
        if current is None:
            raise YarnNotFoundError(f"Không tìm thấy nhóm tiêu hao '{request.group_key}' ở xưởng {factory.value}.")
        yarn_repo = YarnRepository()
        yarns = yarn_repo.list_all()
        groups = list(data.loss_groups.values())
        affected = self.business.affected_groups(current.group_key, groups)
        locked = self.business.locked_codes(affected, factory.value, yarns)
        self.business.ensure_can_edit(current.group_key, locked, group.code == GroupCode.SO)
        self.master.require(bool(request.reason.strip()), "Vui lòng nhập lý do.")
        label = self.access.actor_label(group, a.person_name)
        update: dict = {
            "material": collapse_spaces(request.material),
            "technology": request.technology,
            "updated_by": label,
        }
        if request.components:
            components = self.business.check_component_rows(
                current.group_key, [(c.component_group_key, c.ratio) for c in request.components], groups
            )
            update |= {"components": components, "level": LossGroupLevel.THU_CAP}
            update["losses"] = self.business.secondary_losses(components, data.loss_groups, data.stages)
        elif request.losses is not None and current.level != LossGroupLevel.THU_CAP:
            values = {k: v for k, v in request.losses.items() if v is not None}
            self.business.ensure_valid_group(current.group_key, factory.value, False, values)
            update["losses"] = self.business.manual_losses(values, data.nsm_stage_codes)
        updated = current.model_copy(update=update)
        by_key = {**data.loss_groups, updated.group_key: updated}
        recomputed = self.business.recompute_secondaries(list(by_key.values()), data.stages)
        by_key.update({g.group_key: g for g in recomputed})
        self.repository.save_many([updated, *recomputed])
        data = data.model_copy(update={"loss_groups": by_key})
        affected = self.business.affected_groups(updated.group_key, list(by_key.values()))
        batch_repo = RecalcBatchRepository()
        codes = [b.batch_code for b in batch_repo.list_all()]
        effective = request.effective_date or date.today()
        outcome = self.recalc.recalculate(
            yarns,
            data,
            PriceEvent.SUA_TIEU_HAO,
            utc_now(),
            effective,
            selector=lambda y: y.loss_group_key in affected,
            changed_by=label,
            batch_id=self.recalc.batch_code(factory.value, codes),
            reason=request.reason,
        )
        yarn_repo.store(yarns, outcome.yarns)
        PriceHistoryRepository().add_many(outcome.history)
        batch = self.recalc.make_batch(
            factory, PriceEvent.SUA_TIEU_HAO, effective, request.reason, label, outcome, codes
        )
        batch_repo.add(batch)
        locked_count = sum(1 for y in outcome.yarns if y.is_locked)
        stage_codes = sorted(set(current.losses) | set(updated.losses))
        detail = "; ".join(
            f"{c}: {format_percent(current.loss_at(c))}% → {format_percent(updated.loss_at(c))}%"
            for c in stage_codes
            if current.loss_at(c) != updated.loss_at(c)
        )
        AuditLogRepository().add(
            self.access.audit_entry(
                group, a.person_name, "UC-13", f"{factory.value} / {updated.group_key}", detail, request.reason
            )
        )
        self.logger.info(
            "Loss group %s/%s updated; %s yarns recalculated (%s locked)",
            factory,
            updated.group_key,
            outcome.yarn_count,
            locked_count,
        )
        return LossGroupSaveResponse(
            message=(
                f"Đã sửa nhóm tiêu hao '{updated.group_key}'. Đã tính lại {outcome.yarn_count} mã "
                f"(trong đó {locked_count} mã đã có mã kế toán)."
            ),
            group=loss_group_dto(updated, [], locked, []),
            recalculated_count=outcome.yarn_count,
        )
