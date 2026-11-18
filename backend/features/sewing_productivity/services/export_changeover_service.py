"""UC-15: Excel file of the changeover report. UC-32: the same call with `line_performance` gives the Line
performance file of Screen 6 (the app keeps one call per screen file)."""

from collections.abc import Callable

from backend.core.base import BaseService, FileDownloadDTO
from backend.features.sewing_productivity.builders.changeover_builders import ChangeoverFileBuilder
from backend.features.sewing_productivity.builders.line_performance_file_builders import LinePerformanceFileBuilder
from backend.features.sewing_productivity.business.changeover_business import ChangeoverBusiness
from backend.features.sewing_productivity.business.cleaning_business import CleaningBusiness
from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.business.line_performance_business import LinePerformanceBusiness
from backend.features.sewing_productivity.business.report_business import ReportBusiness
from backend.features.sewing_productivity.constants import ALL_FACTORIES
from backend.features.sewing_productivity.dto.changeover_dto import ChangeoverRequest
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source


class ExportChangeoverService(BaseService[ChangeoverRequest, FileDownloadDTO]):
    def __init__(self, loader: Callable[[], ReportSource] = load_report_source) -> None:
        self.loader = loader
        self.filters = FilterBusiness()
        self.cleaning = CleaningBusiness()
        self.changeover = ChangeoverBusiness()
        self.reports = ReportBusiness()
        self.performance = LinePerformanceBusiness()

    def execute(self, request: ChangeoverRequest) -> FileDownloadDTO:
        self.filters.ensure_period(request.from_date, request.to_date)
        source = self.loader()
        if request.line_performance:
            return self._line_performance(source, request)
        lookup = self.cleaning.name_lookup(source.production, source.targets)
        history = self.cleaning.clean(source.production, lookup, source.catalogs)
        report = self.changeover.report(
            history,
            source.weekly_changeovers,
            request.from_date,
            request.to_date,
            tuple(request.factories),
            request.lines,
        )
        self.logger.info("Export changeover %s..%s", request.from_date, request.to_date)
        return ChangeoverFileBuilder(request.from_date, request.to_date, report, request.english).build()

    def _line_performance(self, source: ReportSource, request: ChangeoverRequest) -> FileDownloadDTO:
        """UC-32 (since 2026-11-12): the Line performance table as an Excel file (BR-85); since 2026-11-13 one sheet
        per factory, all 4 factories whatever the factory chosen on the screen."""
        factories = list(ALL_FACTORIES)  # BR-98: never the closed factory
        facts = self.reports.facts(source, request.from_date, request.to_date, factories)
        by_factory = {factory: self.performance.rows(facts, factory) for factory in factories}
        self.logger.info(
            "Export line performance %s..%s: rows per factory %s", request.from_date, request.to_date,
            {factory.value: len(rows) for factory, rows in by_factory.items()},
        )  # fmt: skip
        return LinePerformanceFileBuilder(request.from_date, request.to_date, by_factory).build()
