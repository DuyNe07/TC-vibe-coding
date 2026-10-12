"""Stored in data/yarn_costing/price_history.json (only changed lines are recorded)."""

from backend.features.yarn_costing.models.price_history import PriceHistory
from backend.features.yarn_costing.repositories.compact_json_repository import CompactJsonRepository


class PriceHistoryRepository(CompactJsonRepository[PriceHistory]):
    storage_file = "price_history.json"

    def add_many(self, entries: list[PriceHistory]) -> None:
        if entries:
            self.save_many(entries)
