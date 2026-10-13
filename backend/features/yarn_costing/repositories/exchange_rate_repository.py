"""Tables xuan2894__yarn_costing__exchange_rate (seed 25.000 from 2026-01-01) and xuan2894__yarn_costing__settings (trial factor 3)."""

from datetime import date

from backend.features.yarn_costing.constants import SEED_EXCHANGE_RATE, SEED_EXCHANGE_RATE_DATE, SEED_TRIAL_FACTOR
from backend.features.yarn_costing.models.exchange_rate import CostingSettings, ExchangeRate
from backend.features.yarn_costing.repositories.yarn_sql_repository import YarnSqlRepository


class ExchangeRateRepository(YarnSqlRepository[ExchangeRate]):
    legacy_file = "exchange_rates.json"

    def _seed(self) -> list[ExchangeRate]:
        return [
            ExchangeRate(
                effective_date=date.fromisoformat(SEED_EXCHANGE_RATE_DATE),
                rate=SEED_EXCHANGE_RATE,
                created_by="Khởi tạo",
            )
        ]

    def list_ordered(self) -> list[ExchangeRate]:
        return sorted(self.list_all(), key=lambda r: (r.effective_date, r.created_at), reverse=True)


class SettingsRepository(YarnSqlRepository[CostingSettings]):
    legacy_file = "settings.json"

    def get_settings(self) -> CostingSettings:
        items = self.list_all()
        if items:
            return items[0]
        settings = CostingSettings(trial_factor=SEED_TRIAL_FACTOR)
        self.add(settings)
        return settings
