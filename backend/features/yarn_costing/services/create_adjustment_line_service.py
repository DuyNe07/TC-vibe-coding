"""UC-25 Tạo dòng chiết khấu / phụ phí (BR-31, BR-34)."""

from datetime import date

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import line_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.business.display_business import format_vnd
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.price_line_business import ADJUSTMENT_TYPES, PriceLineBusiness
from backend.features.yarn_costing.dto.price_dto import CreateAdjustmentLineRequest, PriceLineResponse
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.models.costing import AdjustmentInput
from backend.features.yarn_costing.models.enums import PriceEvent
from backend.features.yarn_costing.repositories.exchange_rate_repository import ExchangeRateRepository
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.user_group_repository import UserGroupRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class CreateAdjustmentLineService(BaseService[CreateAdjustmentLineRequest, PriceLineResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.access = AccessBusiness()
        self.lines = PriceLineBusiness()
        self.master = MasterBusiness()
        self.costing = CostingBusiness()

    def execute(self, request: CreateAdjustmentLineRequest) -> PriceLineResponse:
        a = request.actor
        yarns = self.repository.list_all()
        yarn = next((y for y in yarns if y.yarn_code == request.yarn_code), None)
        if yarn is None:
            raise YarnNotFoundError(f"Không tìm thấy mã {request.yarn_code}.")
        group = self.access.verify(
            a.group_code,
            a.access_code,
            a.person_name,
            UserGroupRepository().list_all(),
            "UC-25",
            yarn.factory_code.value,
        )
        self.master.require(request.line_type in ADJUSTMENT_TYPES, "Vui lòng chọn Chiết khấu hoặc Phụ phí.")
        self.master.require(
            yarn.regular_line is not None, f"Mã {yarn.yarn_code} chưa có giá, chưa tạo được dòng CK/PP."
        )
        data = AdjustmentInput(percent=request.percent, reason=request.reason, order_ref=request.order_ref)
        self.lines.ensure_adjustment_valid(data)
        label = self.access.actor_label(group, a.person_name)
        updated, line = self.lines.new_adjustment_line(yarn, request.line_type, data, label)
        entry = self.lines.history(
            updated,
            line,
            PriceEvent.TINH_LAN_DAU,
            None,
            changed_by=label,
            effective_date=date.today(),
            reason=data.reason,
        )
        self.repository.store(yarns, [updated])
        PriceHistoryRepository().add_many([entry])
        AuditLogRepository().add(
            self.access.audit_entry(
                group,
                a.person_name,
                "UC-25",
                line.line_code,
                f"{request.line_type.value} {request.percent} - {request.order_ref}",
                request.reason,
            )
        )
        rate = self.costing.current_exchange_rate(ExchangeRateRepository().list_all(), date.today())
        self.logger.info("Adjustment line %s created (%s)", line.line_code, request.percent)
        return PriceLineResponse(
            message=f"Đã tạo dòng {line.line_code}: {format_vnd(line.total_vnd)} VND/kg.",
            line=line_dto(updated, line, rate.rate if rate else None),
        )
