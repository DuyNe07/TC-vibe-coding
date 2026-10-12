"""Stored in data/yarn_costing/exchange_rates.json (seed 25.000 from 2026-01-01) and settings.json (trial factor 3)."""

from datetime import date

from backend.features.yarn_costing.constants import SEED_EXCHANGE_RATE, SEED_EXCHANGE_RATE_DATE, SEED_TRIAL_FACTOR
from backend.features.yarn_costing.models.exchange_rate import CostingSettings, ExchangeRate
from backend.features.yarn_costing.repositories.safe_json_repository import SafeJsonRepository


class ExchangeRateRepository(SafeJsonRepository[ExchangeRate]):
    storage_file = "exchange_rates.json"

    def _read(self) -> dict[str, ExchangeRate]:
        if not self.file_path.exists():
            with self._lock:
                if not self.file_path.exists():
                    seed = ExchangeRate(
                        effective_date=date.fromisoformat(SEED_EXCHANGE_RATE_DATE),
                        rate=SEED_EXCHANGE_RATE,
                        created_by="Khởi tạo",
                    )
                    self._save({seed.id: seed})
        return super()._read()

    def list_ordered(self) -> list[ExchangeRate]:
        return sorted(self.list_all(), key=lambda r: (r.effective_date, r.created_at), reverse=True)


class SettingsRepository(SafeJsonRepository[CostingSettings]):
    storage_file = "settings.json"

    def get_settings(self) -> CostingSettings:
        items = self.list_all()
        if items:
            return items[0]
        settings = CostingSettings(trial_factor=SEED_TRIAL_FACTOR)
        self.add(settings)
        return settings
