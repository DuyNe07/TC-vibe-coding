"""UC-27 list: BR-52 visibility, filters, KPI tiles, warning text (BR-14, BR-28); UC-30 tasks."""

from collections.abc import Sequence
from datetime import date

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.core.current_user import CurrentUser
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.models.costsheet import Costsheet
from backend.features.woven_costing.models.enums import CostsheetStatus
from backend.features.woven_costing.models.list_filter import CostsheetFilter, CostsheetKpis

S = CostsheetStatus


class ListBusiness(BaseBusiness[Costsheet]):
    def rules(self) -> Sequence[BaseBusinessRule[Costsheet]]:
        return ()

    def matches(self, sheet: Costsheet, f: CostsheetFilter) -> bool:
        keyword = f.keyword.strip().casefold()
        text = f"{sheet.costsheet_no} {sheet.tcfno} {sheet.oc_no} {sheet.style}".casefold()
        checks = (
            not keyword or keyword in text,
            not f.statuses or sheet.status in f.statuses,
            not f.team or sheet.team == f.team,
            not f.sales_username or sheet.sales_username == f.sales_username,
            not f.customer_name or sheet.customer_name == f.customer_name,
            not f.dye_plant or sheet.dye_plant == f.dye_plant,
            not f.order_type or sheet.order_type == f.order_type,
            not f.price_type or sheet.price_type == f.price_type,
            not f.date_from or sheet.costing_date >= f.date_from,
            not f.date_to or sheet.costing_date <= f.date_to,
            not f.below_threshold_only or sheet.result.below_threshold,
        )
        return all(checks)

    def visible(self, sheets: list[Costsheet], user: CurrentUser | None) -> list[Costsheet]:
        """BR-52."""
        access = AccessBusiness()
        return [s for s in sheets if access.can_view(user, s)]

    def filter(self, sheets: list[Costsheet], f: CostsheetFilter, user: CurrentUser | None) -> list[Costsheet]:
        """UC-27: visible costsheets matching the filters ("chỉ phiên bản mới nhất" keeps the highest version),
        newest costing date first."""
        rows = self.visible(sheets, user)
        if f.latest_only:
            latest: dict[str, Costsheet] = {}
            for sheet in rows:
                if sheet.costsheet_no not in latest or sheet.version > latest[sheet.costsheet_no].version:
                    latest[sheet.costsheet_no] = sheet
            rows = list(latest.values())
        rows = [s for s in rows if self.matches(s, f)]
        return sorted(rows, key=lambda s: (s.costing_date, s.costsheet_no, s.version), reverse=True)

    def kpis(self, rows: list[Costsheet]) -> CostsheetKpis:
        return CostsheetKpis(
            total=len(rows),
            pending=sum(1 for r in rows if r.status == S.CHO_DUYET),
            approved=sum(1 for r in rows if r.status == S.DA_DUYET),
            closed=sum(1 for r in rows if r.status == S.DA_CHOT_DON),
            below_threshold=sum(1 for r in rows if r.result.below_threshold),
            low_shrinkage=sum(1 for r in rows if r.result.low_shrinkage),
        )

    def warning_text(self, sheet: Costsheet) -> str:
        """Column "Cảnh báo": GP/OP thấp (BR-28), độ co thấp (BR-14)."""
        parts = []
        if sheet.result.gp_below:
            parts.append("GP thấp")
        if sheet.result.op_below:
            parts.append("OP thấp")
        if sheet.result.low_shrinkage:
            parts.append("Độ co thấp / bằng 0")
        return ", ".join(parts)

    def default_from(self, today: date, days: int) -> date:
        return date.fromordinal(today.toordinal() - days)
