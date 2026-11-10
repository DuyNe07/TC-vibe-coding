"""UC-54 Đối chiếu giá app với giá thành kế toán (BR-82, BR-83; bổ sung 2026-11-10). Không lưu gì."""

from decimal import Decimal

from backend.core.base import BaseService
from backend.features.yarn_costing.business.accounting_cost_business import (
    CURRENT_PRICE,
    WARN_GAP,
    WARN_SMALL,
    AccountingCostBusiness,
)
from backend.features.yarn_costing.dto.sales_dto import (
    AccountingCompareRowDTO,
    AccountingComparisonResponse,
    AccountingMissingRowDTO,
    GetAccountingComparisonRequest,
)
from backend.features.yarn_costing.models.price_history import PriceHistory
from backend.features.yarn_costing.repositories.accounting_cost_repository import (
    AccountingCostLineRepository,
    AccountingCostMonthRepository,
)
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

TOP_GAPS = 20
HUNDRED = Decimal(100)


class GetAccountingComparisonService(BaseService[GetAccountingComparisonRequest, AccountingComparisonResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.business = AccountingCostBusiness()

    def execute(self, request: GetAccountingComparisonRequest) -> AccountingComparisonResponse:
        self.business.ensure_levels(request.small_kg, request.gap_percent)
        month = AccountingCostMonthRepository().current(request.period)
        if month is None:
            return AccountingComparisonResponse(period=request.period)
        lines = [
            line
            for line in AccountingCostLineRepository().for_month(month.id)
            if request.factory_code is None or line.factory_code == request.factory_code
        ]
        by_code = self.business.lines_by_code(self.repository.list_all())
        history: dict[str, list[PriceHistory]] = {}
        for entry in PriceHistoryRepository().list_all():
            history.setdefault(entry.line_code, []).append(entry)
        end = self.business.month_end(request.period)
        rows: list[AccountingCompareRowDTO] = []
        missing: list[AccountingMissingRowDTO] = []
        for line in sorted(lines, key=lambda x: (x.factory_code.value, x.accounting_code)):
            kt = line.conversion_unit_cost
            pairs = by_code.get(line.accounting_code.strip().upper(), [])
            if not pairs:
                missing.append(
                    AccountingMissingRowDTO(
                        factory_code=line.factory_code,
                        accounting_code=line.accounting_code,
                        product_name=line.product_name,
                        quantity=line.quantity,
                        accounting_conversion=kt,
                    )
                )
                continue
            yarn, price_line = pairs[0]
            cost, price_date = self.business.price_at(price_line, history.get(price_line.line_code, []), end)
            notes = [] if price_date else [CURRENT_PRICE]
            if len(pairs) > 1:
                notes.append(f"Mã kế toán có ở {len(pairs)} dòng giá")
            gap = self.business.gap_percent(cost.total, kt)
            amounts = line.amounts
            rows.append(
                AccountingCompareRowDTO(
                    factory_code=line.factory_code,
                    accounting_code=line.accounting_code,
                    product_name=line.product_name,
                    line_code=price_line.line_code,
                    yarn_name=yarn.yarn_name,
                    quantity=line.quantity,
                    app_total=cost.total,
                    app_price_date=price_date,
                    app_price_note="; ".join(notes),
                    accounting_conversion=kt,
                    difference=cost.total - kt,
                    difference_percent=gap,
                    app_labor=cost.labor,
                    app_depreciation=cost.depreciation,
                    app_electricity=cost.electricity,
                    app_materials=cost.materials,
                    app_overhead=cost.overhead,
                    kt_labor=line.unit(amounts.labor),
                    kt_depreciation=line.unit(amounts.depreciation),
                    kt_power=line.unit(amounts.power),
                    kt_materials=line.unit(amounts.materials),
                    kt_overhead=line.unit(amounts.overhead),
                    accounting_unit_cost=line.unit_cost,
                    warnings=self.business.warnings(line.quantity, gap, request.small_kg, request.gap_percent),
                )
            )
        normal = [r for r in rows if WARN_SMALL not in r.warnings]
        base = sum((r.accounting_conversion * r.quantity for r in normal), Decimal(0))
        weighted = sum((r.difference * r.quantity for r in normal), Decimal(0)) / base * HUNDRED if base > 0 else None
        shown = [
            r
            for r in rows
            if (not request.only_gap or WARN_GAP in r.warnings)
            and (not request.hide_small or WARN_SMALL not in r.warnings)
        ]
        shown.sort(key=lambda r: -abs(r.difference_percent) if r.difference_percent is not None else 0)
        top = sorted(
            (r for r in normal if r.difference_percent is not None),
            key=lambda r: -abs(r.difference_percent),  # type: ignore[arg-type]
        )[:TOP_GAPS]
        self.logger.info(
            "Accounting comparison %s (%s): %s matched, %s missing",
            request.period,
            request.factory_code,
            len(rows),
            len(missing),
        )
        return AccountingComparisonResponse(
            period=request.period,
            matched_count=len(rows),
            gap_count=sum(1 for r in rows if WARN_GAP in r.warnings),
            small_count=sum(1 for r in rows if WARN_SMALL in r.warnings),
            missing_count=len(missing),
            weighted_gap_percent=weighted,
            rows=shown,
            missing=missing,
            top_gaps=top,
        )
