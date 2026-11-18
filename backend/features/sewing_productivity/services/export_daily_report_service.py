"""UC-12: Excel file of the daily report, all 4 factories."""

from collections.abc import Callable

from backend.core.base import BaseService, FileDownloadDTO
from backend.features.sewing_productivity.builders.daily_builders import DailyReportFileBuilder
from backend.features.sewing_productivity.business.line_report_business import LineReportBusiness
from backend.features.sewing_productivity.business.report_business import ReportBusiness
from backend.features.sewing_productivity.constants import ALL_FACTORIES
from backend.features.sewing_productivity.dto.export_dto import ExportDailyRequest
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source


class ExportDailyReportService(BaseService[ExportDailyRequest, FileDownloadDTO]):
    def __init__(self, loader: Callable[[], ReportSource] = load_report_source) -> None:
        self.loader = loader
        self.reports = ReportBusiness()
        self.lines = LineReportBusiness()

    def execute(self, request: ExportDailyRequest) -> FileDownloadDTO:
        facts = self.reports.facts(self.loader(), request.report_date, request.report_date)
        summaries = [self.reports.daily_summary(facts, factory) for factory in ALL_FACTORIES]
        hcm = self.reports.hcm_daily_summary(facts)
        if hcm:
            summaries.append(hcm)
        rows = []
        for factory in ALL_FACTORIES:
            day_rows = self.lines.day_rows(facts, factory)
            if day_rows:
                rows.extend([*day_rows, self.lines.day_total_row(facts, factory, day_rows)])
        self.logger.info("Export daily report %s lines=%s", request.report_date, len(rows))
        return DailyReportFileBuilder(request.report_date, summaries, rows, request.english).build()
