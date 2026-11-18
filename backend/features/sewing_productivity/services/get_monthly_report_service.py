"""UC-08: each factory day by day, with a total row. UC-29: the period report of Screen 4 (same call, with a period
kind: the app keeps one call per screen report)."""

from collections.abc import Callable

from backend.core.base import BaseService
from backend.features.sewing_productivity.builders.monthly_builders import MonthlyReportResponseBuilder
from backend.features.sewing_productivity.builders.period_builders import PERIOD_FIELDS, PeriodReportResponseBuilder
from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.business.period_business import PeriodBusiness
from backend.features.sewing_productivity.business.report_business import CodeDays, ReportBusiness
from backend.features.sewing_productivity.constants import MIN_PERIODS_TO_COMPARE
from backend.features.sewing_productivity.dto.monthly_dto import MonthlyReportRequest, MonthlyReportResponse, PeriodKind
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.models.report_values import PeriodSummaries
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source


class GetMonthlyReportService(BaseService[MonthlyReportRequest, MonthlyReportResponse]):
    def __init__(self, loader: Callable[[], ReportSource] = load_report_source) -> None:
        self.loader = loader
        self.filters = FilterBusiness()
        self.reports = ReportBusiness()
        self.periods = PeriodBusiness()

    def execute(self, request: MonthlyReportRequest) -> MonthlyReportResponse:
        self.filters.ensure_period(request.from_date, request.to_date)
        if request.period_kind is not None:
            return self._period_report(request, request.period_kind)
        facts = self.reports.facts(self.loader(), request.from_date, request.to_date, request.factories)
        tables = {}
        for factory in facts.factories:
            days = self.reports.factory_days(facts, factory)
            tables[factory.value] = [*days, self.reports.factory_total(facts, factory)] if days else []
        self.logger.info("Monthly report %s..%s factories=%s", request.from_date, request.to_date, len(tables))
        return MonthlyReportResponseBuilder(tables, self.reports.has_data(facts)).build()

    def _period_report(self, request: MonthlyReportRequest, kind: PeriodKind) -> MonthlyReportResponse:
        """UC-29 (Screen 4 since 2026-11-06): the periods of BR-68, each with the Screen 1 figures of BR-69, and the
        cards of the last period compared with the same number of days of the period before it (BR-70, BR-71). Since
        2026-11-13 also Matching strength and Changeover/line/day (BR-89)."""
        source = self.loader()
        periods = self.periods.periods(request.from_date, request.to_date, kind)
        code_days = self.reports.code_days(source, request.factories)  # BR-87, BR-89: once for every period
        summaries = self.reports.period_summaries(source, periods, request.factories, code_days)
        compared = self._compared(source, summaries, request, code_days)
        changes = self.periods.changes(summaries[-1], compared, PERIOD_FIELDS) if compared else {}
        self.logger.info(
            "Period report %s %s..%s: %s periods, %s with data, cards compared with %s",
            kind.value,
            request.from_date,
            request.to_date,
            len(periods),
            len(summaries),
            compared.period.label if compared else "nothing",
        )
        return PeriodReportResponseBuilder(
            summaries,
            compare_label=compared.period.label if compared else "",
            changes=changes,
            rising_is_good={field: self.periods.rising_is_good(field) for field in PERIOD_FIELDS},
        ).build()

    def _compared(
        self,
        source: ReportSource,
        summaries: list[PeriodSummaries],
        request: MonthlyReportRequest,
        code_days: CodeDays,
    ) -> PeriodSummaries | None:
        """BR-71 the figures of the previous period on the same number of days; None with one period or no data."""
        if len(summaries) < MIN_PERIODS_TO_COMPARE:
            return None
        days = self.periods.comparison_range(summaries[-1].period, summaries[-2].period)
        found = self.reports.period_summaries(source, [days], request.factories, code_days)
        return found[0] if found else None
