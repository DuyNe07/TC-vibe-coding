"""BR-78, BR-79, BR-80: Screen 6 Line performance - each line of one factory, then the factory total."""

from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.sewing_productivity.business.line_report_business import LineReportBusiness
from backend.features.sewing_productivity.business.productivity_business import (
    HUNDRED,
    ProductivityBusiness,
    total,
)
from backend.features.sewing_productivity.business.report_business import ReportBusiness
from backend.features.sewing_productivity.constants import TOTAL_LINE_LABEL
from backend.features.sewing_productivity.models.clean_values import CleanRow
from backend.features.sewing_productivity.models.enums import Factory
from backend.features.sewing_productivity.models.report_values import LinePerformance, ReportFacts
from backend.features.sewing_productivity.models.settings_records import FactoryGoal


class LinePerformanceBusiness(BaseBusiness[LinePerformance]):
    def __init__(self) -> None:
        self.calc = ProductivityBusiness()
        self.lines = LineReportBusiness()
        self.reports = ReportBusiness()

    def rows(self, facts: ReportFacts, factory: Factory) -> list[LinePerformance]:
        """UC-31 one row per line with output (BR-78), then the Total row (BR-79); empty without data."""
        goal = self.calc.goal_on(facts.goals.get(factory, []), facts.to_date)  # BR-26: the level of the last day
        result = []
        for stat, rows in self.lines.line_periods(facts, factory):
            ratio = self.calc.efficiency_b(rows)
            result.append(
                LinePerformance(
                    line=stat.line,
                    operators=stat.sewers,
                    target_output=self.calc.target_b(rows),
                    output=total(row.quantity for row in rows),
                    output_ratio=ratio,
                    target_value=self.target_value(rows),
                    value=total(row.cm_earning for row in rows),
                    value_ratio=self.value_ratio(rows),
                    mo8h=stat.mo8h,
                    output_ratio_assessment=self.calc.assess_efficiency(ratio, goal),
                    mo8h_assessment=self.calc.assess_mo8h(stat.mo8h, goal),
                )
            )
        if result:
            result.append(self._total(facts, factory, result, goal))
        return result

    @staticmethod
    def target_value(rows: list[CleanRow]) -> Decimal | None:
        """BR-78 Value Target = sum of (target with ratio x CM price) of the rows that have a target."""
        kept = [row for row in rows if row.standard_output is not None]
        return total(row.standard_output * row.cm_price for row in kept) if kept else None

    def value_ratio(self, rows: list[CleanRow]) -> Decimal | None:
        """BR-78 Value Ratio (%) = CM earning / Value Target, the rows without a target left out of both sides."""
        kept = [row for row in rows if row.standard_output is not None]
        target = self.target_value(kept)
        return total(row.cm_earning for row in kept) * HUNDRED / target if target else None

    def _total(
        self, facts: ReportFacts, factory: Factory, lines: list[LinePerformance], goal: FactoryGoal | None
    ) -> LinePerformance:
        """BR-79 sums of the lines, ratios again on the sums, MO 8h of the factory (BR-23, as Screen 1)."""
        rows = list(facts.shown.get(factory, ()))
        ratio = self.calc.efficiency_b(rows)
        mo8h = self.reports.factory_summary(facts, factory).mo8h
        operators = [line.operators for line in lines if line.operators is not None]
        return LinePerformance(
            line=TOTAL_LINE_LABEL,
            is_total=True,
            operators=total(operators) if operators else None,
            target_output=self.calc.target_b(rows),
            output=total(row.quantity for row in rows),
            output_ratio=ratio,
            target_value=self.target_value(rows),
            value=total(row.cm_earning for row in rows),
            value_ratio=self.value_ratio(rows),
            mo8h=mo8h,
            output_ratio_assessment=self.calc.assess_efficiency(ratio, goal),
            mo8h_assessment=self.calc.assess_mo8h(mo8h, goal),
        )
