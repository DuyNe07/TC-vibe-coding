"""UC-11: Excel file of the weekly report."""

from collections.abc import Callable

from backend.core.base import BaseService, FileDownloadDTO
from backend.features.sewing_productivity.builders.line_detail_builders import WeeklyReportFileBuilder
from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.business.line_report_business import LineReportBusiness
from backend.features.sewing_productivity.business.report_business import ReportBusiness
from backend.features.sewing_productivity.constants import ALL_FACTORIES
from backend.features.sewing_productivity.dto.export_dto import ExportWeeklyRequest
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source


class ExportWeeklyReportService(BaseService[ExportWeeklyRequest, FileDownloadDTO]):
    def __init__(self, loader: Callable[[], ReportSource] = load_report_source) -> None:
        self.loader = loader
        self.filters = FilterBusiness()
        self.reports = ReportBusiness()
        self.lines = LineReportBusiness()

    def execute(self, request: ExportWeeklyRequest) -> FileDownloadDTO:
        self.filters.ensure_period(request.from_date, request.to_date)
        facts = self.reports.facts(
            self.loader(),
            request.from_date,
            request.to_date,
            request.factories,
            request.customer_groups,
            request.product_groups,
        )
        summaries = [self.reports.factory_summary(facts, factory) for factory in ALL_FACTORIES]
        lines = {}
        for factory in ALL_FACTORIES:
            rows = self.lines.line_rows(facts, factory) if factory in facts.factories else []
            lines[factory.value] = [*rows, self.lines.factory_total_row(facts, factory)] if rows else []
        self.logger.info("Export weekly report %s..%s", request.from_date, request.to_date)
        return WeeklyReportFileBuilder(request.from_date, request.to_date, summaries, lines).build()
