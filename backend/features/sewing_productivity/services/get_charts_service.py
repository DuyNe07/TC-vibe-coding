"""UC-05: the data of the overview charts."""

from collections.abc import Callable

from backend.core.base import BaseService
from backend.features.sewing_productivity.builders.overview_builders import ChartsResponseBuilder
from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.business.report_business import ReportBusiness
from backend.features.sewing_productivity.constants import MESSAGE_NOT_APPLICABLE
from backend.features.sewing_productivity.dto.overview_dto import ChartsRequest, ChartsResponse
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source


class GetChartsService(BaseService[ChartsRequest, ChartsResponse]):
    def __init__(self, loader: Callable[[], ReportSource] = load_report_source) -> None:
        self.loader = loader
        self.filters = FilterBusiness()
        self.reports = ReportBusiness()

    def execute(self, request: ChartsRequest) -> ChartsResponse:
        self.filters.ensure_period(request.from_date, request.to_date)
        facts = self.reports.facts(
            self.loader(),
            request.from_date,
            request.to_date,
            request.factories,
            request.customer_groups,
            request.product_groups,
        )
        days = [stat for factory in facts.factories for stat in self.reports.factory_days(facts, factory)]
        summaries = [self.reports.factory_summary(facts, factory) for factory in facts.factories]
        top_lines, bottom_lines = self.reports.line_ranking(facts, request.ranking_metric)
        message = MESSAGE_NOT_APPLICABLE if facts.filtered else ""
        self.logger.info(
            "Charts %s..%s metric=%s days=%s", request.from_date, request.to_date, request.ranking_metric, len(days)
        )
        return ChartsResponseBuilder(
            days, summaries, top_lines, bottom_lines, message, self.reports.has_data(facts)
        ).build()
