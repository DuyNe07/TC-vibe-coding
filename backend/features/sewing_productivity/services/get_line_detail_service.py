"""UC-06: lines day by day for one factory; since 2026-11-12 also the Line Detail table (BR-83) and, per line, the base
orders made in the chosen dates with the line's strength (BR-84); since 2026-11-13 Matching ratio by the line
strengths (BR-86), Changeover by code (BR-87), %Efficiency and SMV (BR-83, BR-88)."""

from collections.abc import Callable
from datetime import date, timedelta

from backend.core.base import BaseService
from backend.features.sewing_productivity.builders.line_detail_builders import LineDetailResponseBuilder
from backend.features.sewing_productivity.builders.line_overview_builders import LineTrendResponseBuilder
from backend.features.sewing_productivity.business.changeover_business import ChangeoverBusiness
from backend.features.sewing_productivity.business.cleaning_business import CleaningBusiness
from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.business.line_overview_business import LineOverviewBusiness
from backend.features.sewing_productivity.business.line_report_business import LineReportBusiness
from backend.features.sewing_productivity.business.period_business import PeriodBusiness
from backend.features.sewing_productivity.business.report_business import ReportBusiness
from backend.features.sewing_productivity.constants import TREND_WEEKS
from backend.features.sewing_productivity.dto.line_detail_dto import LineDetailRequest, LineDetailResponse, PeriodKind
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.models.report_values import PeriodRange
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source
from backend.features.sewing_productivity.repositories.source_repositories import LineStrengthRepository


class GetLineDetailService(BaseService[LineDetailRequest, LineDetailResponse]):
    def __init__(
        self,
        loader: Callable[[], ReportSource] = load_report_source,
        strengths: LineStrengthRepository | None = None,
    ) -> None:
        self.loader = loader
        self.strengths = strengths or LineStrengthRepository()
        self.filters = FilterBusiness()
        self.reports = ReportBusiness()
        self.lines = LineReportBusiness()
        self.cleaning = CleaningBusiness()
        self.overview = LineOverviewBusiness()
        self.changeovers = ChangeoverBusiness()
        self.periods = PeriodBusiness()

    def execute(self, request: LineDetailRequest) -> LineDetailResponse:
        self.filters.ensure_period(request.from_date, request.to_date)
        if request.trend_line:
            return self._trend(request)
        source = self.loader()
        lookup = self.cleaning.name_lookup(source.production, source.targets)
        factory_rows = [row for row in source.production if row.factory == request.factory]
        history = self.cleaning.clean(factory_rows, lookup, source.catalogs)
        strengths = [item for item in self.strengths.list_all() if item.factory == request.factory]
        facts = self.reports.facts(
            source,
            request.from_date,
            request.to_date,
            [request.factory],
            request.customer_groups,
            request.product_groups,
            lookup=lookup,
            strengths=strengths,  # BR-86 (sửa 2026-11-13)
            code_days=self.changeovers.code_days(history),  # BR-87 (sửa 2026-11-13): the whole history
        )
        has_data = self.reports.has_data(facts)
        rows = self.lines.line_rows(facts, request.factory, request.lines)
        if has_data:
            rows.append(self.lines.factory_total_row(facts, request.factory))
        days = self.reports.factory_days(facts, request.factory)
        first_days = self.overview.first_days(history, request.factory)
        overview = self.overview.rows(facts, request.factory, request.lines)
        orders = self.overview.orders(facts, request.factory, first_days, {item.line: item for item in strengths})
        self.logger.info(
            "Line detail %s %s..%s rows=%s lines=%s orders=%s strengths=%s", request.factory, request.from_date,
            request.to_date, len(rows), max(len(overview) - 1, 0), len(orders), len(strengths),
        )  # fmt: skip
        return LineDetailResponseBuilder(
            rows, days, self.reports.efficiency_a_note(facts), has_data, overview, orders, strengths
        ).build()

    def _trend_periods(self, to_date: date, kind: PeriodKind) -> list[PeriodRange]:
        """BR-90, BR-91: by week the last weeks up to `to_date` (whole weeks, the first cut one left out); by month or
        year from 01/01 of the year of `to_date`."""
        if kind != PeriodKind.WEEK:
            return self.periods.periods(date(to_date.year, 1, 1), to_date, kind)
        weeks = self.periods.periods(to_date - timedelta(weeks=TREND_WEEKS + 1), to_date, kind)
        return weeks[-TREND_WEEKS:]

    def _trend(self, request: LineDetailRequest) -> LineDetailResponse:
        """BR-90 the "Line trend" of one line, cut into periods (BR-68, BR-91), each with the figures of its Line Detail
        row (customer / product filters applied, BR-29)."""
        source = self.loader()
        lookup = self.cleaning.name_lookup(source.production, source.targets)
        periods = self._trend_periods(request.to_date, request.trend_kind)
        points = []
        for period in periods:
            facts = self.reports.facts(
                source,
                period.from_date,
                period.to_date,
                [request.factory],
                request.customer_groups,
                request.product_groups,
                lookup=lookup,
                strengths=[],  # BR-90 shows no matching
            )
            point = self.overview.trend_point(facts, request.factory, request.trend_line, period)
            if point is not None:
                points.append(point)
        self.logger.info(
            "Line trend %s %s %s up to %s: %s periods, %s with output", request.factory, request.trend_line,
            request.trend_kind.value, request.to_date, len(periods), len(points),
        )  # fmt: skip
        return LineTrendResponseBuilder(points).build()
