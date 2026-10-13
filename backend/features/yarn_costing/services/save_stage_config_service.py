"""UC-03 Sửa cấu hình công đoạn (+ tính lại toàn bộ xưởng)."""

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.dto_builders import batch_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.recalc_business import RecalcBusiness
from backend.features.yarn_costing.dto.common_dto import RecalcResultResponse
from backend.features.yarn_costing.dto.master_dto import SaveStageConfigRequest
from backend.features.yarn_costing.models.enums import PriceEvent
from backend.features.yarn_costing.models.stage import Stage
from backend.features.yarn_costing.repositories.factory_data_loader import load_factory_data
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository, RecalcBatchRepository
from backend.features.yarn_costing.repositories.stage_repository import StageRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class SaveStageConfigService(BaseService[SaveStageConfigRequest, RecalcResultResponse]):
    def __init__(self, repository: StageRepository | None = None) -> None:
        self.repository = repository or StageRepository()
        self.access = AccessBusiness()
        self.master = MasterBusiness()
        self.recalc = RecalcBusiness()

    def execute(self, request: SaveStageConfigRequest) -> RecalcResultResponse:
        factory = request.factory_code
        self.access.ensure_allowed(self.current_user, "UC-03", factory.value)
        self.master.require_date_and_reason(request.effective_date, request.reason)
        old = {s.stage_code: s for s in self.repository.for_factory(factory.value)}
        rows = [r for r in request.rows if r.stage_code and r.stage_code.strip()]
        self.master.require(
            all(r.sequence is not None and r.sequence >= 1 for r in rows),
            "Cấu hình công đoạn không hợp lệ: thiếu thứ tự công đoạn.",
        )
        stages = []
        for r in rows:
            code = r.stage_code.strip()
            values = r.model_dump(exclude={"factory_code"}) | {"stage_code": code, "factory_code": factory}
            values["stage_name"] = (r.stage_name or code).strip()
            values["stage_group"] = (r.stage_group or code).strip()
            values["cumulative_stages"] = [c.strip() for c in r.cumulative_stages if c.strip()]
            stage = Stage(**values)
            if code in old:
                stage = stage.model_copy(update={"id": old[code].id, "created_at": old[code].created_at})
            stages.append(stage)
        yarn_repo = YarnRepository()
        yarns = yarn_repo.list_all()
        used = {c for y in yarns if y.factory_code == factory for c, v in y.nsm.items() if v > 0}
        used |= {c.carding_stage for y in yarns if y.factory_code == factory for c in y.components if c.carding_stage}
        used |= {c for g in LossGroupRepository().for_factory(factory.value) for c, v in g.losses.items() if v != 0}
        self.master.ensure_valid_stages(factory.value, stages, used, set(old))
        for code, stage in old.items():
            if code not in {s.stage_code for s in stages}:
                self.repository.delete(stage.id)
        self.repository.save_many(stages)
        label = self.access.user_label(self.current_user)
        now = utc_now()
        data = load_factory_data(factory)
        batch_repo = RecalcBatchRepository()
        codes = [b.batch_code for b in batch_repo.list_all()]
        code = self.recalc.batch_code(factory.value, codes)
        outcome = self.recalc.recalculate(
            yarns,
            data,
            PriceEvent.DOI_DU_LIEU_NEN,
            now,
            request.effective_date,
            changed_by=label,
            batch_id=code,
            reason=request.reason,  # type: ignore[arg-type]
        )
        yarn_repo.store(yarns, outcome.yarns)
        PriceHistoryRepository().add_many(outcome.history)
        batch = self.recalc.make_batch(
            factory, PriceEvent.DOI_DU_LIEU_NEN, request.effective_date, request.reason, label, outcome, codes
        )  # type: ignore[arg-type]
        batch_repo.add(batch)
        AuditLogRepository().add(
            self.access.audit_entry(
                self.current_user,
                "UC-03",
                factory.value,
                f"{len(stages)} công đoạn; lần tính lại {batch.batch_code}",
                request.reason,
            )
        )
        self.logger.info(
            "Stage config %s saved (%s stages); recalculated %s yarns", factory, len(stages), outcome.yarn_count
        )
        return RecalcResultResponse(
            message=f"Đã lưu cấu hình công đoạn {factory.value}. Đã tính lại {outcome.yarn_count} mã, {outcome.failed_yarn_count} mã chưa tính được.",
            batch=batch_dto(batch),
            batches=[batch_dto(batch)],
            recalculated_count=outcome.yarn_count,
            failed_count=outcome.failed_yarn_count,
        )
