"""Persistence of 4.4 exchange rates, 4.7 fabric factors, 4.8 holidays, 4.9 customers."""

from backend.core.base import SqlRepository
from backend.features.woven_costing.models.master import (
    Customer,
    ExchangeRate,
    FabricFactor,
    Holiday,
    initial_fabric_factors,
)


class ExchangeRateRepository(SqlRepository[ExchangeRate]):
    def for_month(self, month: int, year: int) -> ExchangeRate | None:
        found = self.find_by(month=month, year=year)
        return found[0] if found else None

    def newest_first(self) -> list[ExchangeRate]:
        return sorted(self.list_all(), key=lambda r: (r.year, r.month), reverse=True)


class FabricFactorRepository(SqlRepository[FabricFactor]):
    def list_with_seed(self) -> list[FabricFactor]:
        """4.7: the table starts with the initial data of the Excel files (ES17020213, ES17020413)."""
        rows = self.list_all()
        if not rows and not self.list_deleted():
            rows = self.save_many(initial_fabric_factors())
        return sorted(rows, key=lambda f: (f.tcfno, f.stage.value, f.cost_item.value, f.effective_from))


class HolidayRepository(SqlRepository[Holiday]):
    def by_date(self, day: object) -> Holiday | None:
        found = self.find_by(date=day)
        return found[0] if found else None


class CustomerRepository(SqlRepository[Customer]):
    def by_code(self, code: str) -> Customer | None:
        found = self.find_by(customer_code=code)
        return found[0] if found else None

    def sorted_by_name(self) -> list[Customer]:
        return sorted(self.list_all(), key=lambda c: c.name.casefold())
