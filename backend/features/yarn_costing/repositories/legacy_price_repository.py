"""Stored in data/yarn_costing/legacy_prices.json and import_batches.json."""

from backend.features.yarn_costing.models.legacy_price import ImportBatch, LegacyPrice
from backend.features.yarn_costing.repositories.compact_json_repository import CompactJsonRepository
from backend.features.yarn_costing.repositories.safe_json_repository import SafeJsonRepository


class LegacyPriceRepository(CompactJsonRepository[LegacyPrice]):
    storage_file = "legacy_prices.json"

    def for_import(self, import_id: str) -> list[LegacyPrice]:
        return self.find(lambda p: p.import_id == import_id)


class ImportBatchRepository(SafeJsonRepository[ImportBatch]):
    storage_file = "import_batches.json"

    def newest_first(self) -> list[ImportBatch]:
        return sorted(self.list_all(), key=lambda b: b.imported_at, reverse=True)
