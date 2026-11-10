"""Đợt 2 (bổ sung 2026-11-10) tables xuan2894__yarn_costing__*: 4.22-4.28 (giá nguyên liệu, hàng sắp về, giá báo khách)."""

from backend.features.yarn_costing.models.material_price import (
    ArrivalImport,
    ArrivalLot,
    ArrivalMapping,
    MaterialPriceGroup,
    MonthInputs,
    MonthlyMaterialSetting,
    Quote,
    StockItemSetting,
    StockLine,
    StockMonth,
)
from backend.features.yarn_costing.repositories.exchange_rate_repository import ExchangeRateRepository
from backend.features.yarn_costing.repositories.yarn_sql_repository import YarnSqlRepository


class MaterialPriceGroupRepository(YarnSqlRepository[MaterialPriceGroup]):
    pass


class StockItemSettingRepository(YarnSqlRepository[StockItemSetting]):
    def by_code(self) -> dict[str, StockItemSetting]:
        return {s.accounting_code: s for s in self.list_all()}


class StockMonthRepository(YarnSqlRepository[StockMonth]):
    def current(self, period: str) -> StockMonth | None:
        """BR-87: the one month version in use for a period."""
        return next(iter(self.find_by(period=period)), None)

    def ordered(self) -> list[StockMonth]:
        return sorted(self.list_all(), key=lambda m: m.period, reverse=True)


class StockLineRepository(YarnSqlRepository[StockLine]):
    def for_month(self, month_id: str) -> list[StockLine]:
        return self.find_by(month_id=month_id)


class MonthlyMaterialSettingRepository(YarnSqlRepository[MonthlyMaterialSetting]):
    def for_period(self, period: str) -> MonthlyMaterialSetting | None:
        return next(iter(self.find_by(period=period)), None)


class ArrivalImportRepository(YarnSqlRepository[ArrivalImport]):
    pass


class ArrivalLotRepository(YarnSqlRepository[ArrivalLot]):
    pass


class ArrivalMappingRepository(YarnSqlRepository[ArrivalMapping]):
    def by_key(self) -> dict[tuple[str, str], ArrivalMapping]:
        return {(m.supplier_key, m.description_key): m for m in self.list_all()}


class QuoteRepository(YarnSqlRepository[Quote]):
    def all_numbers(self) -> list[str]:
        """BR-97: numbers already used, deleted ones included (never reused)."""
        return [q.quote_no for q in [*self.list_all(), *self.list_deleted()]]


def previous_period(period: str) -> str:
    year, month = (int(p) for p in period.split("-"))
    return f"{year - 1:04d}-12" if month == 1 else f"{year:04d}-{month - 1:02d}"


def load_month_inputs(period: str) -> MonthInputs:
    """BR-92 inputs of month M: stock file of M−1, settings, groups, lots, mappings, monthly settings, exchange rates."""
    stock_month = StockMonthRepository().current(previous_period(period))
    return MonthInputs(
        period=period,
        stock_month=stock_month,
        stock_lines=StockLineRepository().for_month(stock_month.id) if stock_month else [],
        settings=StockItemSettingRepository().by_code(),
        groups={g.id: g for g in MaterialPriceGroupRepository().list_all()},
        lots=ArrivalLotRepository().list_all(),
        mappings=ArrivalMappingRepository().by_key(),
        monthly=MonthlyMaterialSettingRepository().list_all(),
        rates=ExchangeRateRepository().list_all(),
    )
