"""UC-21: the 4 catalogs and what they are still missing. UC-34: the same call gives the line strengths (read only)."""

from collections.abc import Callable

from backend.core.base import BaseService, EmptyRequest
from backend.features.sewing_productivity.builders.line_overview_builders import strength_dtos
from backend.features.sewing_productivity.builders.settings_builders import CatalogsResponseBuilder
from backend.features.sewing_productivity.business.access_rules import AccessBusiness
from backend.features.sewing_productivity.business.catalog_business import CatalogBusiness
from backend.features.sewing_productivity.business.cleaning_business import CleaningBusiness
from backend.features.sewing_productivity.dto.catalog_dto import CatalogsResponse
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source
from backend.features.sewing_productivity.repositories.settings_repositories import (
    CustomerGroupRuleRepository,
    LineMappingRuleRepository,
    ProductGroupRuleRepository,
    StyleProductRuleRepository,
)
from backend.features.sewing_productivity.repositories.source_repositories import LineStrengthRepository


class GetCatalogsService(BaseService[EmptyRequest, CatalogsResponse]):
    def __init__(self, loader: Callable[[], ReportSource] = load_report_source) -> None:
        self.loader = loader
        self.access = AccessBusiness()
        self.cleaning = CleaningBusiness()
        self.catalogs = CatalogBusiness()

    def execute(self, request: EmptyRequest) -> CatalogsResponse:
        self.access.ensure_valid(self.current_user)
        source = self.loader()
        lookup = self.cleaning.name_lookup(source.production, source.targets)
        rows = self.cleaning.clean(source.production, lookup, source.catalogs)
        strengths = LineStrengthRepository().list_all()
        self.logger.info("Catalogs read over %s rows, %s line strengths", len(rows), len(strengths))
        response = CatalogsResponseBuilder(
            ProductGroupRuleRepository().list_seeded(),
            CustomerGroupRuleRepository().list_seeded(),
            LineMappingRuleRepository().list_seeded(),
            StyleProductRuleRepository().list_all(),
            self.catalogs.unclassified_names(rows),
            self.catalogs.customer_names(rows),
            self.catalogs.styles_without_name(rows),
        ).build()
        return response.model_copy(update={"line_strengths": strength_dtos(strengths)})  # UC-34
