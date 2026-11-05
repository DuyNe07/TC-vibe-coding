"""UC-23: save the customer groups; every report uses them at once."""

from backend.core.base import BaseService
from backend.features.sewing_productivity.business.access_rules import AccessBusiness
from backend.features.sewing_productivity.business.record_sync import rows_to_write
from backend.features.sewing_productivity.business.settings_business import SettingsBusiness
from backend.features.sewing_productivity.dto.catalog_dto import SaveCatalogResponse, SaveCustomerGroupsRequest
from backend.features.sewing_productivity.repositories.settings_repositories import CustomerGroupRuleRepository


class SaveCustomerGroupsService(BaseService[SaveCustomerGroupsRequest, SaveCatalogResponse]):
    def __init__(self, repository: CustomerGroupRuleRepository | None = None) -> None:
        self.repository = repository or CustomerGroupRuleRepository()
        self.access = AccessBusiness()
        self.settings = SettingsBusiness()

    def execute(self, request: SaveCustomerGroupsRequest) -> SaveCatalogResponse:
        user = self.current_user
        self.access.ensure_valid(user)
        values = self.settings.catalog_pairs([(row.customer_name, row.customer_group) for row in request.rows])
        self.settings.ensure_catalog(values)
        self.repository.list_seeded()
        writes = rows_to_write(
            self.repository.list_all(),
            self.repository.list_deleted(),
            self.settings.customer_group_rules(values),
            lambda _row: True,
            self.access.deleted_by(user),
        )
        if writes:
            self.repository.save_many(writes)
        self.logger.info("Catalog saved: %s rows sent, %s rows written", len(values.pairs), len(writes))
        return SaveCatalogResponse(message="Đã lưu nhóm khách hàng.")
