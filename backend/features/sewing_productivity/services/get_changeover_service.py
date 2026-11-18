"""UC-10: style changeovers. UC-31: the same call with `line_performance` gives Screen 6 Line performance (the app
keeps one call per screen report)."""

from collections.abc import Callable

from backend.core.base import BaseService
from backend.features.sewing_productivity.builders.changeover_builders import ChangeoverResponseBuilder
from backend.features.sewing_productivity.builders.line_performance_builders import LinePerformanceResponseBuilder
from backend.features.sewing_productivity.business.changeover_business import ChangeoverBusiness
from backend.features.sewing_productivity.business.cleaning_business import CleaningBusiness
from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.business.line_performance_business import LinePerformanceBusiness
from backend.features.sewing_productivity.business.report_business import ReportBusiness
from backend.features.sewing_productivity.dto.changeover_dto import ChangeoverRequest, ChangeoverResponse, Factory
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source


class GetChangeoverService(BaseService[ChangeoverRequest, ChangeoverResponse]):
    def __init__(self, loader: Callable[[], ReportSource] = load_report_source) -> None:
        self.loader = loader
        self.filters = FilterBusiness()
        self.cleaning = CleaningBusiness()
        self.changeover = ChangeoverBusiness()
        self.reports = ReportBusiness()
        self.performance = LinePerformanceBusiness()

    def execute(self, request: ChangeoverRequest) -> ChangeoverResponse:
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
        self.logger.info("Changeover %s..%s counted=%s", request.from_date, request.to_date, report.total_kpi_count)
        return ChangeoverResponseBuilder(report).build()

    def _line_performance(self, source: ReportSource, request: ChangeoverRequest) -> ChangeoverResponse:
        """UC-31 (Screen 6 since 2026-11-11): each line of one factory and the factory total (BR-78 to BR-80)."""
        factory = request.factories[0] if request.factories else Factory.FAC_1
        facts = self.reports.facts(source, request.from_date, request.to_date, [factory])
        rows = self.performance.rows(facts, factory)
        self.logger.info(
            "Line performance %s %s..%s: %s lines", factory.value, request.from_date, request.to_date,
            max(len(rows) - 1, 0),
        )  # fmt: skip
        return LinePerformanceResponseBuilder(rows).build()
