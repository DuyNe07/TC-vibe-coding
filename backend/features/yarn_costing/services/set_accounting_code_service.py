"""UC-28 Nhập / sửa / xoá mã kế toán (BR-32 khoá + trạng thái)."""

from datetime import date

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.dto_builders import line_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.price_line_business import PriceLineBusiness
from backend.features.yarn_costing.constants import ACCOUNTING_CODE_MAX
from backend.features.yarn_costing.dto.price_dto import PriceLineResponse, SetAccountingCodeRequest
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.repositories.exchange_rate_repository import ExchangeRateRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class SetAccountingCodeService(BaseService[SetAccountingCodeRequest, PriceLineResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.access = AccessBusiness()
        self.lines = PriceLineBusiness()
        self.master = MasterBusiness()
        self.costing = CostingBusiness()

    def execute(self, request: SetAccountingCodeRequest) -> PriceLineResponse:
        yarns = self.repository.list_all()
        yarn = next((y for y in yarns if y.line(request.line_code) is not None), None)
        if yarn is None:
            raise YarnNotFoundError(f"Không tìm thấy dòng {request.line_code}.")
        self.access.ensure_allowed(self.current_user, "UC-28", yarn.factory_code.value)
        code = request.accounting_code.strip()
        self.master.require(len(code) <= ACCOUNTING_CODE_MAX, "Mã kế toán tối đa 100 ký tự.")
        old = yarn.line(request.line_code)
        label = self.access.user_label(self.current_user)
        new_line = old.model_copy(  # type: ignore[union-attr]
            update={
                "accounting_code": code or None,
                "accounting_code_by": label if code else "",
                "accounting_code_at": utc_now() if code else None,
            }
        )
        updated = yarn.model_copy(
            update={"lines": [new_line if x.line_code == request.line_code else x for x in yarn.lines]}
        )
        updated = updated.model_copy(update={"status": self.lines.status_for(updated)})
        self.repository.store(yarns, [updated])
        AuditLogRepository().add(
            self.access.audit_entry(
                self.current_user,
                "UC-28",
                request.line_code,
                f"{old.accounting_code or '(trống)'} → {code or '(trống)'}",
            )  # type: ignore[union-attr]
        )
        rate = self.costing.current_exchange_rate(ExchangeRateRepository().list_all(), date.today())
        self.logger.info(
            "Accounting code of %s set (%s); yarn %s status=%s",
            request.line_code,
            bool(code),
            yarn.yarn_code,
            updated.status,
        )
        message = (
            f"Đã lưu mã kế toán cho dòng {request.line_code}."
            if code
            else f"Đã xoá mã kế toán của dòng {request.line_code}."
        )
        return PriceLineResponse(message=message, line=line_dto(updated, new_line, rate.rate if rate else None))
