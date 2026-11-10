"""UC-50 Dùng sợi có sẵn từ gợi ý (BR-79; bổ sung 2026-11-10)."""

from datetime import date

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import usd
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.business.customer_name_business import CustomerNameBusiness
from backend.features.yarn_costing.business.name_business import collapse_spaces
from backend.features.yarn_costing.dto.sales_dto import SimpleLineDTO, UseExistingYarnRequest, UseExistingYarnResponse
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.models.customer_name import CustomerYarnName
from backend.features.yarn_costing.repositories.customer_name_repository import CustomerYarnNameRepository
from backend.features.yarn_costing.repositories.exchange_rate_repository import ExchangeRateRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

USE_CASE = "UC-50"


def vnd_text(value: object) -> str:
    return f"{value:,.0f}".replace(",", ".") if value is not None else "-"


class UseExistingYarnService(BaseService[UseExistingYarnRequest, UseExistingYarnResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.access = AccessBusiness()
        self.aliases = CustomerNameBusiness()

    def execute(self, request: UseExistingYarnRequest) -> UseExistingYarnResponse:
        self.access.ensure_allowed(self.current_user, USE_CASE)
        yarns = self.repository.list_all()
        yarn = next((y for y in yarns if y.yarn_code == request.yarn_code), None)
        if yarn is None:
            raise YarnNotFoundError(f"Không tìm thấy sợi {request.yarn_code}.")
        base = next((y for y in yarns if y.yarn_code == yarn.base_code), yarn)
        rate = CostingBusiness().current_exchange_rate(ExchangeRateRepository().list_all(), date.today())
        lines = [
            SimpleLineDTO(
                line_code=line.line_code,
                line_type=line.line_type,
                total_vnd=line.total_vnd,
                usd_per_kg=usd(line.total_vnd, rate.rate if rate else None),
                accounting_code=line.accounting_code or "",
            )
            for line in yarn.lines
        ]
        customer, typed = collapse_spaces(request.customer_name), collapse_spaces(request.typed_name)
        repo = CustomerYarnNameRepository()
        existing = repo.list_all()
        same_as_standard = self.aliases.names.comparable_name(typed) == self.aliases.names.comparable_name(
            base.yarn_name
        )
        already = any(
            a.base_code == base.base_code
            and self.aliases.key(a.customer_name, a.customer_yarn_name) == self.aliases.key(customer, typed)
            for a in existing
        )
        regular = yarn.regular_line
        if not customer or not typed or same_as_standard or already:
            self.logger.info("Use existing yarn %s (no customer name saved)", yarn.yarn_code)
            return UseExistingYarnResponse(
                message=f"Sợi {yarn.yarn_code} - {yarn.yarn_name}: {vnd_text(regular.total_vnd if regular else None)} đ/kg.",
                yarn_code=yarn.yarn_code,
                yarn_name=yarn.yarn_name,
                lines=lines,
            )
        customer, typed, _ = self.aliases.check(base, customer, typed, "", existing)
        label = self.access.user_label(self.current_user)
        repo.add(
            CustomerYarnName(
                base_code=base.base_code, customer_name=customer, customer_yarn_name=typed, created_by=label
            )
        )
        AuditLogRepository().add(
            self.access.audit_entry(self.current_user, USE_CASE, base.base_code, f"+ {customer}: {typed}")
        )
        self.logger.info("Customer name %r of %r saved for %s", typed, customer, base.base_code)
        return UseExistingYarnResponse(
            message=f"Đã lưu tên '{typed}' của khách {customer} cho sợi {base.base_code}.",
            saved=True,
            yarn_code=yarn.yarn_code,
            yarn_name=yarn.yarn_name,
            lines=lines,
        )
