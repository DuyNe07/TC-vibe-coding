"""UC-03: save the valid rows of an uploaded file (create or update by product code)."""

from backend.core.base import BaseService
from backend.features.sample_product_import.builders.import_result_builder import CommitImportResponseBuilder
from backend.features.sample_product_import.builders.import_rows_builder import ImportRowsBuilder
from backend.features.sample_product_import.business.import_business import ProductImportBusiness
from backend.features.sample_product_import.dto.import_dto import CommitImportRequest, CommitImportResponse
from backend.features.sample_product_import.repositories.product_repository import ProductRepository


class CommitImportService(BaseService[CommitImportRequest, CommitImportResponse]):
    def __init__(self, repository: ProductRepository | None = None) -> None:
        self.repository = repository or ProductRepository()
        self.business = ProductImportBusiness()

    def execute(self, request: CommitImportRequest) -> CommitImportResponse:
        rows = ImportRowsBuilder(request.file).build()
        self.business.ensure_row_limit(rows)
        existing = self.repository.index_by_code()
        evaluation = self.business.evaluate(rows, existing_codes=set(existing))
        products = [self.business.to_product(e.row, existing.get(e.row.code)) for e in evaluation.valid_rows]
        self.repository.save_many(products)
        self.logger.info("Saved %s valid rows of %s from %s", len(products), len(rows), request.file.filename)
        return CommitImportResponseBuilder(evaluation).build()
