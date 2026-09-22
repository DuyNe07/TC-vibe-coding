"""Stock classification (BR-08) and totals (BR-09)."""

from collections.abc import Sequence
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.sample_product_import.models.product import Product, StockStatus
from backend.features.sample_product_import.models.stock_summary import StockSummary


class ProductStockBusiness(BaseBusiness[Product]):
    LOW_STOCK_THRESHOLD = 10

    def classify(self, product: Product) -> StockStatus:
        if product.quantity == 0:
            return StockStatus.OUT_OF_STOCK
        if product.quantity < self.LOW_STOCK_THRESHOLD:
            return StockStatus.LOW
        return StockStatus.IN_STOCK

    def filter_by_status(self, products: Sequence[Product], status: StockStatus | None) -> list[Product]:
        return [p for p in products if status is None or self.classify(p) == status]

    def summarize(self, products: Sequence[Product]) -> StockSummary:
        statuses = [self.classify(p) for p in products]
        return StockSummary(
            product_count=len(products),
            total_quantity=sum(p.quantity for p in products),
            total_value=sum((p.total_value for p in products), Decimal(0)),
            out_of_stock=statuses.count(StockStatus.OUT_OF_STOCK),
            low_stock=statuses.count(StockStatus.LOW),
            in_stock=statuses.count(StockStatus.IN_STOCK),
        )
