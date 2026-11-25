"""The 7 cost items (khoản mục) used by every norm table and every cost breakdown."""

from decimal import Decimal

from backend.core.base import BaseValueObject

ZERO = Decimal(0)


class CostItems(BaseValueObject):
    """Nhân công (labor), Khấu hao, Điện, Vật tư, Nhiên liệu, Hóa chất (HCTN for HCM), CPQL / Quản lý (overhead)."""

    labor: Decimal = ZERO
    depreciation: Decimal = ZERO
    power: Decimal = ZERO
    material: Decimal = ZERO
    fuel: Decimal = ZERO
    chemical: Decimal = ZERO
    overhead: Decimal = ZERO

    @property
    def total(self) -> Decimal:
        return self.labor + self.depreciation + self.power + self.material + self.fuel + self.chemical + self.overhead

    @property
    def total_without_chemical(self) -> Decimal:
        return self.total - self.chemical

    def scaled(self, factor: Decimal) -> "CostItems":
        return CostItems(**{name: value * factor for name, value in self.as_dict().items()})

    def plus(self, other: "CostItems") -> "CostItems":
        mine, theirs = self.as_dict(), other.as_dict()
        return CostItems(**{name: mine[name] + theirs[name] for name in mine})

    def as_dict(self) -> dict[str, Decimal]:
        return {name: getattr(self, name) for name in type(self).model_fields}
