"""Products -> list response DTO, Excel export file, Excel import template."""

from collections.abc import Sequence
from datetime import datetime

from backend.core.base import BaseBuilder, FileDownloadDTO, MimeType
from backend.features.sample_product_import.constants import IMPORT_COLUMNS
from backend.features.sample_product_import.dto.product_dto import ProductDTO, ProductListResponse, StockSummaryDTO
from backend.features.sample_product_import.models.product import Product, StockStatus
from backend.features.sample_product_import.models.stock_summary import StockSummary
from backend.shared.file_io import ExcelWriter

STATUS_LABELS = {StockStatus.OUT_OF_STOCK: "Hết hàng", StockStatus.LOW: "Sắp hết", StockStatus.IN_STOCK: "Còn hàng"}
ClassifiedProducts = Sequence[tuple[Product, StockStatus]]


class ProductListResponseBuilder(BaseBuilder[ProductListResponse]):
    def __init__(self, products: ClassifiedProducts, summary: StockSummary) -> None:
        self.products, self.summary = products, summary

    def build(self) -> ProductListResponse:
        items = [
            ProductDTO(
                code=p.code,
                name=p.name,
                unit=p.unit,
                quantity=p.quantity,
                unit_price=float(p.unit_price),
                total_value=float(p.total_value),
                stock_status=status,
                updated_at=p.updated_at,
            )
            for p, status in self.products
        ]
        summary = StockSummaryDTO(**{**self.summary.model_dump(), "total_value": float(self.summary.total_value)})
        return ProductListResponse(items=items, summary=summary)


class ProductExportFileBuilder(BaseBuilder[FileDownloadDTO]):
    def __init__(self, products: ClassifiedProducts) -> None:
        self.products = products

    def build(self) -> FileDownloadDTO:
        rows = [
            {
                "Mã SP": p.code,
                "Tên sản phẩm": p.name,
                "Đơn vị": p.unit,
                "Số lượng": p.quantity,
                "Đơn giá": float(p.unit_price),
                "Thành tiền": float(p.total_value),
                "Trạng thái": STATUS_LABELS[status],
            }
            for p, status in self.products
        ]
        filename = f"ton-kho-{datetime.now():%Y%m%d-%H%M}.xlsx"
        return FileDownloadDTO(
            filename=filename, content=ExcelWriter().write({"Tồn kho": rows}), mime_type=MimeType.XLSX
        )


class ImportTemplateFileBuilder(BaseBuilder[FileDownloadDTO]):
    SAMPLE_ROWS = (("SP-001", "Áo thun cotton", "cái", 120, 85000), ("SP-002", "Quần kaki", "cái", 8, 250000))

    def build(self) -> FileDownloadDTO:
        headers = [c.header for c in IMPORT_COLUMNS]
        rows = [dict(zip(headers, values, strict=True)) for values in self.SAMPLE_ROWS]
        content = ExcelWriter().write({"San pham": rows})
        return FileDownloadDTO(filename="mau-nhap-san-pham.xlsx", content=content, mime_type=MimeType.XLSX)
