from decimal import Decimal

from backend.core.base import BaseValueObject


class StockSummary(BaseValueObject):
    product_count: int = 0
    total_quantity: int = 0
    total_value: Decimal = Decimal(0)
    out_of_stock: int = 0
    low_stock: int = 0
    in_stock: int = 0
