"""UC-14: Excel file of the MO tables."""

from collections.abc import Callable

from backend.core.base import BaseService, FileDownloadDTO
from backend.features.sewing_productivity.builders.line_mo_builders import LineMoFileBuilder
from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.business.line_report_business import LineReportBusiness
from backend.features.sewing_productivity.business.report_business import ReportBusiness
from backend.features.sewing_productivity.dto.line_mo_dto import LineMoRequest
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source


class ExportLineMoService(BaseService[LineMoRequest, FileDownloadDTO]):
    def __init__(self, loader: Callable[[], ReportSource] = load_report_source) -> None:
        self.loader = loader
        self.filters = FilterBusiness()
        self.reports = ReportBusiness()
        self.lines = LineReportBusiness()

    def execute(self, request: LineMoRequest) -> FileDownloadDTO:
        self.filters.ensure_period(request.from_date, request.to_date)
        facts = self.reports.facts(self.loader(), request.from_date, request.to_date, [request.factory])
        dates, tables = self.lines.mo_tables(facts, request.factory, request.lines)
        self.logger.info("Export line MO %s %s..%s", request.factory, request.from_date, request.to_date)
        return LineMoFileBuilder(
            request.factory, request.from_date, request.to_date, dates, tables, request.english
        ).build()
