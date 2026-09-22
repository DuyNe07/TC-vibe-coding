"""UC-02: check an uploaded file without saving anything."""

from backend.core.base import BaseService
from backend.features.sample_product_import.builders.import_result_builder import PreviewImportResponseBuilder
from backend.features.sample_product_import.builders.import_rows_builder import ImportRowsBuilder
from backend.features.sample_product_import.business.import_business import ProductImportBusiness
from backend.features.sample_product_import.dto.import_dto import PreviewImportRequest, PreviewImportResponse
from backend.features.sample_product_import.repositories.product_repository import ProductRepository


class PreviewImportService(BaseService[PreviewImportRequest, PreviewImportResponse]):
    def __init__(self, repository: ProductRepository | None = None) -> None:
        self.repository = repository or ProductRepository()
        self.business = ProductImportBusiness()

    def execute(self, request: PreviewImportRequest) -> PreviewImportResponse:
        rows = ImportRowsBuilder(request.file).build()
        self.business.ensure_row_limit(rows)
        self.logger.info("Read %s rows from %s", len(rows), request.file.filename)
        evaluation = self.business.evaluate(rows, existing_codes=set(self.repository.index_by_code()))
        self.logger.info(
            "Validation: %s valid, %s invalid", len(evaluation.valid_rows), len(rows) - len(evaluation.valid_rows)
        )
        return PreviewImportResponseBuilder(evaluation).build()
