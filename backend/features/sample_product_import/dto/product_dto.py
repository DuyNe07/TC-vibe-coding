"""Contracts of UC-04 (list_products) and UC-05 (export_products)."""

from datetime import datetime

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.sample_product_import.models.product import StockStatus

__all__ = [
    "ExportProductsRequest",
    "ListProductsRequest",
    "ProductDTO",
    "ProductListResponse",
    "StockStatus",
    "StockSummaryDTO",
]


class ListProductsRequest(BaseRequestDTO):
    keyword: str = ""
    stock_status: StockStatus | None = None


class ExportProductsRequest(ListProductsRequest):
    pass


class ProductDTO(BaseDTO):
    code: str
    name: str
    unit: str
    quantity: int
    unit_price: float
    total_value: float
    stock_status: StockStatus
    updated_at: datetime


class StockSummaryDTO(BaseDTO):
    product_count: int
    total_quantity: int
    total_value: float
    out_of_stock: int
    low_stock: int
    in_stock: int


class ProductListResponse(BaseResponseDTO):
    items: list[ProductDTO]
    summary: StockSummaryDTO
