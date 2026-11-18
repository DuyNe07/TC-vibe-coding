"""UC-09: the 5 tables of one factory, lines in rows and days in columns."""

from collections.abc import Callable

from backend.core.base import BaseService
from backend.features.sewing_productivity.builders.line_mo_builders import LineMoResponseBuilder
from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.business.line_report_business import LineReportBusiness
from backend.features.sewing_productivity.business.report_business import ReportBusiness
from backend.features.sewing_productivity.dto.line_mo_dto import LineMoRequest, LineMoResponse
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source


class GetLineMoService(BaseService[LineMoRequest, LineMoResponse]):
    def __init__(self, loader: Callable[[], ReportSource] = load_report_source) -> None:
        self.loader = loader
        self.filters = FilterBusiness()
        self.reports = ReportBusiness()
        self.lines = LineReportBusiness()

    def execute(self, request: LineMoRequest) -> LineMoResponse:
        self.filters.ensure_period(request.from_date, request.to_date)
        facts = self.reports.facts(self.loader(), request.from_date, request.to_date, [request.factory])
        dates, tables = self.lines.mo_tables(facts, request.factory, request.lines)
        self.logger.info("Line MO %s %s..%s days=%s", request.factory, request.from_date, request.to_date, len(dates))
        return LineMoResponseBuilder(dates, tables, bool(dates)).build()
