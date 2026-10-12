"""UC-24 Tạo bản ĐCNSM (BR-33; bản gốc giữ nguyên)."""

from datetime import date

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.dto_builders import components_from_rows
from backend.features.yarn_costing.builders.pricing_result_builder import PricingResultBuilder
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.business.display_business import format_vnd
from backend.features.yarn_costing.business.price_line_business import PriceLineBusiness
from backend.features.yarn_costing.business.pricing_business import PricingBusiness
from backend.features.yarn_costing.business.request_business import RequestBusiness
from backend.features.yarn_costing.dto.pricing_dto import CreateNsmRevisionRequest, PricingResultResponse
from backend.features.yarn_costing.exceptions import YarnNotFoundError, YarnValidationError
from backend.features.yarn_costing.models.enums import NsmMode, PriceEvent, YarnOrigin, YarnStatus
from backend.features.yarn_costing.models.yarn import Yarn
from backend.features.yarn_costing.repositories.exchange_rate_repository import ExchangeRateRepository
from backend.features.yarn_costing.repositories.factory_data_loader import load_factory_data
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.user_group_repository import UserGroupRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

SOURCE_STATUSES = (YarnStatus.DA_TINH_GIA, YarnStatus.CO_MA_KE_TOAN, YarnStatus.CHUA_TINH_DUOC)


class CreateNsmRevisionService(BaseService[CreateNsmRevisionRequest, PricingResultResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.access = AccessBusiness()
        self.pricing = PricingBusiness()
        self.lines = PriceLineBusiness()
        self.costing = CostingBusiness()
        self.requests = RequestBusiness()

    def execute(self, request: CreateNsmRevisionRequest) -> PricingResultResponse:
        a = request.actor
        yarns = self.repository.list_all()
        source = next((y for y in yarns if y.yarn_code == request.source_yarn_code), None)
        if source is None:
            raise YarnNotFoundError(f"Không tìm thấy mã {request.source_yarn_code}.")
        group = self.access.verify(
            a.group_code,
            a.access_code,
            a.person_name,
            UserGroupRepository().list_all(),
            "UC-24",
            source.factory_code.value,
        )
        if source.status not in SOURCE_STATUSES:
            raise YarnValidationError(
                f"Mã {source.yarn_code} đang ở trạng thái '{source.status.value}', chưa tạo được bản ĐCNSM."
            )
        code, number = self.requests.next_revision(source.base_code, yarns)
        label = self.access.actor_label(group, a.person_name)
        now = utc_now()
        draft = Yarn(
            **source.model_dump(
                include={
                    "factory_code",
                    "base_code",
                    "yarn_name",
                    "yarn_group",
                    "count",
                    "loss_group_key",
                    "technology",
                    "is_compact",
                    "packaging_code",
                }
            ),
            yarn_code=code,
            revision_no=number,
            origin=YarnOrigin.DCNSM,
            status=YarnStatus.CHUA_TINH_DUOC,
            adjust_reason=request.adjust_reason.strip(),
            nsm_mode=NsmMode.TU_NHAP,
            requested_by=label,
            handled_by=label,
            handled_at=now,
        )
        data = load_factory_data(source.factory_code)
        preview = self.pricing.preview(
            draft,
            components_from_rows(request.components),
            request.nsm,
            data,
            yarns,
            adjust_reason=request.adjust_reason,
        )
        rate = self.costing.current_exchange_rate(ExchangeRateRepository().list_all(), date.today())
        rate_value = rate.rate if rate else None
        if not request.save:
            self.logger.info("Revision %s of %s checked (passed=%s)", code, source.yarn_code, preview.result.passed)
            return PricingResultBuilder(
                preview, None, data.trial_factor, rate_value, self.pricing.message(preview, rate_value, False)
            ).build()
        self.pricing.ensure_can_save(preview, request.nsm_warning_reason)
        candidate = preview.candidate.model_copy(
            update={
                "reference_yarn_code": preview.reference_yarn_code,
                "nsm_warning_reason": request.nsm_warning_reason.strip(),
            }
        )
        saved, history = self.lines.apply_result(
            candidate, preview.result, data.trial_factor, PriceEvent.TINH_LAN_DAU, now, date.today(), changed_by=label
        )
        self.repository.store(yarns, [saved])
        PriceHistoryRepository().add_many(history)
        AuditLogRepository().add(
            self.access.audit_entry(
                group, a.person_name, "UC-24", code, f"Bản ĐCNSM của {source.yarn_code}", request.adjust_reason
            )
        )
        self.logger.info("Revision %s created from %s (status=%s)", code, source.yarn_code, saved.status)
        if preview.result.passed:
            message = f"Đã tạo bản {code}: {format_vnd(preview.result.cost.total)} VND/kg."
        else:
            message = self.pricing.message(preview, rate_value, True)
        return PricingResultBuilder(preview, saved, data.trial_factor, rate_value, message).build()
