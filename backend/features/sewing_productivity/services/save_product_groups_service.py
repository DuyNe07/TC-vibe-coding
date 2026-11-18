"""UC-22: save the product groups; every report uses them at once."""

from backend.core.base import BaseService
from backend.features.sewing_productivity.business.access_rules import AccessBusiness
from backend.features.sewing_productivity.business.record_sync import rows_to_write
from backend.features.sewing_productivity.business.settings_business import SettingsBusiness
from backend.features.sewing_productivity.dto.catalog_dto import SaveCatalogResponse, SaveProductGroupsRequest
from backend.features.sewing_productivity.repositories.settings_repositories import ProductGroupRuleRepository


class SaveProductGroupsService(BaseService[SaveProductGroupsRequest, SaveCatalogResponse]):
    def __init__(self, repository: ProductGroupRuleRepository | None = None) -> None:
        self.repository = repository or ProductGroupRuleRepository()
        self.access = AccessBusiness()
        self.settings = SettingsBusiness()

    def execute(self, request: SaveProductGroupsRequest) -> SaveCatalogResponse:
        user = self.current_user
        self.access.ensure_valid(user)
        values = self.settings.catalog_pairs([(row.product_name, row.product_group) for row in request.rows])
        self.settings.ensure_catalog(values)
        self.repository.list_seeded()
        writes = rows_to_write(
            self.repository.list_all(),
            self.repository.list_deleted(),
            self.settings.product_group_rules(values),
            lambda _row: True,
            self.access.deleted_by(user),
        )
        if writes:
            self.repository.save_many(writes)
        self.logger.info("Catalog saved: %s rows sent, %s rows written", len(values.pairs), len(writes))
        return SaveCatalogResponse(message="Đã lưu nhóm sản phẩm.")
