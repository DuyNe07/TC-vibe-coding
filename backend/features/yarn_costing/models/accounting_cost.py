"""4.21 Tháng giá thành kế toán and 4.21.1 its lines (file Z, bổ sung 2026-11-10)."""

from decimal import Decimal
from typing import Any

from backend.core.base import BaseEntity, BaseValueObject
from backend.features.yarn_costing.models.enums import FactoryCode

ZERO = Decimal(0)


class AccountingCostMonth(BaseEntity):
    period: str  # yyyy-mm
    file_name: str = ""
    sheet_name: str = ""
    row_count: int = 0
    total_quantity: Decimal = ZERO
    imported_by: str = ""


class AccountingAmounts(BaseValueObject):
    """5 cost columns of file Z (đồng; may be negative)."""

    labor: Decimal = ZERO
    depreciation: Decimal = ZERO
    power: Decimal = ZERO
    materials: Decimal = ZERO
    overhead: Decimal = ZERO


class AccountingCostLine(BaseEntity):
    month_id: str
    period: str
    factory_code: FactoryCode
    accounting_code: str
    product_name: str = ""
    quantity: Decimal
    material_amount: Decimal = ZERO
    amounts: AccountingAmounts = AccountingAmounts()
    total_amount: Decimal = ZERO

    @property
    def unit_cost(self) -> Decimal:
        """Giá thành đơn vị (có nguyên liệu) = Cộng ÷ Số lượng."""
        return self.total_amount / self.quantity

    @property
    def conversion_unit_cost(self) -> Decimal:
        """BR-80: chi phí chế biến kế toán = (Cộng − VLC) ÷ Số lượng."""
        return (self.total_amount - self.material_amount) / self.quantity

    def unit(self, amount: Decimal) -> Decimal:
        return amount / self.quantity


class ZSheet(BaseValueObject):
    """One month sheet of file Z as read (5.9): period '' = month unreadable; rows = (excel row, cells by field)."""

    sheet: str
    period: str
    rows: list[tuple[int, dict[str, Any]]] = []
    problem: str = ""
