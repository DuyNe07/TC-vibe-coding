"""Stored in data/yarn_costing/packaging_types.json."""

from backend.features.yarn_costing.models.packaging_type import PackagingType
from backend.features.yarn_costing.repositories.safe_json_repository import SafeJsonRepository


class PackagingTypeRepository(SafeJsonRepository[PackagingType]):
    storage_file = "packaging_types.json"

    def for_factory(self, factory_code: str) -> list[PackagingType]:
        return sorted(self.find(lambda p: p.factory_code.value == factory_code), key=lambda p: p.code)
