"""Assembling the factory-level reports from the base formulas (UC-04, UC-05, UC-07, UC-08)."""

from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import date
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.sewing_productivity.business.changeover_business import ChangeoverBusiness
from backend.features.sewing_productivity.business.cleaning_business import CleaningBusiness
from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.business.line_strength_business import LineStrengthBusiness
from backend.features.sewing_productivity.business.productivity_business import ProductivityBusiness, total
from backend.features.sewing_productivity.constants import (
    ALL_FACTORIES,
    HCM_COLUMN,
    HCM_FACTORIES,
    HOURS_PER_SHIFT,
    MIN_HCM_FACTORIES,
    RANKING_SIZE,
    TOTAL_COLUMN,
)
from backend.features.sewing_productivity.models.clean_values import CleanRow, NameLookup, ReportSource
from backend.features.sewing_productivity.models.enums import Factory, RankingMetric
from backend.features.sewing_productivity.models.report_values import (
    DailyFactorySummary,
    FactoryDayStat,
    FactorySummary,
    PeriodRange,
    PeriodSummaries,
    RankedLine,
    ReportFacts,
)
from backend.features.sewing_productivity.models.settings_records import FactoryGoal
from backend.features.sewing_productivity.models.source_records import LineStrength

CodeDays = dict[tuple[Factory, str], list[tuple[date, frozenset]]]  # BR-87, see ChangeoverBusiness.code_days


