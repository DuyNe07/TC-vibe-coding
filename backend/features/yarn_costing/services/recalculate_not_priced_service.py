"""UC-43 Tính lại các mã chưa tính được (BR-65, dùng BR-64)."""

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.dto_builders import batch_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.recalc_business import RecalcBusiness
from backend.features.yarn_costing.dto.common_dto import RecalcResultResponse
from backend.features.yarn_costing.dto.master_dto import RecalculateNotPricedRequest
from backend.features.yarn_costing.models.enums import PriceEvent
from backend.features.yarn_costing.repositories.factory_data_loader import load_factory_data
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository, RecalcBatchRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class RecalculateNotPricedService(BaseService[RecalculateNotPricedRequest, RecalcResultResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.access = AccessBusiness()
        self.master = MasterBusiness()
        self.recalc = RecalcBusiness()

    def execute(self, request: RecalculateNotPricedRequest) -> RecalcResultResponse:
        factory = request.factory_code
        self.access.ensure_allowed(self.current_user, "UC-43", factory.value)
        self.master.require_date_and_reason(request.effective_date, request.reason)
        yarns = self.repository.list_all()
        waiting = self.recalc.not_priced(yarns, factory)
        self.logger.info("Recalculate not priced yarns of %s: %s waiting", factory, len(waiting))
        self.master.require(bool(waiting), f"Xưởng {factory.value} không có mã nào đang 'Chưa tính được'.")
        label = self.access.user_label(self.current_user)
        batch_repo = RecalcBatchRepository()
        codes = [b.batch_code for b in batch_repo.list_all()]
        outcome = self.recalc.recalculate_not_priced(
            yarns,
            load_factory_data(factory),
            utc_now(),
            request.effective_date,  # type: ignore[arg-type]
            changed_by=label,
            batch_id=self.recalc.batch_code(factory.value, codes),
            reason=request.reason,
        )
        self.repository.store(yarns, outcome.yarns)
        PriceHistoryRepository().add_many(outcome.history)
        batch = self.recalc.make_batch(
            factory, PriceEvent.TINH_LAI_CHUA_TINH, request.effective_date, request.reason, label, outcome, codes
        )  # type: ignore[arg-type]
        batch_repo.add(batch)
        priced = outcome.yarn_count - outcome.failed_yarn_count
        AuditLogRepository().add(
            self.access.audit_entry(
                self.current_user,
                "UC-43",
                factory.value,
                f"Tính lại {outcome.yarn_count} mã chưa tính được: {priced} mã đã có giá",
                request.reason,
            )
        )
        self.logger.info(
            "Not priced yarns of %s recalculated: %s yarns, %s priced, %s still waiting",
            factory,
            outcome.yarn_count,
            priced,
            outcome.failed_yarn_count,
        )
        return RecalcResultResponse(
            message=(
                f"Đã tính lại {outcome.yarn_count} mã chưa tính được của xưởng {factory.value}: "
                f"{priced} mã đã có giá, {outcome.failed_yarn_count} mã vẫn chưa tính được."
            ),
            batch=batch_dto(batch),
            batches=[batch_dto(batch)],
            recalculated_count=outcome.yarn_count,
            failed_count=outcome.failed_yarn_count,
            will_recalculate=True,
        )
