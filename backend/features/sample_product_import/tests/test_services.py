from io import BytesIO

import pytest
from openpyxl import Workbook

from backend.core.base import EmptyRequest, UploadedFileDTO
from backend.features.sample_product_import.controllers.sample_product_import_controller import (
    SampleProductImportController,
)
from backend.features.sample_product_import.dto.import_dto import CommitImportRequest, PreviewImportRequest
from backend.features.sample_product_import.dto.product_dto import ListProductsRequest, StockStatus
from backend.features.sample_product_import.exceptions import ImportFileError
from backend.features.sample_product_import.repositories.product_repository import ProductRepository
from backend.features.sample_product_import.services.commit_import_service import CommitImportService
from backend.features.sample_product_import.services.download_template_service import DownloadTemplateService
from backend.features.sample_product_import.services.list_products_service import ListProductsService
from backend.features.sample_product_import.services.preview_import_service import PreviewImportService


def excel(rows: list[list]) -> UploadedFileDTO:
    workbook = Workbook()
    for values in rows:
        workbook.active.append(values)
    buffer = BytesIO()
    workbook.save(buffer)
    return UploadedFileDTO(filename="products.xlsx", content=buffer.getvalue())


@pytest.fixture
def repository(tmp_path) -> ProductRepository:
    return ProductRepository(file_path=tmp_path / "products.json")


def test_template_is_a_valid_import_file(repository) -> None:
    template = DownloadTemplateService().handle(EmptyRequest())
    file = UploadedFileDTO(filename=template.filename, content=template.content)
    preview = PreviewImportService(repository).handle(PreviewImportRequest(file=file))
    assert preview.valid_rows == 2 and preview.invalid_rows == 0


def test_commit_then_list(repository) -> None:
    file = excel([["Mã SP", "Tên sản phẩm", "Số lượng", "Đơn giá"], ["a-1", "Áo", 3, 100], ["B-2", "", 5, 10]])
    result = CommitImportService(repository).handle(CommitImportRequest(file=file))
    assert (result.created, result.rejected) == (1, 1)

    listed = ListProductsService(repository).handle(ListProductsRequest(stock_status=StockStatus.LOW))
    assert [p.code for p in listed.items] == ["A-1"]
    assert listed.summary.total_value == 300


def test_missing_column_raises_friendly_error() -> None:
    file = excel([["Mã SP", "Tên sản phẩm"], ["A", "B"]])
    with pytest.raises(ImportFileError, match="thiếu cột"):
        SampleProductImportController().preview_import(PreviewImportRequest(file=file))
