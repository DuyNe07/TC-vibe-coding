"""UC-07: results of one day."""

from collections.abc import Callable

from backend.core.base import BaseService
from backend.features.sewing_productivity.builders.daily_builders import DailyReportResponseBuilder
from backend.features.sewing_productivity.business.line_report_business import LineReportBusiness
from backend.features.sewing_productivity.business.report_business import ReportBusiness
from backend.features.sewing_productivity.constants import ALL_FACTORIES
from backend.features.sewing_productivity.dto.daily_dto import DailyReportRequest, DailyReportResponse
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source


class GetDailyReportService(BaseService[DailyReportRequest, DailyReportResponse]):
    def __init__(self, loader: Callable[[], ReportSource] = load_report_source) -> None:
        self.loader = loader
        self.reports = ReportBusiness()
        self.lines = LineReportBusiness()

    def execute(self, request: DailyReportRequest) -> DailyReportResponse:
        facts = self.reports.facts(self.loader(), request.report_date, request.report_date)
        summaries = [self.reports.daily_summary(facts, factory) for factory in ALL_FACTORIES]
        rows = self.lines.day_rows(facts, request.factory)
        if rows:
            rows.append(self.lines.day_total_row(facts, request.factory, rows))
        has_data = self.reports.has_data(facts)
        self.logger.info(
            "Daily report %s %s lines=%s has_data=%s", request.report_date, request.factory, len(rows), has_data
        )
        return DailyReportResponseBuilder(summaries, rows, has_data).build()
