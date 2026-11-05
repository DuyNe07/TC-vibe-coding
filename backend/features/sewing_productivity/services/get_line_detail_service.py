"""UC-06: lines day by day for one factory."""

from collections.abc import Callable

from backend.core.base import BaseService
from backend.features.sewing_productivity.builders.line_detail_builders import LineDetailResponseBuilder
from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.business.line_report_business import LineReportBusiness
from backend.features.sewing_productivity.business.report_business import ReportBusiness
from backend.features.sewing_productivity.dto.line_detail_dto import LineDetailRequest, LineDetailResponse
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source


class GetLineDetailService(BaseService[LineDetailRequest, LineDetailResponse]):
    def __init__(self, loader: Callable[[], ReportSource] = load_report_source) -> None:
        self.loader = loader
        self.filters = FilterBusiness()
        self.reports = ReportBusiness()
        self.lines = LineReportBusiness()

    def execute(self, request: LineDetailRequest) -> LineDetailResponse:
        self.filters.ensure_period(request.from_date, request.to_date)
        facts = self.reports.facts(
            self.loader(),
            request.from_date,
            request.to_date,
            [request.factory],
            request.customer_groups,
            request.product_groups,
        )
        has_data = self.reports.has_data(facts)
        rows = self.lines.line_rows(facts, request.factory, request.lines)
        if has_data:
            rows.append(self.lines.factory_total_row(facts, request.factory))
        days = self.reports.factory_days(facts, request.factory)
        self.logger.info(
            "Line detail %s %s..%s rows=%s", request.factory, request.from_date, request.to_date, len(rows)
        )
        return LineDetailResponseBuilder(rows, days, self.reports.efficiency_a_note(facts), has_data).build()
