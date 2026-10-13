"""UC-21 Nhập NSM, kiểm tra và lưu giá (xem trước khi save=False)."""

from datetime import date

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.dto_builders import components_from_rows
from backend.features.yarn_costing.builders.pricing_result_builder import PricingResultBuilder
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.business.price_line_business import PriceLineBusiness
from backend.features.yarn_costing.business.pricing_business import PricingBusiness
from backend.features.yarn_costing.dto.pricing_dto import PricingResultResponse, SaveYarnNsmRequest
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.models.enums import PriceEvent
from backend.features.yarn_costing.repositories.exchange_rate_repository import ExchangeRateRepository
from backend.features.yarn_costing.repositories.factory_data_loader import load_factory_data
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class SaveYarnNsmService(BaseService[SaveYarnNsmRequest, PricingResultResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.access = AccessBusiness()
        self.pricing = PricingBusiness()
        self.lines = PriceLineBusiness()
        self.costing = CostingBusiness()

    def execute(self, request: SaveYarnNsmRequest) -> PricingResultResponse:
        yarn_repo = self.repository
        yarns = yarn_repo.list_all()
        yarn = next((y for y in yarns if y.yarn_code == request.yarn_code), None)
        if yarn is None:
            raise YarnNotFoundError(f"Không tìm thấy mã {request.yarn_code}.")
        self.access.ensure_allowed(self.current_user, "UC-21", yarn.factory_code.value)
        self.pricing.ensure_status(yarn)
        data = load_factory_data(yarn.factory_code)
        preview = self.pricing.preview(
            yarn, components_from_rows(request.components), request.nsm, data, yarns, request.reference_yarn_code
        )
        rate = self.costing.current_exchange_rate(ExchangeRateRepository().list_all(), date.today())
        rate_value = rate.rate if rate else None
        if not request.save:
            self.logger.info(
                "NSM of %s checked (passed=%s, warnings=%s)",
                yarn.yarn_code,
                preview.result.passed,
                preview.warning_stages,
            )
            return PricingResultBuilder(
                preview, None, data.trial_factor, rate_value, self.pricing.message(preview, rate_value, saved=False)
            ).build()
        self.pricing.ensure_can_save(preview, request.nsm_warning_reason)
        label = self.access.user_label(self.current_user)
        now = utc_now()
        event = PriceEvent.SUA_NSM if yarn.regular_line is not None else PriceEvent.TINH_LAN_DAU
        candidate = preview.candidate.model_copy(
            update={
                "nsm_mode": request.nsm_mode,
                "reference_yarn_code": preview.reference_yarn_code,
                "nsm_warning_reason": request.nsm_warning_reason.strip() if preview.warning_stages else "",
                "handled_by": yarn.handled_by or label,
                "handled_at": yarn.handled_at or now,
            }
        )
        saved, history = self.lines.apply_result(
            candidate, preview.result, data.trial_factor, event, now, date.today(), changed_by=label
        )
        yarn_repo.store(yarns, [saved])
        PriceHistoryRepository().add_many(history)
        detail = f"NSM: {dict(yarn.nsm)} → {dict(saved.nsm)}; thành phần: {len(saved.components)}; trạng thái: {yarn.status.value} → {saved.status.value}"
        AuditLogRepository().add(
            self.access.audit_entry(self.current_user, "UC-21", yarn.yarn_code, detail, request.nsm_warning_reason)
        )
        self.logger.info("NSM of %s saved (status=%s, history=%s)", yarn.yarn_code, saved.status, len(history))
        return PricingResultBuilder(
            preview, saved, data.trial_factor, rate_value, self.pricing.message(preview, rate_value, saved=True)
        ).build()
