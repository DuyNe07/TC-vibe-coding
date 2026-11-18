"""BR-83, BR-84, BR-86 to BR-88: Screen 2 Line Detail (sửa 2026-11-12, 2026-11-13) - one row per line over the chosen
dates, and the base orders each line made with its strength."""

from collections import defaultdict
from collections.abc import Iterable
from datetime import date

from backend.core.base import BaseBusiness
from backend.features.sewing_productivity.business.changeover_business import ChangeoverBusiness
from backend.features.sewing_productivity.business.line_report_business import LineReportBusiness
from backend.features.sewing_productivity.business.line_strength_business import LineStrengthBusiness
from backend.features.sewing_productivity.business.productivity_business import (
    ProductivityBusiness,
    total,
)
from backend.features.sewing_productivity.business.report_business import ReportBusiness
from backend.features.sewing_productivity.constants import TOTAL_LINE_LABEL
from backend.features.sewing_productivity.models.clean_values import CleanRow, line_sort_key
from backend.features.sewing_productivity.models.enums import Factory
from backend.features.sewing_productivity.models.report_values import (
    LineOrder,
    LineOverview,
    LineTrendPoint,
    PeriodRange,
    ReportFacts,
)
from backend.features.sewing_productivity.models.source_records import LineStrength

FirstDays = dict[tuple[str, str], date]  # (line, base order) -> first day on that line, over every stored row


class LineOverviewBusiness(BaseBusiness[CleanRow]):
    def __init__(self) -> None:
        self.calc = ProductivityBusiness()
        self.lines = LineReportBusiness()
        self.reports = ReportBusiness()
        self.strengths = LineStrengthBusiness()
        self.changeovers = ChangeoverBusiness()

    @staticmethod
    def first_days(history: Iterable[CleanRow], factory: Factory) -> FirstDays:
        """BR-83 the first day of each base order (BR-12) on each line of the factory, on every stored row."""
        result: FirstDays = {}
        for row in history:
            if row.factory == factory:
                key = (row.line, row.base_po)
                if key not in result or row.production_date < result[key]:
                    result[key] = row.production_date
        return result

    def rows(self, facts: ReportFacts, factory: Factory, lines: list[str]) -> list[LineOverview]:
        """BR-83 one row per line with output (only the chosen lines, if any), then the Total row. Since 2026-11-13:
        %Efficiency (with ratio), Matching ratio by BR-86, Changeover by BR-87."""
        goal = self.calc.goal_on(facts.goals.get(factory, []), facts.to_date)
        result = []
        for stat, rows in self.lines.line_periods(facts, factory):
            if lines and stat.line not in lines:
                continue
            result.append(
                LineOverview(
                    line=stat.line,
                    output=total(row.quantity for row in rows),
                    efficiency=stat.efficiency_b,
                    mo8h=stat.mo8h,
                    hours=stat.hours,
                    matching_ratio=self.strengths.matching_ratio(rows, facts.strengths),
                    changeover=self.changeover(facts, factory, stat.line, rows),
                    efficiency_assessment=stat.efficiency_b_assessment,
                    mo8h_assessment=self.calc.assess_mo8h(stat.mo8h, goal),
                )
            )
        if result:
            summary = self.reports.factory_summary(facts, factory)
            shown = [row for row in facts.shown.get(factory, ()) if not lines or row.line in lines]
            efficiency = self.calc.efficiency_b(shown)
            result.append(
                LineOverview(
                    line=TOTAL_LINE_LABEL,
                    is_total=True,
                    output=total(row.quantity for row in shown),
                    efficiency=efficiency,
                    mo8h=summary.mo8h,
                    hours=summary.average_hours,
                    matching_ratio=self.strengths.matching_ratio(shown, facts.strengths),
                    changeover=sum(row.changeover for row in result),
                    efficiency_assessment=self.calc.assess_efficiency(efficiency, goal),
                    mo8h_assessment=self.calc.assess_mo8h(summary.mo8h, goal),
                )
            )
        return result

    def trend_point(
        self, facts: ReportFacts, factory: Factory, line: str, period: PeriodRange
    ) -> LineTrendPoint | None:
        """BR-90 one period of the line (the facts cover that period): the same Output, %Efficiency (with ratio) and
        MO 8h as its Line Detail row (BR-83, BR-29 applied); None when the line made nothing in the period."""
        found = next(
            ((stat, rows) for stat, rows in self.lines.line_periods(facts, factory) if stat.line == line), None
        )
        if found is None:
            return None
        stat, rows = found
        return LineTrendPoint(
            period=period,
            output=total(row.quantity for row in rows),
            efficiency=stat.efficiency_b,
            mo8h=stat.mo8h,
            efficiency_assessment=stat.efficiency_b_assessment,
            mo8h_assessment=stat.mo8h_assessment,
        )

    def changeover(self, facts: ReportFacts, factory: Factory, line: str, rows: list[CleanRow]) -> int:
        """BR-87 the codes new on the line in the chosen dates; with the BR-29 filters only the codes of the rows
        shown count."""
        shown: defaultdict[date, set] = defaultdict(set)
        for row in rows:
            if row.smv is not None and row.quantity > 0:
                shown[row.production_date].add(self.changeovers.code_of(row))
        days = facts.code_days.get((factory, line), [])
        return self.changeovers.style_changeovers(days, facts.from_date, facts.to_date, shown)

    def orders(
        self, facts: ReportFacts, factory: Factory, first_days: FirstDays, strengths: dict[str, LineStrength]
    ) -> list[LineOrder]:
        """BR-84 for every line, the base orders made in the chosen dates, by first day then order."""
        grouped: defaultdict[tuple[str, str], list[CleanRow]] = defaultdict(list)
        for row in facts.shown.get(factory, ()):
            grouped[(row.line, row.base_po)].append(row)
        result = []
        for (line, base_po), rows in grouped.items():
            output = total(row.quantity for row in rows)
            groups = list(dict.fromkeys(row.product_group for row in rows))
            result.append(
                LineOrder(
                    line=line,
                    base_po=base_po,
                    customers=", ".join(dict.fromkeys(row.customer_name for row in rows)),
                    styles=", ".join(dict.fromkeys(row.style for row in rows)),
                    product_groups=groups,
                    cm_price=total(row.cm_earning for row in rows) / output if output else None,
                    output=output,
                    smv=self.calc.average_smv(rows),
                    efficiency=self.calc.efficiency_b(rows),
                    first_day=first_days.get((line, base_po)),
                    matches=self.strengths.matches(groups, strengths.get(line)),
                )
            )
        return sorted(result, key=lambda order: (line_sort_key(order.line), order.first_day or date.max, order.base_po))
