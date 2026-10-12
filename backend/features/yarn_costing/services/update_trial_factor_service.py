"""UC-09 Cập nhật hệ số thí nghiệm (cập nhật dòng thí nghiệm của cả hai xưởng)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import batch_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.price_line_business import PriceLineBusiness
from backend.features.yarn_costing.business.recalc_business import RecalcBusiness
from backend.features.yarn_costing.dto.common_dto import RecalcResultResponse
from backend.features.yarn_costing.dto.master_dto import UpdateTrialFactorRequest
from backend.features.yarn_costing.models.costing import RecalcOutcome
from backend.features.yarn_costing.models.enums import FactoryCode, PriceEvent
from backend.features.yarn_costing.repositories.exchange_rate_repository import SettingsRepository
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository, RecalcBatchRepository
from backend.features.yarn_costing.repositories.user_group_repository import UserGroupRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


def factor_text(value: object) -> str:
    return (
        format(value, "f").rstrip("0").rstrip(".").replace(".", ",")
        if "." in format(value, "f")
        else format(value, "f")
    )


class UpdateTrialFactorService(BaseService[UpdateTrialFactorRequest, RecalcResultResponse]):
    def __init__(self, repository: SettingsRepository | None = None) -> None:
        self.repository = repository or SettingsRepository()
        self.access = AccessBusiness()
        self.master = MasterBusiness()
        self.lines = PriceLineBusiness()
        self.recalc = RecalcBusiness()

    def execute(self, request: UpdateTrialFactorRequest) -> RecalcResultResponse:
        a = request.actor
        group = self.access.verify(
            a.group_code, a.access_code, a.person_name, UserGroupRepository().list_all(), "UC-09"
        )
        self.master.ensure_positive(request.trial_factor, "Hệ số thí nghiệm phải lớn hơn 0.")
        self.master.require_date_and_reason(request.effective_date, request.reason)
        settings = self.repository.get_settings()
        old_factor, new_factor = settings.trial_factor, request.trial_factor
        self.repository.update(
            settings.model_copy(
                update={"trial_factor": new_factor, "trial_factor_effective_date": request.effective_date}
            )
        )
        label = self.access.actor_label(group, a.person_name)
        yarn_repo = YarnRepository()
        yarns = yarn_repo.list_all()
        batch_repo = RecalcBatchRepository()
        codes = [b.batch_code for b in batch_repo.list_all()]
        changed, history, batches = [], [], []
        for factory in FactoryCode:
            code = self.recalc.batch_code(factory.value, codes)
            entries_before = len(history)
            count = 0
            for yarn in yarns:
                if yarn.factory_code != factory or yarn.regular_line is None:
                    continue
                updated, entries = self.lines.apply_trial_factor(
                    yarn,
                    new_factor,
                    changed_by=label,
                    batch_id=code,
                    effective_date=request.effective_date,
                    reason=request.reason,  # type: ignore[arg-type]
                )
                count += 1
                if entries:
                    changed.append(updated)
                    history.extend(entries)
            outcome = RecalcOutcome(
                yarn_count=count, changed_line_count=len(history) - entries_before, line_count=count
            )
            batch = self.recalc.make_batch(
                factory, PriceEvent.DOI_HE_SO_TN, request.effective_date, request.reason, label, outcome, codes
            )  # type: ignore[arg-type]
            codes.append(batch.batch_code)
            batches.append(batch)
        yarn_repo.store(yarns, changed)
        PriceHistoryRepository().add_many(history)
        for batch in batches:
            batch_repo.add(batch)
        AuditLogRepository().add(
            self.access.audit_entry(
                group, a.person_name, "UC-09", "Hệ số thí nghiệm", f"{old_factor} → {new_factor}", request.reason
            )
        )
        self.logger.info("Trial factor %s -> %s; %s trial lines updated", old_factor, new_factor, len(history))
        return RecalcResultResponse(
            message=f"Đã đổi hệ số thí nghiệm từ {factor_text(old_factor)} thành {factor_text(new_factor)}. Đã cập nhật {len(history)} dòng thí nghiệm.",
            batch=batch_dto(batches[-1]),
            batches=[batch_dto(b) for b in batches],
            recalculated_count=len(history),
            old_value=old_factor,
        )
