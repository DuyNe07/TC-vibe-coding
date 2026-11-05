"""UC-47 Đánh dấu / bỏ đánh dấu Không sản xuất (BR-72, BR-73, BR-74; bổ sung 2026-11-05)."""

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.not_produced_business import NotProducedBusiness
from backend.features.yarn_costing.business.recalc_business import RecalcBusiness
from backend.features.yarn_costing.dto.request_dto import NotProducedResponse, SetNotProducedRequest
from backend.features.yarn_costing.exceptions import YarnNotFoundError, YarnValidationError
from backend.features.yarn_costing.models.enums import PriceEvent
from backend.features.yarn_costing.repositories.factory_data_loader import load_factory_data
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

USE_CASE = "UC-47"


class SetNotProducedService(BaseService[SetNotProducedRequest, NotProducedResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.access = AccessBusiness()
        self.business = NotProducedBusiness()
        self.recalc = RecalcBusiness()

    def execute(self, request: SetNotProducedRequest) -> NotProducedResponse:
        yarns = self.repository.list_all()
        yarn = next((y for y in yarns if y.yarn_code == request.yarn_code), None)
        if yarn is None:
            raise YarnNotFoundError(f"Không tìm thấy mã {request.yarn_code}.")
        self.access.ensure_allowed(self.current_user, USE_CASE, yarn.factory_code.value)
        reason = self.business.clean_reason(request.reason)
        family = self.business.family(yarns, yarn)
        label = self.access.user_label(self.current_user)
        now = utc_now()
        base = family[0].yarn_code
        if request.not_produced:
            return self._mark(yarns, family, reason, label, now, base)
        return self._unmark(yarns, family, reason, label, now, base)

    def _mark(self, yarns, family, reason, label, now, base) -> NotProducedResponse:  # type: ignore[no-untyped-def]
        problem = self.business.mark_problem(family)
        if problem:
            raise YarnValidationError(problem)
        updated, history, removed = self.business.mark(family, reason, label, now)
        self.repository.store(yarns, updated)
        PriceHistoryRepository().add_many(history)
        codes = [y.yarn_code for y in updated]
        AuditLogRepository().add(
            self.access.audit_entry(
                self.current_user,
                USE_CASE,
                base,
                f"{', '.join(f'{y.yarn_code}: {y.status.value}' for y in family)} → Không sản xuất; gỡ {removed} dòng giá",
                reason,
            )
        )
        self.logger.info("Yarn %s marked not produced: %s versions, %s price lines removed", base, len(codes), removed)
        return NotProducedResponse(
            message=f"Đã đánh dấu Không sản xuất cho {base} ({len(codes)} bản, gỡ {removed} dòng giá).",
            yarn_codes=codes,
            removed_line_count=removed,
        )

    def _unmark(self, yarns, family, reason, label, now, base) -> NotProducedResponse:  # type: ignore[no-untyped-def]
        ready = self.business.to_recalculate(family)
        codes = {y.yarn_code for y in ready}
        outcome = self.recalc.recalculate(
            ready,
            load_factory_data(family[0].factory_code),
            PriceEvent.BO_KHONG_SAN_XUAT,
            now,
            now.date(),
            changed_by=label,
            reason=reason,
        )
        self.repository.store(yarns, outcome.yarns)
        PriceHistoryRepository().add_many(outcome.history)
        priced = outcome.yarn_count - outcome.failed_yarn_count
        AuditLogRepository().add(
            self.access.audit_entry(
                self.current_user,
                USE_CASE,
                base,
                f"Bỏ đánh dấu Không sản xuất: {', '.join(f'{y.yarn_code}: {y.status.value}' for y in outcome.yarns)}",
                reason,
            )
        )
        self.logger.info("Yarn %s unmarked: %s priced, %s not priced", base, priced, outcome.failed_yarn_count)
        return NotProducedResponse(
            message=(
                f"Đã bỏ đánh dấu Không sản xuất cho {base}: {priced} bản đã tính giá, "
                f"{outcome.failed_yarn_count} bản chưa tính được."
            ),
            yarn_codes=sorted(codes),
            priced_count=priced,
            failed_count=outcome.failed_yarn_count,
        )
