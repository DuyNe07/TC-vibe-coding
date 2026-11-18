"""Line-level reports: Screen 2, the line table of Screen 3 and the 5 tables of Screen 5."""

from collections import defaultdict
from datetime import date
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.sewing_productivity.business.productivity_business import (
    ProductivityBusiness,
    average,
    total,
)
from backend.features.sewing_productivity.business.report_business import ReportBusiness
from backend.features.sewing_productivity.constants import NO_RATIO_TABLE_TITLE, TOTAL_LINE_LABEL
from backend.features.sewing_productivity.models.clean_values import CleanRow, line_sort_key
from backend.features.sewing_productivity.models.enums import Factory, NumberKind, RowType
from backend.features.sewing_productivity.models.report_values import (
    LineStat,
    MatrixCell,
    MatrixRow,
    MatrixTable,
    ReportFacts,
)


class LineReportBusiness(BaseBusiness[CleanRow]):
    def __init__(self) -> None:
        self.calc = ProductivityBusiness()
        self.reports = ReportBusiness()

    def line_rows(self, facts: ReportFacts, factory: Factory, lines: list[str] | None = None) -> list[LineStat]:
        """UC-06 lines sorted by number then day, each followed by its period row (BR-17 to BR-22, BR-27, BR-28)."""
        result: list[LineStat] = []
        by_line = self._days_by_line(facts, factory, lines)
        for line in sorted(by_line, key=line_sort_key):
            days = by_line[line]
            stats = [self._line_day(facts, factory, line, day, days[day]) for day in sorted(days)]
            result.extend(stats)
            result.append(self._line_period(facts, factory, line, stats, days))
        return result

    def line_periods(self, facts: ReportFacts, factory: Factory) -> list[tuple[LineStat, list[CleanRow]]]:
        """UC-31 each line with output, sorted by number: its period row (as Screen 2 / Screen 5) and its rows."""
        by_line = self._days_by_line(facts, factory, None, with_targets=False)
        result = []
        for line in sorted(by_line, key=line_sort_key):
            days = by_line[line]
            stats = [self._line_day(facts, factory, line, day, days[day]) for day in sorted(days)]
            rows = [row for day in sorted(days) for row in days[day]]
            result.append((self._line_period(facts, factory, line, stats, days), rows))
        return result

    def day_rows(self, facts: ReportFacts, factory: Factory) -> list[LineStat]:
        """UC-07 one row per line on the only day of the report, sorted by number (BR-21, BR-22, BR-43)."""
        by_line = self._days_by_line(facts, factory, None)
        return [
            self._line_day(facts, factory, line, day, rows)
            for line in sorted(by_line, key=line_sort_key)
            for day, rows in by_line[line].items()
            if rows
        ]

    def _days_by_line(
        self, facts: ReportFacts, factory: Factory, lines: list[str] | None, with_targets: bool = True
    ) -> dict[str, dict[date, list[CleanRow]]]:
        """Rows by line and day; a line and day with a target A but no output still gets a row (BR-18 scope)."""
        wanted = set(lines or ())
        by_line: defaultdict[str, defaultdict[date, list[CleanRow]]] = defaultdict(lambda: defaultdict(list))
        for row in facts.shown.get(factory, ()):
            if not wanted or row.line in wanted:
                by_line[row.line][row.production_date].append(row)
        if with_targets and not facts.filtered:
            for key_factory, line, day in facts.target_map:
                if key_factory == factory and (not wanted or line in wanted):
                    by_line[line].setdefault(day, [])
        return by_line

    def _line_day(self, facts: ReportFacts, factory: Factory, line: str, day: date, rows: list[CleanRow]) -> LineStat:
        key = (factory, line, day)
        goal = self.calc.goal_on(facts.goals.get(factory, []), day)
        output = total(row.quantity for row in rows)
        cm = total(row.cm_earning for row in rows)
        hours = facts.line_hours.get(key)
        sewers = None if facts.filtered else facts.line_sewers.get(key)
        target_a = None if facts.filtered else facts.target_map.get(key)
        efficiency_a = self.calc.efficiency_a(output, target_a)
        efficiency_b = self.calc.efficiency_b(rows)
        mo8h = self.calc.line_mo8h(cm, sewers, hours)
        return LineStat(
            row_type=RowType.DAY,
            factory=factory,
            line=line,
            day=day,
            target_a=target_a,
            output=output,
            efficiency_a=efficiency_a,
            target_b=self.calc.target_b(rows),
            efficiency_b=efficiency_b,
            target_no_ratio=self.calc.target_no_ratio(rows),
            efficiency_no_ratio=self.calc.efficiency_no_ratio(rows),
            cm_earning=cm,
            sewers=sewers,
            hours=hours,
            mo=cm / sewers if sewers else None,
            mo8h=mo8h,
            mismatched_output=self.mismatched_output(rows),
            efficiency_a_assessment=self.calc.assess_efficiency(efficiency_a, goal),
            efficiency_b_assessment=self.calc.assess_efficiency(efficiency_b, goal),
            mo8h_assessment=self.calc.assess_mo8h(mo8h, goal),
        )

    def mismatched_output(self, rows: list[CleanRow]) -> Decimal:
        """BR-43 output of the rows marked `Trái sở trường`."""
        return total(row.quantity for row in rows if row.is_mismatched)

    def _line_period(
        self, facts: ReportFacts, factory: Factory, line: str, stats: list[LineStat], days: dict[date, list[CleanRow]]
    ) -> LineStat:
        goal = self.calc.goal_on(facts.goals.get(factory, []), facts.to_date)
        rows = [row for day_rows in days.values() for row in day_rows]
        with_target = [stat for stat in stats if stat.target_a is not None]
        target_a = total(stat.target_a for stat in with_target) if with_target else None
        efficiency_a = self.calc.efficiency_a(total(stat.output for stat in with_target), target_a)
        efficiency_b = self.calc.efficiency_b(rows)
        mo8h = self.calc.line_period_mo8h(stat.mo8h for stat in stats)
        return LineStat(
            row_type=RowType.PERIOD,
            factory=factory,
            line=line,
            target_a=target_a,
            output=total(stat.output for stat in stats),
            efficiency_a=efficiency_a,
            target_b=self.calc.target_b(rows),
            efficiency_b=efficiency_b,
            target_no_ratio=self.calc.target_no_ratio(rows),
            efficiency_no_ratio=self.calc.efficiency_no_ratio(rows),
            cm_earning=total(stat.cm_earning for stat in stats),
            sewers=average(stat.sewers for stat in stats if stat.sewers is not None),
            hours=average(stat.hours for stat in stats if stat.hours is not None),
            mo8h=mo8h,
            mismatched_output=self.mismatched_output(rows),
            efficiency_a_assessment=self.calc.assess_efficiency(efficiency_a, goal),
            efficiency_b_assessment=self.calc.assess_efficiency(efficiency_b, goal),
            mo8h_assessment=self.calc.assess_mo8h(mo8h, goal),
        )

    def factory_total_row(self, facts: ReportFacts, factory: Factory) -> LineStat:
        """UC-06 the factory total, over all its lines whatever lines are chosen (BR-18, BR-19, BR-20, BR-23)."""
        goal = self.calc.goal_on(facts.goals.get(factory, []), facts.to_date)
        summary = self.reports.factory_summary(facts, factory)
        shown = facts.shown.get(factory, [])
        return LineStat(
            row_type=RowType.TOTAL,
            factory=factory,
            line=TOTAL_LINE_LABEL,
            target_a=summary.target_a,
            output=total(row.quantity for row in shown),
            efficiency_a=summary.efficiency_a,
            target_b=summary.target_b,
            efficiency_b=summary.efficiency_b,
            target_no_ratio=summary.target_no_ratio,
            efficiency_no_ratio=summary.efficiency_no_ratio,
            cm_earning=total(row.cm_earning for row in shown),
            sewers=None if facts.filtered else self._average_people_per_day(facts, factory),
            hours=summary.average_hours,
            mo8h=summary.mo8h,
            mismatched_output=self.mismatched_output(shown),
            efficiency_a_assessment=self.calc.assess_efficiency(summary.efficiency_a, goal),
            efficiency_b_assessment=self.calc.assess_efficiency(summary.efficiency_b, goal),
            mo8h_assessment=self.calc.assess_mo8h(summary.mo8h, goal),
        )

    def _average_people_per_day(self, facts: ReportFacts, factory: Factory) -> Decimal | None:
        per_day: defaultdict[date, Decimal] = defaultdict(lambda: Decimal(0))
        for (key_factory, _line, day), sewers in facts.line_sewers.items():
            if key_factory == factory:
                per_day[day] += sewers
        return average(per_day.values())

    def day_total_row(self, facts: ReportFacts, factory: Factory, stats: list[LineStat]) -> LineStat:
        """UC-07 total of the line table: sums, and MO 8h on the totals of the lines (BR-48)."""
        day = facts.from_date
        hours = facts.factory_hours.get((factory, day))
        cm = total(stat.cm_earning for stat in stats)
        sewers = total(stat.sewers for stat in stats if stat.sewers is not None)
        goal = self.calc.goal_on(facts.goals.get(factory, []), day)
        mo8h = self.calc.line_mo8h(cm, sewers, hours)
        return LineStat(
            row_type=RowType.TOTAL,
            factory=factory,
            line=TOTAL_LINE_LABEL,
            day=day,
            output=total(stat.output for stat in stats),
            cm_earning=cm,
            sewers=sewers or None,
            hours=hours,
            mo=cm / sewers if sewers else None,
            mo8h=mo8h,
            mismatched_output=total(stat.mismatched_output for stat in stats),
            mo8h_assessment=self.calc.assess_mo8h(mo8h, goal),
        )

    def mo_tables(
        self, facts: ReportFacts, factory: Factory, lines: list[str] | None
    ) -> tuple[list[date], list[MatrixTable]]:
        """UC-09 the tables of Screen 5: lines in rows, days in columns, period column and total row (BR-48, BR-55)."""
        by_line = self._days_by_line(facts, factory, lines, with_targets=False)
        names = sorted(by_line, key=line_sort_key)
        day_stats = {
            line: {day: self._line_day(facts, factory, line, day, rows) for day, rows in by_line[line].items()}
            for line in names
        }
        period_stats = {
            line: self._line_period(facts, factory, line, list(day_stats[line].values()), by_line[line])
            for line in names
        }
        dates = sorted({day for line in names for day in by_line[line]})
        tables = [
            self._table("MO 8h", "MO 8h", NumberKind.MONEY, names, day_stats, period_stats, "mo8h", "mo8h_assessment"),
            self._table("Tiền CM", "Tien CM", NumberKind.MONEY, names, day_stats, period_stats, "cm_earning", None),
            self._table("Giờ làm", "Gio lam", NumberKind.MONEY, names, day_stats, period_stats, "hours", None),
            self._table("Số người", "So nguoi", NumberKind.PEOPLE, names, day_stats, period_stats, "sewers", None),
            self._table(
                "Hiệu suất B", "Hieu suat B", NumberKind.PERCENT, names, day_stats, period_stats, "efficiency_b",
                "efficiency_b_assessment",
            ),
            self._table(
                NO_RATIO_TABLE_TITLE, "Hieu suat khong ti le", NumberKind.PERCENT, names, day_stats, period_stats,
                "efficiency_no_ratio", None,
            ),
        ]  # fmt: skip
        totals = self._matrix_totals(facts, factory, by_line, dates)
        for table, total_row in zip(tables, totals, strict=True):
            table.rows.append(total_row)
        return dates, tables

    @staticmethod
    def _table(
        title: str,
        sheet: str,
        kind: NumberKind,
        names: list[str],
        day_stats: dict[str, dict[date, LineStat]],
        period_stats: dict[str, LineStat],
        field: str,
        assessment_field: str | None,
    ) -> MatrixTable:
        def cell(stat: LineStat) -> MatrixCell:
            assessment = getattr(stat, assessment_field) if assessment_field else None
            return MatrixCell.model_construct(value=getattr(stat, field), assessment=assessment)

        rows = [
            MatrixRow.model_construct(
                line=line,
                is_total=False,
                cells={day: cell(stat) for day, stat in day_stats[line].items()},
                period=cell(period_stats[line]),
            )
            for line in names
        ]
        return MatrixTable.model_construct(title=title, sheet=sheet, kind=kind, rows=rows)

    def _matrix_totals(
        self, facts: ReportFacts, factory: Factory, by_line: dict[str, dict[date, list[CleanRow]]], dates: list[date]
    ) -> list[MatrixRow]:
        """BR-48 total row, for each day and for the period; in the order of the tables."""
        day_rows: defaultdict[date, list[CleanRow]] = defaultdict(list)
        for days in by_line.values():
            for day, rows in days.items():
                day_rows[day].extend(rows)
        day_people: defaultdict[date, Decimal] = defaultdict(lambda: Decimal(0))
        for line, days in by_line.items():
            for day in days:
                day_people[day] += facts.line_sewers.get((factory, line, day), Decimal(0))
        mo8h_cells: dict[date, MatrixCell] = {}
        cm_cells: dict[date, MatrixCell] = {}
        hour_cells: dict[date, MatrixCell] = {}
        people_cells: dict[date, MatrixCell] = {}
        efficiency_cells: dict[date, MatrixCell] = {}
        no_ratio_cells: dict[date, MatrixCell] = {}
        for day in dates:
            goal = self.calc.goal_on(facts.goals.get(factory, []), day)
            cm = total(row.cm_earning for row in day_rows[day])
            hours = facts.factory_hours.get((factory, day))
            mo8h = self.calc.line_mo8h(cm, day_people[day], hours)
            efficiency = self.calc.efficiency_b(day_rows[day])
            mo8h_cells[day] = MatrixCell.model_construct(value=mo8h, assessment=self.calc.assess_mo8h(mo8h, goal))
            cm_cells[day] = MatrixCell.model_construct(value=cm, assessment=None)
            hour_cells[day] = MatrixCell.model_construct(value=hours, assessment=None)
            people_cells[day] = MatrixCell.model_construct(value=day_people[day], assessment=None)
            efficiency_cells[day] = MatrixCell.model_construct(
                value=efficiency, assessment=self.calc.assess_efficiency(efficiency, goal)
            )
            no_ratio_cells[day] = MatrixCell.model_construct(
                value=self.calc.efficiency_no_ratio(day_rows[day]), assessment=None
            )
        goal = self.calc.goal_on(facts.goals.get(factory, []), facts.to_date)
        all_rows = [row for rows in day_rows.values() for row in rows]
        period_cm = total(row.cm_earning for row in all_rows)
        period_hours = average(
            facts.factory_hours[(factory, day)] for day in dates if (factory, day) in facts.factory_hours
        )
        period_people = total(day_people[day] for day in dates)
        period_mo8h = self.calc.line_mo8h(period_cm, period_people, period_hours)
        period_efficiency = self.calc.efficiency_b(all_rows)
        periods = [
            MatrixCell.model_construct(value=period_mo8h, assessment=self.calc.assess_mo8h(period_mo8h, goal)),
            MatrixCell.model_construct(value=period_cm, assessment=None),
            MatrixCell.model_construct(value=period_hours, assessment=None),
            MatrixCell.model_construct(value=average(day_people[day] for day in dates), assessment=None),
            MatrixCell.model_construct(
                value=period_efficiency, assessment=self.calc.assess_efficiency(period_efficiency, goal)
            ),
            MatrixCell.model_construct(value=self.calc.efficiency_no_ratio(all_rows), assessment=None),
        ]
        cells = [mo8h_cells, cm_cells, hour_cells, people_cells, efficiency_cells, no_ratio_cells]
        return [
            MatrixRow.model_construct(line=TOTAL_LINE_LABEL, is_total=True, cells=day_cells, period=period)
            for day_cells, period in zip(cells, periods, strict=True)
        ]
