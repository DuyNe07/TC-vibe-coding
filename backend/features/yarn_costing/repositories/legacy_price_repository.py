"""Tables yarn_costing__legacy_price and yarn_costing__import_batch."""

from backend.features.yarn_costing.models.legacy_price import ImportBatch, LegacyPrice
from backend.features.yarn_costing.repositories.yarn_sql_repository import YarnSqlRepository


class LegacyPriceRepository(YarnSqlRepository[LegacyPrice]):
    legacy_file = "legacy_prices.json"

    def for_import(self, import_id: str) -> list[LegacyPrice]:
        return self.find(lambda p: p.import_id == import_id)


class ImportBatchRepository(YarnSqlRepository[ImportBatch]):
    legacy_file = "import_batches.json"

    def newest_first(self) -> list[ImportBatch]:
        return sorted(self.list_all(), key=lambda b: b.imported_at, reverse=True)
