"""UC-08: each factory day by day, with a total row."""

from collections.abc import Callable

from backend.core.base import BaseService
from backend.features.sewing_productivity.builders.monthly_builders import MonthlyReportResponseBuilder
from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.business.report_business import ReportBusiness
from backend.features.sewing_productivity.dto.monthly_dto import MonthlyReportRequest, MonthlyReportResponse
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source


class GetMonthlyReportService(BaseService[MonthlyReportRequest, MonthlyReportResponse]):
    def __init__(self, loader: Callable[[], ReportSource] = load_report_source) -> None:
        self.loader = loader
        self.filters = FilterBusiness()
        self.reports = ReportBusiness()

    def execute(self, request: MonthlyReportRequest) -> MonthlyReportResponse:
        self.filters.ensure_period(request.from_date, request.to_date)
        facts = self.reports.facts(self.loader(), request.from_date, request.to_date, request.factories)
        tables = {}
        for factory in facts.factories:
            days = self.reports.factory_days(facts, factory)
            tables[factory.value] = [*days, self.reports.factory_total(facts, factory)] if days else []
        self.logger.info("Monthly report %s..%s factories=%s", request.from_date, request.to_date, len(tables))
        return MonthlyReportResponseBuilder(tables, self.reports.has_data(facts)).build()
