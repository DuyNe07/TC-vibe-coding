"""UC-06 Khai báo hồi phế (+ tính lại toàn bộ xưởng)."""

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.dto_builders import batch_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.recalc_business import RecalcBusiness
from backend.features.yarn_costing.dto.common_dto import RecalcResultResponse
from backend.features.yarn_costing.dto.master_dto import SaveRecoveryRatesRequest
from backend.features.yarn_costing.models.enums import PriceEvent, RecoveryType
from backend.features.yarn_costing.models.recovery_rate import RecoveryRate
from backend.features.yarn_costing.repositories.factory_data_loader import load_factory_data
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository, RecalcBatchRepository
from backend.features.yarn_costing.repositories.recovery_rate_repository import RecoveryRateRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class SaveRecoveryRatesService(BaseService[SaveRecoveryRatesRequest, RecalcResultResponse]):
    def __init__(self, repository: RecoveryRateRepository | None = None) -> None:
        self.repository = repository or RecoveryRateRepository()
        self.access = AccessBusiness()
        self.master = MasterBusiness()
        self.recalc = RecalcBusiness()

    def execute(self, request: SaveRecoveryRatesRequest) -> RecalcResultResponse:
        factory = request.factory_code
        self.access.ensure_allowed(self.current_user, "UC-06", factory.value)
        rows = [r for r in request.rows if r.recovery_type != RecoveryType.KHONG]
        for r in rows:
            self.master.ensure_recovery_rate(r.rate if r.rate is not None else -1)  # type: ignore[arg-type]
        self.master.require_date_and_reason(request.effective_date, request.reason)
        old = {r.recovery_type: r for r in self.repository.for_factory(factory.value)}
        details = []
        items = []
        for r in rows:
            current = old.get(r.recovery_type)
            details.append(f"{r.recovery_type.value}: {current.rate if current else '-'} → {r.rate}")
            item = (
                current.model_copy(update={"rate": r.rate})
                if current
                else RecoveryRate(factory_code=factory, recovery_type=r.recovery_type, rate=r.rate)
            )  # type: ignore[arg-type]
            items.append(item)
        self.repository.save_many(items)
        label = self.access.user_label(self.current_user)
        yarn_repo = YarnRepository()
        yarns = yarn_repo.list_all()
        batch_repo = RecalcBatchRepository()
        codes = [b.batch_code for b in batch_repo.list_all()]
        outcome = self.recalc.recalculate(
            yarns,
            load_factory_data(factory),
            PriceEvent.DOI_DU_LIEU_NEN,
            utc_now(),
            request.effective_date,  # type: ignore[arg-type]
            changed_by=label,
            batch_id=self.recalc.batch_code(factory.value, codes),
            reason=request.reason,
        )
        yarn_repo.store(yarns, outcome.yarns)
        PriceHistoryRepository().add_many(outcome.history)
        batch = self.recalc.make_batch(
            factory, PriceEvent.DOI_DU_LIEU_NEN, request.effective_date, request.reason, label, outcome, codes
        )  # type: ignore[arg-type]
        batch_repo.add(batch)
        AuditLogRepository().add(
            self.access.audit_entry(self.current_user, "UC-06", factory.value, "; ".join(details), request.reason)
        )
        self.logger.info("Recovery rates %s saved; recalculated %s yarns", factory, outcome.yarn_count)
        return RecalcResultResponse(
            message=f"Đã lưu hồi phế {factory.value}. Đã tính lại {outcome.yarn_count} mã, {outcome.failed_yarn_count} mã chưa tính được.",
            batch=batch_dto(batch),
            batches=[batch_dto(batch)],
            recalculated_count=outcome.yarn_count,
            failed_count=outcome.failed_yarn_count,
        )