class ReportBusiness(BaseBusiness[CleanRow]):
    def __init__(self) -> None:
        self.calc = ProductivityBusiness()
        self.cleaning = CleaningBusiness()
        self.filters = FilterBusiness()
        self.changeover = ChangeoverBusiness()
        self.strength = LineStrengthBusiness()

    def facts(
        self,
        source: ReportSource,
        from_date: date,
        to_date: date,
        factories: Iterable[Factory] = (),
        customer_groups: list[str] | None = None,
        product_groups: list[str] | None = None,
        lookup: NameLookup | None = None,
        strengths: list[LineStrength] | None = None,
        code_days: CodeDays | None = None,
    ) -> ReportFacts:
        """Narrow everything to the period first, then build the lookups once (BR-29: `shown` applies the filters).

        `lookup` (BR-13) can be given when one report builds the facts of many periods from the same data.
        `strengths` (BR-86) default to the ones of the source; `code_days` (BR-87) only when changeovers are counted."""
        chosen = tuple(factories) or ALL_FACTORIES
        lookup = lookup or self.cleaning.name_lookup(source.production, source.targets)
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
            headcount={
                (worker.factory, worker.work_date): worker.total_workers
                for worker in source.workers
                if from_date <= worker.work_date <= to_date and worker.total_workers is not None
            },
            goals=self._by_factory(source.goals, lambda goal: goal.factory),
            weekly=source.weekly_changeovers,
            strengths=self.strength.strong_map(source.strengths if strengths is None else strengths),
            code_days=code_days or {},
        )

    def code_days(
        self, source: ReportSource, factories: Iterable[Factory] = (), lookup: NameLookup | None = None
    ) -> CodeDays:
        """BR-87 the working days and codes of every line of the chosen factories, over the whole stored history."""
        chosen = tuple(factories) or ALL_FACTORIES
        lookup = lookup or self.cleaning.name_lookup(source.production, source.targets)
        records = [record for record in source.production if record.factory in chosen]
        return self.changeover.code_days(self.cleaning.clean(records, lookup, source.catalogs))

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
        return self._members_mo8h(facts, (factory,))

    def _members_mo8h(self, facts: ReportFacts, members: tuple[Factory, ...]) -> tuple[Decimal | None, Decimal | None]:
        """BR-23 over one factory or a group (BR-51): the factory-days with sewers, hours = average of those days."""
        pairs = [(factory, day) for factory in members for day in self._days_with_workers(facts, factory)]
        if not pairs:
            return None, None
        kept = set(pairs)
        cm = total(
            row.cm_earning
            for factory in members
            for row in facts.rows.get(factory, ())
            if (factory, row.production_date) in kept
        )
        workers = total(facts.workers[pair] for pair in pairs)
        hours = self.calc.factory_period_hours(facts.factory_hours[pair] for pair in pairs)
        return self.calc.factory_mo(cm, workers), self.calc.factory_mo8h(cm, workers, hours)

    def _members_direct_labor(self, facts: ReportFacts, members: tuple[Factory, ...]) -> Decimal | None:
        """BR-65 over one factory or a group: the factory-days that have both numbers, summed before dividing."""
        pairs = [pair for pair in facts.headcount if pair[0] in members and pair in facts.workers]
        if not pairs:
            return None
        return self.calc.direct_labor(
            total(facts.workers[pair] for pair in pairs), total(facts.headcount[pair] for pair in pairs)
        )

    def _members_direct_workers(self, facts: ReportFacts, members: tuple[Factory, ...]) -> Decimal | None:
        """BR-69 Direct worker: each factory's average sewers per day over its days with a number; a group adds them."""
        averages = []
        for factory in members:
            counts = [count for (owner, _day), count in facts.workers.items() if owner == factory]
            if counts:
                averages.append(total(counts) / len(counts))
        return total(averages) if averages else None

    def period_summaries(
        self,
        source: ReportSource,
        periods: list[PeriodRange],
        factories: Iterable[Factory] = (),
        code_days: CodeDays | None = None,
    ) -> list[PeriodSummaries]:
        """UC-29 every period with production (BR-68), with the Screen 1 figures of each chosen factory, HCM, Total;
        with `code_days` also the changeovers of BR-89."""
        lookup = self.cleaning.name_lookup(source.production, source.targets)
        result = []
        for period in periods:
            facts = self.facts(source, period.from_date, period.to_date, factories, lookup=lookup, code_days=code_days)
            if not self.has_data(facts):
                continue
            summaries = [self.factory_summary(facts, factory) for factory in facts.factories]
            hcm = self.hcm_summary(facts)
            if hcm:
                summaries.append(hcm)
            summaries.append(self.total_summary(facts))
            result.append(PeriodSummaries(period=period, summaries=summaries))
        return result

    def hcm_members(self, facts: ReportFacts) -> tuple[Factory, ...]:
        """BR-51 the chosen HCM factories; empty when fewer than 2 are chosen."""
        members = tuple(factory for factory in HCM_FACTORIES if factory in facts.factories)
        return members if len(members) >= MIN_HCM_FACTORIES else ()

    def _common_goal(self, facts: ReportFacts, members: tuple[Factory, ...], day: date) -> FactoryGoal | None:
        """BR-26 for a group (BR-51): its level only when every member has the same 4 numbers, otherwise none."""
        goals = [self.calc.goal_on(facts.goals.get(factory, []), day) for factory in members]
        levels = {
            (goal.efficiency_target, goal.mo8h_target, goal.efficiency_threshold, goal.mo8h_threshold) if goal else None
            for goal in goals
        }
        return goals[0] if len(levels) == 1 else None

    def _weekly_changeover(self, facts: ReportFacts, members: tuple[Factory, ...]) -> tuple[int | None, int]:
        """BR-38, BR-34 over one factory or a group: a group has a weekly number only when every member has one."""
        counts = [
            self.changeover.weekly_count(facts.weekly, factory, facts.from_date, facts.to_date) for factory in members
        ]
        lines = sum(self.changeover.line_count(facts.rows.get(factory, [])) for factory in members)
        known = [count for count in counts if count is not None]
        return (sum(known) if len(known) == len(counts) else None), lines

    def factory_summary(self, facts: ReportFacts, factory: Factory) -> FactorySummary:
        """UC-04 one column of the overview table (BR-17 to BR-28, BR-38, BR-41), BR-29 applied."""
        if factory not in facts.factories:
            return FactorySummary(factory=factory)
        return self._summary(facts, (factory,), factory=factory)

    def hcm_summary(self, facts: ReportFacts) -> FactorySummary | None:
        """UC-27 the HCM column of the overview table (BR-51); None when it is not shown."""
        members = self.hcm_members(facts)
        return self._summary(facts, members, group_name=HCM_COLUMN) if members else None

    def total_summary(self, facts: ReportFacts) -> FactorySummary:
        """BR-58 every chosen factory together (Vinh Long + HCM), with the same formulas as one factory."""
        return self._summary(facts, tuple(facts.factories), group_name=TOTAL_COLUMN)

    def _summary(
        self, facts: ReportFacts, members: tuple[Factory, ...], factory: Factory | None = None, group_name: str = ""
    ) -> FactorySummary:
        goal = self._common_goal(facts, members, facts.to_date)
        efficiency_target = goal.efficiency_target if goal else None
        mo8h_target = goal.mo8h_target if goal else None
        shown = [row for member in members for row in facts.shown.get(member, ())]
        rows = [row for member in members for row in facts.rows.get(member, ())]
        target_map = {key: value for key, value in facts.target_map.items() if key[0] in members}
        target_a = total(target_map.values()) if target_map and not facts.filtered else None
        efficiency_a = None
        if target_a:
            efficiency_a = self.calc.efficiency_a(self.calc.output_in_target_scope(rows, target_map), target_a)
        efficiency_b = self.calc.efficiency_b(shown)
        mo8h = None if facts.filtered else self._members_mo8h(facts, members)[1]
        output = total(row.quantity for row in shown) if shown else None
        cm = total(row.cm_earning for row in shown) if shown else None
        hours = [value for key, value in facts.factory_hours.items() if key[0] in members]
        weekly, lines = self._weekly_changeover(facts, members)
        changeovers, per_line_day = self._style_changeovers(facts, members)
        return FactorySummary(
            factory=factory,
            group_name=group_name,
            target_a=target_a,
            output=output,
            efficiency_target=efficiency_target,
            efficiency_a=efficiency_a,
            efficiency_a_vs_target=self.calc.percent_of_target(efficiency_a, efficiency_target),
            target_b=self.calc.target_b(shown),
            efficiency_b=efficiency_b,
            efficiency_b_vs_target=self.calc.percent_of_target(efficiency_b, efficiency_target),
            target_no_ratio=self.calc.target_no_ratio(shown),
            efficiency_no_ratio=self.calc.efficiency_no_ratio(shown),
            cm_earning=cm,
            mo8h_target=mo8h_target,
            mo8h=mo8h,
            mo8h_vs_target=self.calc.percent_of_target(mo8h, mo8h_target),
            average_cm_price=self.calc.average_cm_price(cm, output) if cm is not None else None,
            average_hours=self.calc.factory_period_hours(hours),
            strength_match=self.strength.matching_ratio(shown, facts.strengths),  # BR-86 (sửa BR-25, 2026-11-13)
            weekly_changeover=None if weekly is None else Decimal(weekly),
            weekly_changeover_per_line=self.changeover.weekly_per_line(weekly, lines),
            average_smv=self.calc.average_smv(shown),
            direct_labor=None if facts.filtered else self._members_direct_labor(facts, members),
            direct_workers=None if facts.filtered else self._members_direct_workers(facts, members),
            changeovers=changeovers,
            changeover_per_line_day=per_line_day,
            efficiency_a_assessment=self.calc.assess_efficiency(efficiency_a, goal),
            efficiency_b_assessment=self.calc.assess_efficiency(efficiency_b, goal),
            mo8h_assessment=self.calc.assess_mo8h(mo8h, goal),
        )

    def _style_changeovers(self, facts: ReportFacts, members: tuple[Factory, ...]) -> tuple[int | None, Decimal | None]:
        """BR-89 the changeovers of the members (BR-87, every line) and changeovers / line / day; a group divides by
        the sum of working days x lines of each member. (None, None) when the report does not count changeovers."""
        if not facts.code_days:
            return None, None
        count = sum(
            self.changeover.style_changeovers(days, facts.from_date, facts.to_date)
            for (factory, _line), days in facts.code_days.items()
            if factory in members
        )
        line_days = sum(
            self.changeover.working_days(facts.rows.get(member, []))
            * self.changeover.line_count(facts.rows.get(member, []))
            for member in members
        )
        return count, (Decimal(count) / Decimal(line_days) if line_days else None)

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

    def hcm_days(self, facts: ReportFacts) -> list[FactoryDayStat]:
        """UC-27 the HCM points of the daily charts (BR-51): the 3 formulas on the factories together, day by day."""
        members = self.hcm_members(facts)
        shown_by_day: defaultdict[date, list[CleanRow]] = defaultdict(list)
        rows_by_day: defaultdict[date, list[CleanRow]] = defaultdict(list)
        targets_by_day: defaultdict[date, dict] = defaultdict(dict)
        for member in members:
            for row in facts.shown.get(member, ()):
                shown_by_day[row.production_date].append(row)
            for row in facts.rows.get(member, ()):
                rows_by_day[row.production_date].append(row)
        for key, value in facts.target_map.items():
            if key[0] in members:
                targets_by_day[key[2]][key] = value
        return [
            self._hcm_day(facts, members, day, shown_by_day[day], rows_by_day[day], targets_by_day.get(day, {}))
            for day in sorted(shown_by_day)
        ]

    def _hcm_day(
        self,
        facts: ReportFacts,
        members: tuple[Factory, ...],
        day: date,
        shown: list[CleanRow],
        rows: list[CleanRow],
        targets: dict,
    ) -> FactoryDayStat:
        target_a = total(targets.values()) if targets and not facts.filtered else None
        efficiency_a = None
        if target_a:
            efficiency_a = self.calc.efficiency_a(self.calc.output_in_target_scope(rows, targets), target_a)
        mo8h = None
        with_workers = [factory for factory in members if (factory, day) in facts.workers]
        if with_workers and not facts.filtered:
            cm = total(row.cm_earning for row in shown if row.factory in with_workers)
            workers = total(facts.workers[(factory, day)] for factory in with_workers)
            hours = self.calc.factory_period_hours(
                facts.factory_hours[(factory, day)] for factory in with_workers if (factory, day) in facts.factory_hours
            )
            mo8h = self.calc.factory_mo8h(cm, workers, hours)
        return FactoryDayStat(
            group_name=HCM_COLUMN,
            day=day,
            mo8h=mo8h,
            efficiency_a=efficiency_a,
            efficiency_b=self.calc.efficiency_b(shown),
            efficiency_no_ratio=self.calc.efficiency_no_ratio(shown),
        )

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
            target_no_ratio=self.calc.target_no_ratio(shown),
            efficiency_no_ratio=self.calc.efficiency_no_ratio(shown),
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
            target_no_ratio=self.calc.target_no_ratio(shown),
            efficiency_no_ratio=self.calc.efficiency_no_ratio(shown),
            cm_earning=total(row.cm_earning for row in shown),
            workers=workers,
            efficiency_b_assessment=self.calc.assess_efficiency(efficiency_b, goal),
            mo8h_assessment=self.calc.assess_mo8h(mo8h, goal),
        )

    def daily_summary(self, facts: ReportFacts, factory: Factory) -> DailyFactorySummary:
        """UC-07 one column of the daily report (BR-17 to BR-20, BR-23, BR-25, BR-42)."""
        return self._daily(facts, (factory,), factory=factory)

    def hcm_daily_summary(self, facts: ReportFacts) -> DailyFactorySummary | None:
        """UC-27 the HCM column of the daily report (BR-51); None when it is not shown."""
        members = self.hcm_members(facts)
        return self._daily(facts, members, group_name=HCM_COLUMN) if members else None

    def _daily(
        self, facts: ReportFacts, members: tuple[Factory, ...], factory: Factory | None = None, group_name: str = ""
    ) -> DailyFactorySummary:
        day = facts.from_date
        goal = self._common_goal(facts, members, day)
        rows = [row for member in members for row in facts.rows.get(member, ())]
        targets = [target for member in members for target in facts.targets.get(member, ())]
        target_map = {key: value for key, value in facts.target_map.items() if key[0] in members}
        hours = self.calc.factory_period_hours(
            facts.factory_hours[(member, day)] for member in members if (member, day) in facts.factory_hours
        )
        with_workers = [member for member in members if (member, day) in facts.workers]
        workers = total(facts.workers[(member, day)] for member in with_workers) if with_workers else None
        worker_hours = self.calc.factory_period_hours(
            facts.factory_hours[(member, day)] for member in with_workers if (member, day) in facts.factory_hours
        )
        mo, mo8h = self._members_mo8h(facts, members)
        target_mo8h = self.target_mo8h(
            [target for member in with_workers for target in facts.targets.get(member, ())], workers, worker_hours
        )
        target_a = total(target_map.values()) if target_map else None
        efficiency_a = None
        if target_a:
            efficiency_a = self.calc.efficiency_a(self.calc.output_in_target_scope(rows, target_map), target_a)
        efficiency_b = self.calc.efficiency_b(rows)
        return DailyFactorySummary(
            factory=factory,
            group_name=group_name,
            mo=mo,
            hours=hours,
            target_mo8h=target_mo8h,
            mo8h=mo8h,
            mo8h_vs_target=self.calc.percent_of_target(mo8h, target_mo8h),
            target_output=total(target.daily_target_qty for target in targets) if targets else None,
            output=total(row.quantity for row in rows) if rows else None,
            efficiency_a=efficiency_a,
            efficiency_b=efficiency_b,
            efficiency_no_ratio=self.calc.efficiency_no_ratio(rows),
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
        if metric == RankingMetric.NO_RATIO:
            return {line: self.calc.efficiency_no_ratio(rows) for line, rows in by_line.items()}
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
