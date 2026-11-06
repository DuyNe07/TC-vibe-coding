"""Style changeovers (BR-12 via the clean rows, BR-32 to BR-38, BR-41)."""

from calendar import monthrange
from collections import defaultdict
from datetime import date
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.sewing_productivity.constants import ALL_FACTORIES
from backend.features.sewing_productivity.models.clean_values import CleanRow, line_sort_key
from backend.features.sewing_productivity.models.enums import Factory
from backend.features.sewing_productivity.models.report_values import (
    ChangeoverCount,
    ChangeoverDetail,
    ChangeoverLineCount,
    ChangeoverReport,
)
from backend.features.sewing_productivity.models.settings_records import WeeklyChangeover

PAIR_PLACES = 6
MONTHS_IN_YEAR = 12


def pair_of(row: CleanRow) -> tuple[Decimal, Decimal]:
    """One SMV with one CM price. Rounded far below any real value: Excel formulas leave noise in the last digits."""
    return round(row.smv, PAIR_PLACES), round(row.cm_price, PAIR_PLACES)


class ChangeoverBusiness(BaseBusiness[CleanRow]):
    def usable_rows(self, rows: list[CleanRow]) -> list[CleanRow]:
        """BR-37 rows without SMV are not counted in BR-32 and BR-36."""
        return [row for row in rows if row.smv is not None]

    def kpi_rows(self, line_rows: list[CleanRow], from_date: date, to_date: date) -> list[CleanRow]:
        """BR-32 on one line: orders first seen on the line (whole history) in the period; each pair counts once.

        Only the rows of an order's first day count: a later correction of its SMV is not a new changeover.
        Returns the row where each counted pair first appears. `line_rows` is the whole history of the line."""
        first_day: dict[str, date] = {}
        ordered = sorted(line_rows, key=lambda row: (row.production_date, row.base_po, row.style))
        for row in ordered:
            first_day.setdefault(row.base_po, row.production_date)
        seen: set[tuple[Decimal, Decimal]] = set()
        counted: list[CleanRow] = []
        for row in ordered:
            if row.production_date != first_day[row.base_po] or not from_date <= row.production_date <= to_date:
                continue
            pair = pair_of(row)
            if pair not in seen:
                seen.add(pair)
                counted.append(row)
        return counted

    def rerun_count(self, line_rows: list[CleanRow], from_date: date, to_date: date) -> int:
        """BR-36 on one line: per day in the period, each pair the previous working day of the line did not run.

        The previous working day is read in the whole history; a day off is not a gap; the first time also counts."""
        pairs_by_day: defaultdict[date, set[tuple[Decimal, Decimal]]] = defaultdict(set)
        for row in line_rows:
            pairs_by_day[row.production_date].add(pair_of(row))
        count = 0
        previous: set[tuple[Decimal, Decimal]] = set()
        for day in sorted(pairs_by_day):
            if day > to_date:
                break
            if day >= from_date:
                count += len(pairs_by_day[day] - previous)
            previous = pairs_by_day[day]
        return count

    def working_days(self, rows: list[CleanRow]) -> int:
        """BR-33 number of days with output."""
        return len({row.production_date for row in rows if row.quantity > 0})

    def line_count(self, rows: list[CleanRow]) -> int:
        """BR-34 number of lines with output."""
        return len({row.line for row in rows if row.quantity > 0})

    def kpi(self, kpi_count: int, working_days: int, line_count: int) -> Decimal | None:
        """BR-35 changeover KPI = KPI changeovers / working days / lines."""
        if not working_days or not line_count:
            return None
        return Decimal(kpi_count) / Decimal(working_days) / Decimal(line_count)

    def weekly_count(
        self, entries: list[WeeklyChangeover], factory: Factory, from_date: date, to_date: date
    ) -> int | None:
        """BR-38 the weekly number shows only when the period is exactly the one entered for the factory."""
        for entry in entries:
            if entry.factory == factory and entry.from_date == from_date and entry.to_date == to_date:
                return entry.changeover_count
        return None

    def weekly_per_line(self, weekly: int | None, line_count: int) -> Decimal | None:
        """BR-41 weekly changeovers per line = weekly changeovers / lines of BR-34."""
        return Decimal(weekly) / Decimal(line_count) if weekly is not None and line_count else None

    def month_ranges(self, from_date: date, to_date: date) -> list[tuple[str, date, date]]:
        """Each calendar month of the period, cut to the period (the monthly table counts them separately)."""
        ranges: list[tuple[str, date, date]] = []
        year, month = from_date.year, from_date.month
        while (year, month) <= (to_date.year, to_date.month):
            start = max(from_date, date(year, month, 1))
            end = min(to_date, date(year, month, monthrange(year, month)[1]))
            ranges.append((f"{month:02d}/{year}", start, end))
            year, month = (year + 1, 1) if month == MONTHS_IN_YEAR else (year, month + 1)
        return ranges

    def report(
        self,
        rows: list[CleanRow],
        weekly: list[WeeklyChangeover],
        from_date: date,
        to_date: date,
        factories: tuple[Factory, ...] = (),
        lines: list[str] | None = None,
    ) -> ChangeoverReport:
        """UC-10 all the tables of Screen 6. `rows` is the whole stored history."""
        chosen = factories or ALL_FACTORIES
        wanted = set(lines or ())
        kept = [row for row in rows if row.factory in chosen and (not wanted or row.line in wanted)]
        history: defaultdict[tuple[Factory, str], list[CleanRow]] = defaultdict(list)
        for row in self.usable_rows(kept):
            history[(row.factory, row.line)].append(row)
        in_period = [row for row in kept if from_date <= row.production_date <= to_date]
        by_factory = [
            self._count(factory, "", kept, history, from_date, to_date, weekly)
            for factory in chosen
            if any(row.factory == factory for row in in_period)
        ]
        by_month = [
            self._count(factory, month, kept, history, start, end, [])
            for month, start, end in self.month_ranges(from_date, to_date)
            for factory in chosen
            if any(row.factory == factory and start <= row.production_date <= end for row in in_period)
        ]
        return ChangeoverReport(
            has_data=bool(in_period),
            total_kpi_count=sum(count.kpi_count for count in by_factory),
            total_rerun_count=sum(count.rerun_count for count in by_factory),
            by_factory=by_factory,
            by_month=by_month,
            by_line=self._line_counts(in_period, history, from_date, to_date),
            details=self._details(history, from_date, to_date),
        )

    def _count(
        self,
        factory: Factory,
        month: str,
        rows: list[CleanRow],
        history: dict[tuple[Factory, str], list[CleanRow]],
        from_date: date,
        to_date: date,
        weekly: list[WeeklyChangeover],
    ) -> ChangeoverCount:
        histories = [line_rows for (key_factory, _line), line_rows in history.items() if key_factory == factory]
        period = [row for row in rows if row.factory == factory and from_date <= row.production_date <= to_date]
        kpi_count = sum(len(self.kpi_rows(line_rows, from_date, to_date)) for line_rows in histories)
        days = self.working_days(period)
        lines = self.line_count(period)
        return ChangeoverCount(
            factory=factory,
            month=month,
            kpi_count=kpi_count,
            working_days=days,
            line_count=lines,
            kpi=self.kpi(kpi_count, days, lines),
            rerun_count=sum(self.rerun_count(line_rows, from_date, to_date) for line_rows in histories),
            weekly_count=self.weekly_count(weekly, factory, from_date, to_date),
        )

    def _line_counts(
        self,
        in_period: list[CleanRow],
        history: dict[tuple[Factory, str], list[CleanRow]],
        from_date: date,
        to_date: date,
    ) -> list[ChangeoverLineCount]:
        keys = sorted({(row.factory, row.line) for row in in_period}, key=lambda key: (key[0], line_sort_key(key[1])))
        return [
            ChangeoverLineCount(
                factory=factory,
                line=line,
                kpi_count=len(self.kpi_rows(history.get((factory, line), []), from_date, to_date)),
                rerun_count=self.rerun_count(history.get((factory, line), []), from_date, to_date),
            )
            for factory, line in keys
        ]

    def _details(
        self, history: dict[tuple[Factory, str], list[CleanRow]], from_date: date, to_date: date
    ) -> list[ChangeoverDetail]:
        details = [
            ChangeoverDetail(
                day=row.production_date,
                factory=factory,
                line=line,
                base_po=row.base_po,
                style=row.style,
                smv=row.smv,
                cm_price=row.cm_price,
            )
            for (factory, line), line_rows in history.items()
            for row in self.kpi_rows(line_rows, from_date, to_date)
        ]
        details.sort(key=lambda item: (item.day, item.factory, line_sort_key(item.line)))
        return details
