"""UC-15: Excel file of the changeover report."""

from collections.abc import Callable

from backend.core.base import BaseService, FileDownloadDTO
from backend.features.sewing_productivity.builders.changeover_builders import ChangeoverFileBuilder
from backend.features.sewing_productivity.business.changeover_business import ChangeoverBusiness
from backend.features.sewing_productivity.business.cleaning_business import CleaningBusiness
from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.dto.changeover_dto import ChangeoverRequest
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source


class ExportChangeoverService(BaseService[ChangeoverRequest, FileDownloadDTO]):
    def __init__(self, loader: Callable[[], ReportSource] = load_report_source) -> None:
        self.loader = loader
        self.filters = FilterBusiness()
        self.cleaning = CleaningBusiness()
        self.changeover = ChangeoverBusiness()

    def execute(self, request: ChangeoverRequest) -> FileDownloadDTO:
        self.filters.ensure_period(request.from_date, request.to_date)
        source = self.loader()
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
        return ChangeoverFileBuilder(request.from_date, request.to_date, report).build()
