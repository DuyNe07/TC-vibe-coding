"""Table yarn_costing__price_history (only changed lines are recorded)."""

from backend.features.yarn_costing.models.price_history import PriceHistory
from backend.features.yarn_costing.repositories.yarn_sql_repository import YarnSqlRepository


class PriceHistoryRepository(YarnSqlRepository[PriceHistory]):
    legacy_file = "price_history.json"

    def add_many(self, entries: list[PriceHistory]) -> None:
        if entries:
            self.save_many(entries)
