from decimal import Decimal
from enum import StrEnum

from pydantic import Field

from backend.core.base import BaseEntity


class StockStatus(StrEnum):
    """BR-08."""

    OUT_OF_STOCK = "OUT_OF_STOCK"
    LOW = "LOW"
    IN_STOCK = "IN_STOCK"


class Product(BaseEntity):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=200)
    unit: str = Field(default="cái", max_length=30)
    quantity: int = Field(ge=0)
    unit_price: Decimal = Field(gt=0)

    @property
    def total_value(self) -> Decimal:
        """BR-09: Thành tiền = Số lượng × Đơn giá."""
        return self.unit_price * self.quantity
