"""BR-68: cutting the chosen dates of Screen 4 into weeks, months, quarters or years. BR-70, BR-71: the cards of
Screen 4 (the last period against the same number of days of the period before it)."""

from collections.abc import Iterable
from datetime import date, timedelta
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.sewing_productivity.models.enums import PeriodKind
from backend.features.sewing_productivity.models.report_values import PeriodRange, PeriodSummaries

# BR-70 the figures (attributes of FactorySummary) whose rise is good: green up, red down; the others are not coloured
RISING_IS_GOOD = frozenset({"mo8h", "efficiency_b", "output", "cm_earning", "strength_match"})  # BR-70
SATURDAY_WEEKDAY = 5
DAYS_IN_WEEK = 7
MONTHS_IN_QUARTER = 3
MONTH_NAMES = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _days(first: date, last: date) -> str:
    return f"{first:%d.%m}–{last:%d.%m}"


def _month_end(day: date) -> date:
    following = date(day.year + day.month // 12, day.month % 12 + 1, 1)
    return following - timedelta(days=1)


class PeriodBusiness(BaseBusiness[PeriodRange]):
    def periods(self, from_date: date, to_date: date, kind: PeriodKind) -> list[PeriodRange]:
        """BR-68 the periods from the first to the last chosen day, each cut to the chosen days.

        A week runs Saturday to Friday and takes the ISO week number of its Friday ("W43 (17.10–23.10)"); months,
        quarters and years follow the calendar. A period cut by the chosen dates shows its real days in its name."""
        result: list[PeriodRange] = []
        start = self._period_start(from_date, kind)
        while start <= to_date:
            end = self._period_end(start, kind)
            first, last = max(start, from_date), min(end, to_date)
            name = self._name(start, end, kind)
            if kind == PeriodKind.WEEK or (first, last) != (start, end):
                name = f"{name} ({_days(first, last)})"
            result.append(PeriodRange(label=name, from_date=first, to_date=last))
            start = end + timedelta(days=1)
        return result

    def comparison_range(self, last: PeriodRange, previous: PeriodRange) -> PeriodRange:
        """BR-71 the days of the previous period that the last one is compared with: as many calendar days as the last
        period has, from the first day of the previous period, never after its last day ("vs W44 (24.10–29.10)")."""
        end = min(previous.from_date + (last.to_date - last.from_date), previous.to_date)
        name = previous.label.split(" (")[0]
        return PeriodRange(
            label=f"vs {name} ({_days(previous.from_date, end)})", from_date=previous.from_date, to_date=end
        )

    @staticmethod
    def rising_is_good(field: str) -> bool | None:
        """BR-70 True: a rise is good (green) and a fall bad (red); None: the arrow is not coloured."""
        return True if field in RISING_IS_GOOD else None

    @staticmethod
    def changes(
        last: PeriodSummaries, compared: PeriodSummaries, fields: Iterable[str]
    ) -> dict[tuple[str, str], Decimal | None]:
        """BR-71 last period - compared days, per (figure, column); None when either number is missing ("-")."""
        before = {summary.column: summary for summary in compared.summaries}
        result: dict[tuple[str, str], Decimal | None] = {}
        for field in fields:
            for summary in last.summaries:
                current = getattr(summary, field)
                other = getattr(before[summary.column], field) if summary.column in before else None
                result[field, summary.column] = None if current is None or other is None else current - other
        return result

    @staticmethod
    def _period_start(day: date, kind: PeriodKind) -> date:
        if kind == PeriodKind.WEEK:
            return day - timedelta(days=(day.weekday() - SATURDAY_WEEKDAY) % DAYS_IN_WEEK)
        if kind == PeriodKind.MONTH:
            return day.replace(day=1)
        if kind == PeriodKind.QUARTER:
            return date(day.year, (day.month - 1) // MONTHS_IN_QUARTER * MONTHS_IN_QUARTER + 1, 1)
        return date(day.year, 1, 1)

    @staticmethod
    def _period_end(start: date, kind: PeriodKind) -> date:
        if kind == PeriodKind.WEEK:
            return start + timedelta(days=DAYS_IN_WEEK - 1)
        if kind == PeriodKind.MONTH:
            return _month_end(start)
        if kind == PeriodKind.QUARTER:
            return _month_end(date(start.year, start.month + MONTHS_IN_QUARTER - 1, 1))
        return date(start.year, 12, 31)

    @staticmethod
    def _name(start: date, end: date, kind: PeriodKind) -> str:
        if kind == PeriodKind.WEEK:
            return f"W{end.isocalendar().week}"
        if kind == PeriodKind.MONTH:
            return f"{MONTH_NAMES[start.month - 1]} {start.year}"
        if kind == PeriodKind.QUARTER:
            return f"Q{(start.month - 1) // MONTHS_IN_QUARTER + 1} {start.year}"
        return str(start.year)
