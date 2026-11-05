"""UC-26: filter choices, newest data day and default periods."""

from collections import defaultdict
from collections.abc import Callable

from backend.core.base import BaseService, EmptyRequest
from backend.features.sewing_productivity.builders.settings_builders import FilterOptionsBuilder
from backend.features.sewing_productivity.business.cleaning_business import CleaningBusiness
from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.constants import ALL_FACTORIES
from backend.features.sewing_productivity.dto.filter_dto import FilterOptionsResponse
from backend.features.sewing_productivity.models.clean_values import ReportSource, line_sort_key
from backend.features.sewing_productivity.models.upload_values import DateRange
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source


class GetFilterOptionsService(BaseService[EmptyRequest, FilterOptionsResponse]):
    def __init__(self, loader: Callable[[], ReportSource] = load_report_source) -> None:
        self.loader = loader
        self.cleaning = CleaningBusiness()
        self.filters = FilterBusiness()

    def execute(self, request: EmptyRequest) -> FilterOptionsResponse:
        source = self.loader()
        lookup = self.cleaning.name_lookup(source.production, source.targets)
        rows = self.cleaning.clean(source.production, lookup, source.catalogs)
        lines: defaultdict[str, set[str]] = defaultdict(set)
        for row in rows:
            lines[row.factory.value].add(row.line)
        lines_by_factory = {
            factory.value: sorted(lines[factory.value], key=line_sort_key)
            for factory in ALL_FACTORIES
            if factory.value in lines
        }
        latest = max((row.production_date for row in rows), default=None)
        week = self.filters.default_week(latest) if latest else DateRange()
        month_start = self.filters.default_month_start(latest) if latest else None
        self.logger.info("Filter options over %s rows, newest day %s", len(rows), latest)
        return FilterOptionsBuilder(
            lines_by_factory,
            sorted({row.customer_group for row in rows}),
            sorted({row.product_group for row in rows}),
            latest,
            source.last_upload_at,
            week,
            month_start,
        ).build()
