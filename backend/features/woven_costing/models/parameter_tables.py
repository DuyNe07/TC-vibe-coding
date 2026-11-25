"""4.6.1 quantity discount table and 4.6.2 % B/C table of a parameter set (added 2026-11-25)."""

from decimal import Decimal
from typing import Final

from pydantic import Field

from backend.core.base import BaseValueObject
from backend.features.woven_costing.models.enums import (
    BC_FALLBACK,
    DiscountCondition,
    DiscountDepartment,
    QuantityUnit,
    SaleForm,
)

D = Decimal

# 4.6.1: unit of the quantity and allowed conditions of each department
DEPARTMENT_UNITS: Final = {
    DiscountDepartment.WEAVING: QuantityUnit.GREIGE_M,
    DiscountDepartment.HCM: QuantityUnit.FINISHED_KG,
    DiscountDepartment.TCDN: QuantityUnit.FINISHED_M,
}
DEPARTMENT_CONDITIONS: Final = {
    DiscountDepartment.WEAVING: (DiscountCondition.MASS, DiscountCondition.TRIAL),
    DiscountDepartment.HCM: (DiscountCondition.MASS, DiscountCondition.TRIAL),
    DiscountDepartment.TCDN: (DiscountCondition.MASS, DiscountCondition.DYEING, DiscountCondition.PARTIAL),
}
DEPARTMENT_APPLIES_TO: Final = {
    DiscountDepartment.WEAVING: "Mắc Hồ, Mắc phân băng, Cone, Dệt, Kiểm",
    DiscountDepartment.HCM: "Hóa chất thuốc nhuộm và Tiền lương",
    DiscountDepartment.TCDN: "Mọi dòng nhuộm",
}


ALL_QUANTITIES = "mọi sản lượng"


def quantity_text(value: Decimal) -> str:
    """7500 -> "7.500"; decimals kept with a comma."""
    if value == value.to_integral_value():
        return f"{value:,.0f}".replace(",", ".")
    return f"{value:,.2f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def range_text(row: "DiscountRow") -> str:
    """ "5.000 ≤ SL < 10.000", "SL ≥ 100.000", "SL < 5.000" or "mọi sản lượng"."""
    low = "≤" if row.from_inclusive else "<"
    high = "≤" if row.to_inclusive else "<"
    if row.from_qty is not None and row.to_qty is not None:
        return f"{quantity_text(row.from_qty)} {low} SL {high} {quantity_text(row.to_qty)}"
    if row.from_qty is not None:
        return f"SL {'≥' if row.from_inclusive else '>'} {quantity_text(row.from_qty)}"
    if row.to_qty is not None:
        return f"SL {high} {quantity_text(row.to_qty)}"
    return ALL_QUANTITIES


def _row_reason(row: "DiscountRow") -> str:
    """Reason shown next to the applied factor, e.g. "Đại trà 5.000 ≤ SL < 10.000 m mộc"."""
    bounds = range_text(row)
    if bounds == ALL_QUANTITIES:
        text = f"{row.condition.value}, {bounds}"
    else:
        text = f"{row.condition.value} {bounds} {row.unit.value}"
    return f"{text} (chia đều giữa mốc)" if row.interpolate else text


class DiscountRow(BaseValueObject):
    """4.6.1 one row: factor for a quantity range of one department + condition (empty bound = no limit)."""

    department: DiscountDepartment
    condition: DiscountCondition
    from_qty: Decimal | None = None
    from_inclusive: bool = True
    to_qty: Decimal | None = None
    to_inclusive: bool = False
    factor: Decimal
    interpolate: bool = False  # only sets stored before 2026-11-25 (Excel formula of BR-23)

    @property
    def unit(self) -> QuantityUnit:
        return DEPARTMENT_UNITS[self.department]

    @property
    def reason(self) -> str:
        """e.g. "Đại trà 5.000 ≤ SL < 10.000 m mộc" (shown next to the applied factor)."""
        return _row_reason(self)

    def contains(self, quantity: Decimal) -> bool:
        """from / to checked with >= or > / <= or < (from_inclusive / to_inclusive)."""
        low, high = self.from_qty, self.to_qty
        below = low is not None and (quantity < low or (quantity == low and not self.from_inclusive))
        above = high is not None and (quantity > high or (quantity == high and not self.to_inclusive))
        return not below and not above


