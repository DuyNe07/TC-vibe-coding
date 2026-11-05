"""Assembling the factory-level reports from the base formulas (UC-04, UC-05, UC-07, UC-08)."""

from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import date
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.sewing_productivity.business.changeover_business import ChangeoverBusiness
from backend.features.sewing_productivity.business.cleaning_business import CleaningBusiness
from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.business.productivity_business import ProductivityBusiness, total
from backend.features.sewing_productivity.constants import ALL_FACTORIES, HOURS_PER_SHIFT, RANKING_SIZE
from backend.features.sewing_productivity.models.clean_values import CleanRow, ReportSource
from backend.features.sewing_productivity.models.enums import Factory, RankingMetric
from backend.features.sewing_productivity.models.report_values import (
    DailyFactorySummary,
    FactoryDayStat,
    FactorySummary,
    RankedLine,
    ReportFacts,
)


class ReportBusiness(BaseBusiness[CleanRow]):
    def __init__(self) -> None:
        self.calc = ProductivityBusiness()
        self.cleaning = CleaningBusiness()
        self.filters = FilterBusiness()
        self.changeover = ChangeoverBusiness()

    def facts(
        self,
        source: ReportSource,
        from_date: date,
        to_date: date,
        factories: Iterable[Factory] = (),
        customer_groups: list[str] | None = None,
        product_groups: list[str] | None = None,
    ) -> ReportFacts:
        """Narrow everything to the period first, then build the lookups once (BR-29: `shown` applies the filters)."""
        chosen = tuple(factories) or ALL_FACTORIES
        lookup = self.cleaning.name_lookup(source.production, source.targets)
        records = [
            record
            for record in source.production
            if from_date <= record.production_date <= to_date and record.factory in chosen
        ]
        rows = self.cleaning.clean(records, lookup, source.catalogs)
        customers = set(customer_groups or ())
        products = set(product_groups or ())
        filtered = bool(customers or products)
        shown = self.filters.apply_groups(rows, customers, products) if filtered else rows
        targets = [
            target
            for target in source.targets
            if from_date <= target.target_date <= to_date and target.factory in chosen
        ]
        line_hours = self.calc.line_hours(rows)
        return ReportFacts.model_construct(
            from_date=from_date,
            to_date=to_date,
            factories=chosen,
            filtered=filtered,
            rows=self._by_factory(rows, lambda row: row.factory),
            shown=self._by_factory(shown, lambda row: row.factory),
            targets=self._by_factory(targets, lambda target: target.factory),
            target_map=self.calc.target_map(targets),
            line_hours=line_hours,
            line_sewers=self.calc.line_sewers(rows),
            factory_hours=self.calc.factory_day_hours(line_hours),
            workers={
                (worker.factory, worker.work_date): worker.direct_sewers
                for worker in source.workers
                if from_date <= worker.work_date <= to_date
            },
            goals=self._by_factory(source.goals, lambda goal: goal.factory),
            weekly=source.weekly_changeovers,
        )

    @staticmethod
    def _by_factory(items: Iterable, factory_of: Callable[[object], Factory]) -> dict[Factory, list]:
        grouped: defaultdict[Factory, list] = defaultdict(list)
        for item in items:
            grouped[factory_of(item)].append(item)
        return dict(grouped)

    @staticmethod
    def has_data(facts: ReportFacts) -> bool:
        return any(facts.shown.get(factory) for factory in facts.factories)

    def efficiency_a_note(self, facts: ReportFacts) -> str:
        """BR-18 tells from which day efficiency A is counted when some production day has no target A."""
        if facts.filtered or not facts.target_map:
            return ""
        first = min(key[2] for key in facts.target_map)
        target_days = {(key[0], key[2]) for key in facts.target_map}
        rows = (row for factory in facts.factories for row in facts.rows.get(factory, ()))
        if all((row.factory, row.production_date) in target_days for row in rows):
            return ""
        return f"Hiệu suất A chỉ tính từ {first:%d/%m/%Y}."

    def _factory_target_map(self, facts: ReportFacts, factory: Factory) -> dict:
        return {key: value for key, value in facts.target_map.items() if key[0] == factory}

    def _days_with_workers(self, facts: ReportFacts, factory: Factory) -> list[date]:
        days = {row.production_date for row in facts.rows.get(factory, ())}
        return sorted(day for day in days if (factory, day) in facts.workers)

    def period_mo8h(self, facts: ReportFacts, factory: Factory) -> tuple[Decimal | None, Decimal | None]:
        """BR-23 (MO, MO 8h) of a factory over the period, only on the days that have a number of sewers."""
        days = self._days_with_workers(facts, factory)
        if not days:
            return None, None
        kept = set(days)
        cm = total(row.cm_earning for row in facts.rows.get(factory, ()) if row.production_date in kept)
        workers = total(facts.workers[(factory, day)] for day in days)
        hours = self.calc.factory_period_hours(facts.factory_hours[(factory, day)] for day in days)
        return self.calc.factory_mo(cm, workers), self.calc.factory_mo8h(cm, workers, hours)

    def factory_summary(self, facts: ReportFacts, factory: Factory) -> FactorySummary:
        """UC-04 one column of the overview table (BR-17 to BR-28, BR-38, BR-41), BR-29 applied."""
        if factory not in facts.factories:
            return FactorySummary(factory=factory)
        goal = self.calc.goal_on(facts.goals.get(factory, []), facts.to_date)
        efficiency_target = goal.efficiency_target if goal else None
        mo8h_target = goal.mo8h_target if goal else None
        shown = facts.shown.get(factory, [])
        rows = facts.rows.get(factory, [])
        target_map = self._factory_target_map(facts, factory)
        target_a = total(target_map.values()) if target_map and not facts.filtered else None
        efficiency_a = None
        if target_a:
            efficiency_a = self.calc.efficiency_a(self.calc.output_in_target_scope(rows, target_map), target_a)
        efficiency_b = self.calc.efficiency_b(shown)
        mo8h = None if facts.filtered else self.period_mo8h(facts, factory)[1]
        output = total(row.quantity for row in shown) if shown else None
        cm = total(row.cm_earning for row in shown) if shown else None
        hours = [value for key, value in facts.factory_hours.items() if key[0] == factory]
        weekly = self.changeover.weekly_count(facts.weekly, factory, facts.from_date, facts.to_date)
        lines = self.changeover.line_count(rows)
        return FactorySummary(
            factory=factory,
            target_a=target_a,
            output=output,
            efficiency_target=efficiency_target,
            efficiency_a=efficiency_a,
            efficiency_a_vs_target=self.calc.percent_of_target(efficiency_a, efficiency_target),
            target_b=self.calc.target_b(shown),
            efficiency_b=efficiency_b,
            efficiency_b_vs_target=self.calc.percent_of_target(efficiency_b, efficiency_target),
            cm_earning=cm,
            mo8h_target=mo8h_target,
            mo8h=mo8h,
            mo8h_vs_target=self.calc.percent_of_target(mo8h, mo8h_target),
            average_cm_price=self.calc.average_cm_price(cm, output) if cm is not None else None,
            average_hours=self.calc.factory_period_hours(hours),
            strength_match=None if facts.filtered else self.calc.strength_match(facts.targets.get(factory, [])),
            weekly_changeover=None if weekly is None else Decimal(weekly),
            weekly_changeover_per_line=self.changeover.weekly_per_line(weekly, lines),
            efficiency_a_assessment=self.calc.assess_efficiency(efficiency_a, goal),
            efficiency_b_assessment=self.calc.assess_efficiency(efficiency_b, goal),
            mo8h_assessment=self.calc.assess_mo8h(mo8h, goal),
        )

    def factory_days(self, facts: ReportFacts, factory: Factory) -> list[FactoryDayStat]:
        """UC-05, UC-08 one factory day by day (BR-18, BR-19, BR-20, BR-23, BR-26, BR-28), BR-29 applied."""
        shown_by_day: defaultdict[date, list[CleanRow]] = defaultdict(list)
        for row in facts.shown.get(factory, ()):
            shown_by_day[row.production_date].append(row)
        rows_by_day: defaultdict[date, list[CleanRow]] = defaultdict(list)
        for row in facts.rows.get(factory, ()):
            rows_by_day[row.production_date].append(row)
        target_map = self._factory_target_map(facts, factory)
        target_by_day: defaultdict[date, dict] = defaultdict(dict)
        for key, value in target_map.items():
            target_by_day[key[2]][key] = value
        return [
            self._factory_day(facts, factory, day, shown_by_day[day], rows_by_day[day], target_by_day.get(day, {}))
            for day in sorted(shown_by_day)
        ]

    def _factory_day(
        self,
        facts: ReportFacts,
        factory: Factory,
        day: date,
        shown: list[CleanRow],
        rows: list[CleanRow],
        targets: dict,
    ) -> FactoryDayStat:
        goal = self.calc.goal_on(facts.goals.get(factory, []), day)
        hours = facts.factory_hours.get((factory, day))
        workers = None if facts.filtered else facts.workers.get((factory, day))
        cm = total(row.cm_earning for row in shown)
        mo = self.calc.factory_mo(cm, workers)
        mo8h = self.calc.factory_mo8h(cm, workers, hours)
        efficiency_b = self.calc.efficiency_b(shown)
        target_a = total(targets.values()) if targets and not facts.filtered else None
        efficiency_a = None
        if target_a:
            efficiency_a = self.calc.efficiency_a(self.calc.output_in_target_scope(rows, targets), target_a)
        return FactoryDayStat(
            factory=factory,
            day=day,
            mo=mo,
            hours=hours,
            mo8h=mo8h,
            target_a=target_a,
            efficiency_a=efficiency_a,
            target_b=self.calc.target_b(shown),
            output=total(row.quantity for row in shown),
            efficiency_b=efficiency_b,
            cm_earning=cm,
            workers=workers,
            efficiency_b_assessment=self.calc.assess_efficiency(efficiency_b, goal),
            mo8h_assessment=self.calc.assess_mo8h(mo8h, goal),
        )

    def factory_total(self, facts: ReportFacts, factory: Factory) -> FactoryDayStat:
        """BR-48 total row of the monthly report: sums, efficiency B = output / target B, MO 8h by BR-23."""
        goal = self.calc.goal_on(facts.goals.get(factory, []), facts.to_date)
        shown = facts.shown.get(factory, [])
        mo, mo8h = self.period_mo8h(facts, factory) if not facts.filtered else (None, None)
        days = self._days_with_workers(facts, factory)
        efficiency_b = self.calc.efficiency_b(shown)
        hours = self.calc.factory_period_hours(value for key, value in facts.factory_hours.items() if key[0] == factory)
        workers = total(facts.workers[(factory, day)] for day in days) if days and not facts.filtered else None
        return FactoryDayStat(
            factory=factory,
            mo=mo,
            hours=hours,
            mo8h=mo8h,
            target_b=self.calc.target_b(shown),
            output=total(row.quantity for row in shown),
            efficiency_b=efficiency_b,
            cm_earning=total(row.cm_earning for row in shown),
            workers=workers,
            efficiency_b_assessment=self.calc.assess_efficiency(efficiency_b, goal),
            mo8h_assessment=self.calc.assess_mo8h(mo8h, goal),
        )

    def daily_summary(self, facts: ReportFacts, factory: Factory) -> DailyFactorySummary:
        """UC-07 one column of the daily report (BR-17 to BR-20, BR-23, BR-25, BR-42)."""
        day = facts.from_date
        goal = self.calc.goal_on(facts.goals.get(factory, []), day)
        rows = facts.rows.get(factory, [])
        targets = facts.targets.get(factory, [])
        target_map = self._factory_target_map(facts, factory)
        hours = facts.factory_hours.get((factory, day))
        workers = facts.workers.get((factory, day))
        cm = total(row.cm_earning for row in rows)
        mo = self.calc.factory_mo(cm, workers) if rows else None
        mo8h = self.calc.factory_mo8h(cm, workers, hours) if rows else None
        target_mo8h = self.target_mo8h(targets, workers, hours)
        target_a = total(target_map.values()) if target_map else None
        efficiency_a = None
        if target_a:
            efficiency_a = self.calc.efficiency_a(self.calc.output_in_target_scope(rows, target_map), target_a)
        efficiency_b = self.calc.efficiency_b(rows)
        return DailyFactorySummary(
            factory=factory,
            mo=mo,
            hours=hours,
            target_mo8h=target_mo8h,
            mo8h=mo8h,
            mo8h_vs_target=self.calc.percent_of_target(mo8h, target_mo8h),
            target_output=total(target.daily_target_qty for target in targets) if targets else None,
            output=total(row.quantity for row in rows) if rows else None,
            efficiency_a=efficiency_a,
            efficiency_b=efficiency_b,
            strength_match=self.calc.strength_match(targets),
            workers=workers,
            efficiency_a_assessment=self.calc.assess_efficiency(efficiency_a, goal),
            efficiency_b_assessment=self.calc.assess_efficiency(efficiency_b, goal),
            mo8h_assessment=self.calc.assess_mo8h(mo8h, goal),
        )

    def target_mo8h(self, targets: list, workers: Decimal | None, hours: Decimal | None) -> Decimal | None:
        """BR-42 Target MO 8h = sum of `Daily Target (CM)` / sewers x 8 / actual hours of the factory that day."""
        values = [target.daily_target_cm for target in targets if target.daily_target_cm is not None]
        if not values or not workers or not hours:
            return None
        return total(values) * HOURS_PER_SHIFT / (workers * hours)

    def line_ranking(self, facts: ReportFacts, metric: RankingMetric) -> tuple[list[RankedLine], list[RankedLine]]:
        """BR-44 the 10 highest and 10 lowest lines of the period by the chosen metric, lines with "-" left out."""
        ranked = [
            RankedLine(factory=factory, line=line, value=value)
            for factory in facts.factories
            for line, value in self._line_metric(facts, factory, metric).items()
            if value is not None
        ]
        ranked.sort(key=lambda item: (item.value, item.factory.value, item.line))
        return list(reversed(ranked[-RANKING_SIZE:])), ranked[:RANKING_SIZE]

    def _line_metric(self, facts: ReportFacts, factory: Factory, metric: RankingMetric) -> dict[str, Decimal | None]:
        by_line: defaultdict[str, list[CleanRow]] = defaultdict(list)
        for row in facts.shown.get(factory, ()):
            by_line[row.line].append(row)
        if metric == RankingMetric.EFFICIENCY_B:
            return {line: self.calc.efficiency_b(rows) for line, rows in by_line.items()}
        if facts.filtered:
            return {}
        if metric == RankingMetric.EFFICIENCY_A:
            return {line: self._line_efficiency_a(facts, factory, line, rows) for line, rows in by_line.items()}
        return {line: self._line_period_mo8h(facts, factory, line, rows) for line, rows in by_line.items()}

    def _line_efficiency_a(
        self, facts: ReportFacts, factory: Factory, line: str, rows: list[CleanRow]
    ) -> Decimal | None:
        targets = {key: value for key, value in facts.target_map.items() if key[0] == factory and key[1] == line}
        if not targets:
            return None
        return self.calc.efficiency_a(self.calc.output_in_target_scope(rows, targets), total(targets.values()))

    def _line_period_mo8h(
        self, facts: ReportFacts, factory: Factory, line: str, rows: list[CleanRow]
    ) -> Decimal | None:
        by_day: defaultdict[date, Decimal] = defaultdict(lambda: Decimal(0))
        for row in rows:
            by_day[row.production_date] += row.cm_earning
        values = [
            self.calc.line_mo8h(
                cm, facts.line_sewers.get((factory, line, day)), facts.line_hours.get((factory, line, day))
            )
            for day, cm in by_day.items()
        ]
        return self.calc.line_period_mo8h(values)
