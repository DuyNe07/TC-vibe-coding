"""UC-04: the overview table, one column per factory."""

from collections.abc import Callable

from backend.core.base import BaseService
from backend.features.sewing_productivity.builders.overview_builders import OverviewResponseBuilder
from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.business.report_business import ReportBusiness
from backend.features.sewing_productivity.constants import ALL_FACTORIES
from backend.features.sewing_productivity.dto.overview_dto import OverviewRequest, OverviewResponse
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source


class GetOverviewService(BaseService[OverviewRequest, OverviewResponse]):
    def __init__(self, loader: Callable[[], ReportSource] = load_report_source) -> None:
        self.loader = loader
        self.filters = FilterBusiness()
        self.reports = ReportBusiness()

    def execute(self, request: OverviewRequest) -> OverviewResponse:
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
        has_data = self.reports.has_data(facts)
        self.logger.info(
            "Overview %s..%s filtered=%s has_data=%s", request.from_date, request.to_date, facts.filtered, has_data
        )
        return OverviewResponseBuilder(summaries, self.reports.efficiency_a_note(facts), has_data).build()