class BcRow(BaseValueObject):
    """4.6.2 one row: % B/C mộc and % B/C thành phẩm of one sale form."""

    sale_form: SaleForm
    greige_bc_rate: Decimal
    finished_bc_rate: Decimal


class DiscountPick(BaseValueObject):
    """4.6.1 factor chosen for one costsheet with the row's reason; ``found`` False = no row matched (factor 1)."""

    factor: Decimal
    reason: str = ""
    found: bool = True
    applies: bool = True


class OpRateRow(BaseValueObject):
    """4.24 (2026-11-25): "Op. Rate to costing" of one TCDN stage (dyeing job orders only, BR-93)."""

    stage: str
    rate: Decimal


# 4.24 initial values (file "Forrmat NGC Nhuộm TCDN.xlsm", sheet Operation Rate)
INITIAL_OP_RATES: Final = (
    ("In Truyền Nhiệt", "0.3"), ("Santa", "0.4"), ("Bonding", "0.3"), ("Raising", "0.3"), ("Brush", "0.3"),
    ("Buffing", "0.3"), ("Shearing", "0.3"), ("Coating", "0.6"), ("Cire", "0.7"), ("Heavy Cire", "0.7"),
    ("Kiểm Trung Gian", "1"), ("Peach", "0.3"),
)  # fmt: skip


def initial_op_rates() -> list[OpRateRow]:
    return [OpRateRow(stage=s, rate=Decimal(r)) for s, r in INITIAL_OP_RATES]


class ParameterTables(BaseValueObject):
    discount_rows: list[DiscountRow] = Field(default_factory=list)
    bc_rows: list[BcRow] = Field(default_factory=list)
    # 4.24 (2026-11-25): sets stored before read the initial values
    op_rates: list[OpRateRow] = Field(default_factory=initial_op_rates)


def complete_bc_rows(rows: list[BcRow]) -> list[BcRow]:
    """4.6.2 (2026-11-25): a set saved before the job sale forms existed reads the Gia công dệt row as the Mộc row and
    the Gia công nhuộm row as the Vải Nhuộm row (stored data unchanged)."""
    forms = {r.sale_form for r in rows}
    extra = [
        BcRow(sale_form=job, greige_bc_rate=source.greige_bc_rate, finished_bc_rate=source.finished_bc_rate)
        for job, base in BC_FALLBACK.items()
        if job not in forms
        for source in [next((r for r in rows if r.sale_form == base), None)]
        if source is not None
    ]
    return [*rows, *extra]


def _row(
    department: DiscountDepartment,
    condition: DiscountCondition,
    factor: str | Decimal,
    from_qty: int | Decimal | None = None,
    to_qty: int | Decimal | None = None,
    *,
    from_inclusive: bool = True,
    to_inclusive: bool = False,
    interpolate: bool = False,
) -> DiscountRow:
    return DiscountRow(
        department=department,
        condition=condition,
        from_qty=None if from_qty is None else D(from_qty),
        from_inclusive=from_inclusive,
        to_qty=None if to_qty is None else D(to_qty),
        to_inclusive=to_inclusive,
        factor=D(factor),
        interpolate=interpolate,
    )


def company_weaving_rows(trial_factor: Decimal) -> list[DiscountRow]:
    """4.6.1 Dệt rows of the company rule "Thống nhất giảm giá / phụ phí theo sản lượng đơn hàng" (steps, no
    interpolation), used from the parameter set effective 2026-11-25."""
    w, mass = DiscountDepartment.WEAVING, DiscountCondition.MASS
    return [
        _row(w, mass, "1.1", 1, 5000, from_inclusive=False),
        _row(w, mass, "1.05", 5000, 10000),
        _row(w, mass, "1", 10000, 20000, to_inclusive=True),
        _row(w, mass, "0.95", 20000, 50000, from_inclusive=False),
        _row(w, mass, "0.92", 50000, 100000),
        _row(w, mass, "0.9", 100000),
        _row(w, DiscountCondition.TRIAL, trial_factor),
    ]
