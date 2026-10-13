"""Table xuan2894__yarn_costing__packaging_type."""

from backend.features.yarn_costing.models.packaging_type import PackagingType
from backend.features.yarn_costing.repositories.yarn_sql_repository import YarnSqlRepository


class PackagingTypeRepository(YarnSqlRepository[PackagingType]):
    legacy_file = "packaging_types.json"

    def for_factory(self, factory_code: str) -> list[PackagingType]:
        return sorted(self.find(lambda p: p.factory_code.value == factory_code), key=lambda p: p.code)
