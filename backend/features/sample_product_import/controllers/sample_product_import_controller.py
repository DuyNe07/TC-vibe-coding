"""Top layer of feature "Nhập sản phẩm từ Excel (mẫu)". Pages call it through gateway.open(...).

One method = one use case = one service.
"""

from backend.core.base import BaseController, EmptyRequest, FileDownloadDTO
from backend.features.sample_product_import.dto.import_dto import (
    CommitImportRequest,
    CommitImportResponse,
    PreviewImportRequest,
    PreviewImportResponse,
)
from backend.features.sample_product_import.dto.product_dto import (
    ExportProductsRequest,
    ListProductsRequest,
    ProductListResponse,
)
from backend.features.sample_product_import.services.commit_import_service import CommitImportService
from backend.features.sample_product_import.services.download_template_service import DownloadTemplateService
from backend.features.sample_product_import.services.export_products_service import ExportProductsService
from backend.features.sample_product_import.services.list_products_service import ListProductsService
from backend.features.sample_product_import.services.preview_import_service import PreviewImportService


class SampleProductImportController(BaseController):
    def download_template(self, request: EmptyRequest) -> FileDownloadDTO:
        """UC-01 Tải file Excel mẫu."""
        return DownloadTemplateService().handle(request)

    def preview_import(self, request: PreviewImportRequest) -> PreviewImportResponse:
        """UC-02 Kiểm tra file trước khi lưu."""
        return PreviewImportService().handle(request)

    def commit_import(self, request: CommitImportRequest) -> CommitImportResponse:
        """UC-03 Lưu các dòng hợp lệ."""
        return CommitImportService().handle(request)

    def list_products(self, request: ListProductsRequest) -> ProductListResponse:
        """UC-04 Tra cứu sản phẩm + tồn kho."""
        return ListProductsService().handle(request)

    def export_products(self, request: ExportProductsRequest) -> FileDownloadDTO:
        """UC-05 Xuất Excel tồn kho."""
        return ExportProductsService().handle(request)
