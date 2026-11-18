"""UC-05: the data of the overview charts; since 2026-11-13 also the "Products & customers" figures (BR-93 to
BR-96)."""

from collections.abc import Callable
from datetime import date

from backend.core.base import BaseService
from backend.features.sewing_productivity.builders.overview_builders import ChartsResponseBuilder
from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.business.period_business import PeriodBusiness
from backend.features.sewing_productivity.business.product_mix_business import ProductMixBusiness
from backend.features.sewing_productivity.business.report_business import ReportBusiness
from backend.features.sewing_productivity.constants import MESSAGE_NOT_APPLICABLE, TOTAL_COLUMN
from backend.features.sewing_productivity.dto.overview_dto import ChartsRequest, ChartsResponse
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.models.enums import PeriodKind
from backend.features.sewing_productivity.models.report_values import ProductMix, ReportFacts
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source


class GetChartsService(BaseService[ChartsRequest, ChartsResponse]):
    def __init__(self, loader: Callable[[], ReportSource] = load_report_source) -> None:
        self.loader = loader
        self.filters = FilterBusiness()
        self.reports = ReportBusiness()
        self.mix = ProductMixBusiness()
        self.periods = PeriodBusiness()

    def execute(self, request: ChartsRequest) -> ChartsResponse:
        self.filters.ensure_period(request.from_date, request.to_date)
        source = self.loader()
        facts = self.reports.facts(
            source,
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
            days,
            summaries,
            top_lines,
            bottom_lines,
            message,
            self.reports.has_data(facts),
            self.reports.hcm_days(facts),
            self.reports.hcm_summary(facts),
            self._products(source, request, facts) if request.products else None,
        ).build()

    def _products(self, source: ReportSource, request: ChartsRequest, facts: ReportFacts) -> ProductMix:
        """BR-93 to BR-96: the chosen dates for the mix, customers and CM prices; 01/01 of the year of the "To" date to
        that date for the months. Customer and product filters as the output (BR-29)."""
        shown = [row for factory in facts.factories for row in facts.shown.get(factory, ())]
        keep = self.mix.top_groups(shown)
        columns = [(factory.value, facts.shown.get(factory, [])) for factory in facts.factories]
        columns.append((TOTAL_COLUMN, shown))
        months = self.periods.periods(date(request.to_date.year, 1, 1), request.to_date, PeriodKind.MONTH)
        year = self.reports.facts(
            source,
            months[0].from_date,
            request.to_date,
            request.factories,
            request.customer_groups,
            request.product_groups,
            strengths=[],
        )
        year_rows = [row for factory in year.factories for row in year.shown.get(factory, ())]
        mix = ProductMix(
            shares=[share for column, rows in columns for share in self.mix.shares(column, rows, keep)],
            table=[share for column, rows in columns for share in self.mix.shares(column, rows)],
            customers=self.mix.top_customers(shown),
            cm_prices=self.mix.cm_prices(shown),
            months=self.mix.monthly(year_rows, months, self.mix.top_groups(year_rows)),
        )
        self.logger.info(
            "Products & customers: %s groups kept, %s customers, %s months", len(keep), len(mix.customers), len(months)
        )
        return mix
