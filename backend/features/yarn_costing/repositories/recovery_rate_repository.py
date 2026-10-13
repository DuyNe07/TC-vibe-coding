"""Table xuan2894__yarn_costing__recovery_rate. Seeds S4 1.5% / 1% / 2.5% and S1 2% / 1% / 1%."""

from backend.features.yarn_costing.constants import SEED_RECOVERY
from backend.features.yarn_costing.models.enums import FactoryCode, RecoveryType
from backend.features.yarn_costing.models.recovery_rate import RecoveryRate
from backend.features.yarn_costing.repositories.yarn_sql_repository import YarnSqlRepository


class RecoveryRateRepository(YarnSqlRepository[RecoveryRate]):
    legacy_file = "recovery_rates.json"

    def _seed(self) -> list[RecoveryRate]:
        return [
            RecoveryRate(factory_code=FactoryCode(f), recovery_type=RecoveryType(kind), rate=rate)
            for f, rates in SEED_RECOVERY.items()
            for kind, rate in rates.items()
        ]

    def for_factory(self, factory_code: str) -> list[RecoveryRate]:
        order = list(RecoveryType)
        return sorted(
            self.find(lambda r: r.factory_code.value == factory_code), key=lambda r: order.index(r.recovery_type)
        )
