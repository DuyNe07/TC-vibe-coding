"""Report period and filters (BR-29, BR-30, BR-31)."""

from datetime import date, timedelta

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.sewing_productivity.constants import DAYS_IN_WEEK, FRIDAY_WEEKDAY, MESSAGE_BR30
from backend.features.sewing_productivity.models.clean_values import CleanRow
from backend.features.sewing_productivity.models.upload_values import DateRange


class DateRangeRule(BaseBusinessRule[DateRange]):
    code = "BR-30"
    message = MESSAGE_BR30
    field = "from_date"

    def is_satisfied_by(self, target: DateRange) -> bool:
        return target.from_date is None or target.to_date is None or target.from_date <= target.to_date


class FilterBusiness(BaseBusiness[DateRange]):
    def rules(self) -> tuple[DateRangeRule, ...]:
        return (DateRangeRule(),)

    def ensure_period(self, from_date: date, to_date: date) -> None:
        """BR-30 the from date is not after the to date."""
        self.ensure_valid(DateRange(from_date=from_date, to_date=to_date))

    def default_week(self, latest: date) -> DateRange:
        """BR-31 last full week from Saturday to Friday, whose Friday is not after the newest data day."""
        friday = latest - timedelta(days=(latest.weekday() - FRIDAY_WEEKDAY) % DAYS_IN_WEEK)
        return DateRange(from_date=friday - timedelta(days=DAYS_IN_WEEK - 1), to_date=friday)

    def default_month_start(self, latest: date) -> date:
        """BR-31 first day of the month of the newest data day."""
        return latest.replace(day=1)

    def default_year_start(self, latest: date) -> date:
        """BR-31 (sửa 2026-11-06) Screen 4: 1 January of the year of the newest data day."""
        return latest.replace(month=1, day=1)

    def apply_groups(self, rows: list[CleanRow], customer_groups: set[str], product_groups: set[str]) -> list[CleanRow]:
        """BR-29 the rows kept by the customer and product filters (an empty filter keeps everything)."""
        return [
            row
            for row in rows
            if (not customer_groups or row.customer_group in customer_groups)
            and (not product_groups or row.product_group in product_groups)
        ]
