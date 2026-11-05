"""UC-24: save the Fac 1 line table; Fac 1 data before 07/07/2026 uses it at once."""

from backend.core.base import BaseService
from backend.features.sewing_productivity.business.access_rules import AccessBusiness
from backend.features.sewing_productivity.business.record_sync import rows_to_write
from backend.features.sewing_productivity.business.settings_business import SettingsBusiness
from backend.features.sewing_productivity.dto.catalog_dto import SaveCatalogResponse, SaveLineMappingsRequest
from backend.features.sewing_productivity.repositories.settings_repositories import LineMappingRuleRepository


class SaveLineMappingsService(BaseService[SaveLineMappingsRequest, SaveCatalogResponse]):
    def __init__(self, repository: LineMappingRuleRepository | None = None) -> None:
        self.repository = repository or LineMappingRuleRepository()
        self.access = AccessBusiness()
        self.settings = SettingsBusiness()

    def execute(self, request: SaveLineMappingsRequest) -> SaveCatalogResponse:
        user = self.current_user
        self.access.ensure_valid(user)
        values = self.settings.catalog_pairs([(row.old_line, row.new_line) for row in request.rows], lines_only=True)
        self.settings.ensure_catalog(values)
        self.repository.list_seeded()
        writes = rows_to_write(
            self.repository.list_all(),
            self.repository.list_deleted(),
            self.settings.line_mapping_rules(values),
            lambda _row: True,
            self.access.deleted_by(user),
        )
        if writes:
            self.repository.save_many(writes)
        self.logger.info("Catalog saved: %s rows sent, %s rows written", len(values.pairs), len(writes))
        return SaveCatalogResponse(message="Đã lưu bảng số chuyền.")
