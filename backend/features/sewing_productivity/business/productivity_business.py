"""The base formulas of the reports (BR-18 to BR-28). Pure and exact: nothing is rounded here (BR-50)."""

from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.sewing_productivity.constants import HOURS_PER_SHIFT
from backend.features.sewing_productivity.models.clean_values import CleanRow
from backend.features.sewing_productivity.models.enums import Assessment
from backend.features.sewing_productivity.models.settings_records import FactoryGoal
from backend.features.sewing_productivity.models.source_records import TargetRecord

ZERO = Decimal(0)
HUNDRED = Decimal(100)


def total(values: Iterable[Decimal]) -> Decimal:
    return sum(values, ZERO)


def average(values: Iterable[Decimal]) -> Decimal | None:
    items = list(values)
    return total(items) / len(items) if items else None


class ProductivityBusiness(BaseBusiness[CleanRow]):
    def target_map(self, targets: list[TargetRecord]) -> dict[tuple[object, str, date], Decimal]:
        """BR-18 target A of each line and day; a line and day with no target stays out of the scope."""
        result: defaultdict[tuple[object, str, date], Decimal] = defaultdict(lambda: ZERO)
        for target in targets:
            result[(target.factory, target.line, target.target_date)] += target.daily_target_qty
        return {key: value for key, value in result.items() if value > 0}

    def output_in_target_scope(
        self, rows: list[CleanRow], target_map: dict[tuple[object, str, date], Decimal]
    ) -> Decimal:
        """BR-18 numerator: only the output of the lines and days that have a target A."""
        return total(row.quantity for row in rows if (row.factory, row.line, row.production_date) in target_map)

    def efficiency_a(self, output_in_scope: Decimal, target_a: Decimal | None) -> Decimal | None:
        """BR-18 efficiency A (%) = output / target A on the same scope; "-" without a target."""
        return output_in_scope * HUNDRED / target_a if target_a else None

    def target_b(self, rows: list[CleanRow]) -> Decimal | None:
        """BR-19 target B = sum of the cells that have a value; "-" when none has."""
        values = [row.standard_output for row in rows if row.standard_output is not None]
        return total(values) if values else None

    def efficiency_b(self, rows: list[CleanRow]) -> Decimal | None:
        """BR-19 efficiency B (%) = output / target B, without the rows missing target B on both sides."""
        kept = [row for row in rows if row.standard_output is not None]
        target = total(row.standard_output for row in kept)
        return total(row.quantity for row in kept) * HUNDRED / target if target else None

    def target_no_ratio(self, rows: list[CleanRow]) -> Decimal | None:
        """BR-55 target without ratio = sum of the cells that have a value; "-" when none has."""
        values = [row.standard_output_no_ratio for row in rows if row.standard_output_no_ratio is not None]
        return total(values) if values else None

    def efficiency_no_ratio(self, rows: list[CleanRow]) -> Decimal | None:
        """BR-55 efficiency without ratio (%) = output / that target, without the rows missing it on both sides."""
        kept = [row for row in rows if row.standard_output_no_ratio is not None]
        target = total(row.standard_output_no_ratio for row in kept)
        return total(row.quantity for row in kept) * HUNDRED / target if target else None

    def line_hours(self, rows: list[CleanRow]) -> dict[tuple[object, str, date], Decimal]:
        """BR-20 hours of a line on a day = average hours of its rows."""
        grouped: defaultdict[tuple[object, str, date], list[Decimal]] = defaultdict(list)
        for row in rows:
            grouped[(row.factory, row.line, row.production_date)].append(row.working_hours)
        return {key: total(values) / len(values) for key, values in grouped.items()}

    def factory_day_hours(
        self, line_hours: dict[tuple[object, str, date], Decimal]
    ) -> dict[tuple[object, date], Decimal]:
        """BR-20 hours of a factory on a day = average hours of its lines."""
        grouped: defaultdict[tuple[object, date], list[Decimal]] = defaultdict(list)
        for (factory, _line, day), hours in line_hours.items():
            grouped[(factory, day)].append(hours)
        return {key: total(values) / len(values) for key, values in grouped.items()}

    def factory_period_hours(self, day_hours: Iterable[Decimal]) -> Decimal | None:
        """BR-20 hours of a factory over the period = average hours of its days."""
        return average(day_hours)

    def line_sewers(self, rows: list[CleanRow]) -> dict[tuple[object, str, date], Decimal]:
        """BR-21 people of a line on a day = average people of its rows."""
        grouped: defaultdict[tuple[object, str, date], list[Decimal]] = defaultdict(list)
        for row in rows:
            grouped[(row.factory, row.line, row.production_date)].append(row.sewers)
        return {key: total(values) / len(values) for key, values in grouped.items()}

    def line_mo8h(self, cm_earning: Decimal, sewers: Decimal | None, hours: Decimal | None) -> Decimal | None:
        """BR-22 MO 8h of a line on a day = CM earning / people x 8 / hours."""
        return cm_earning * HOURS_PER_SHIFT / (sewers * hours) if sewers and hours else None

    def line_period_mo8h(self, day_values: Iterable[Decimal | None]) -> Decimal | None:
        """BR-22 MO 8h of a line over the period = average MO 8h of its days."""
        return average(value for value in day_values if value is not None)

    def factory_mo(self, cm_earning: Decimal, workers: Decimal | None) -> Decimal | None:
        """BR-23 MO of a factory on a day = CM earning / sewers; "-" without a number of sewers."""
        return cm_earning / workers if workers else None

    def factory_mo8h(self, cm_earning: Decimal, workers: Decimal | None, hours: Decimal | None) -> Decimal | None:
        """BR-23 MO 8h of a factory = MO x 8 / hours (also for the period, with its totals and average hours)."""
        return cm_earning * HOURS_PER_SHIFT / (workers * hours) if workers and hours else None

    def average_smv(self, rows: list[CleanRow]) -> Decimal | None:
        """BR-66 average SMV weighted by output = sum(SMV x output) / output, without the rows missing SMV."""
        kept = [row for row in rows if row.smv is not None]
        output = total(row.quantity for row in kept)
        return total(row.smv * row.quantity for row in kept) / output if output else None

    def direct_labor(self, direct: Decimal, headcount: Decimal) -> Decimal | None:
        """BR-65 %Direct labor = direct sewers / total headcount (%), both summed over the same days."""
        return direct * HUNDRED / headcount if headcount else None

    def average_cm_price(self, cm_earning: Decimal, output: Decimal) -> Decimal | None:
        """BR-24 average CM price = CM earning / output."""
        return cm_earning / output if output else None

    def strength_match(self, targets: list[TargetRecord]) -> Decimal | None:
        """BR-25 share of target A not on mismatched rows (%); "-" without target A."""
        whole = total(target.daily_target_qty for target in targets)
        if not whole:
            return None
        mismatched = total(target.daily_target_qty for target in targets if target.is_mismatched)
        return (whole - mismatched) * HUNDRED / whole

    def goal_on(self, goals: list[FactoryGoal], day: date) -> FactoryGoal | None:
        """BR-26 the level with the latest effective date that is not after the day."""
        valid = [goal for goal in goals if goal.effective_from <= day]
        return max(valid, key=lambda goal: goal.effective_from) if valid else None

    def percent_of_target(self, actual: Decimal | None, target: Decimal | None) -> Decimal | None:
        """BR-27 % of target = actual / target."""
        return actual * HUNDRED / target if actual is not None and target else None

    def assess(self, value: Decimal | None, threshold: Decimal | None) -> Assessment:
        """BR-28 below the threshold is "Dưới ngưỡng", equal or above is "Đạt", no number is "-"."""
        if value is None or threshold is None:
            return Assessment.NOT_AVAILABLE
        return Assessment.BELOW if value < threshold else Assessment.PASSED

    def assess_efficiency(self, value: Decimal | None, goal: FactoryGoal | None) -> Assessment:
        """BR-28 applied to efficiency A or B with the level of the day."""
        return self.assess(value, goal.efficiency_threshold if goal else None)

    def assess_mo8h(self, value: Decimal | None, goal: FactoryGoal | None) -> Assessment:
        """BR-28 applied to MO 8h with the level of the day."""
        return self.assess(value, goal.mo8h_threshold if goal else None)
