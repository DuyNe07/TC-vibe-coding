"""UC-41 Xem danh sách lần nhập file."""

from backend.core.base import BaseService
from backend.features.yarn_costing.dto.import_dto import (
    ImportBatchDTO,
    ImportBatchListResponse,
    ListImportBatchesRequest,
    SheetResultDTO,
)
from backend.features.yarn_costing.repositories.legacy_price_repository import ImportBatchRepository


class ListImportBatchesService(BaseService[ListImportBatchesRequest, ImportBatchListResponse]):
    def __init__(self, repository: ImportBatchRepository | None = None) -> None:
        self.repository = repository or ImportBatchRepository()

    def execute(self, request: ListImportBatchesRequest) -> ImportBatchListResponse:
        items = []
        for b in self.repository.newest_first():
            if request.factory_code is not None and b.factory_code != request.factory_code:
                continue
            items.append(
                ImportBatchDTO(
                    import_id=b.batch_code,
                    factory_code=b.factory_code,
                    mode=b.mode,
                    cutoff_date=b.cutoff_date,
                    file_name=b.file_name,
                    imported_by=b.imported_by,
                    imported_at=b.imported_at,
                    created_count=sum(s.created for s in b.sheets),
                    updated_count=sum(s.updated for s in b.sheets),
                    rejected_count=sum(s.rejected for s in b.sheets),
                    sheets=[SheetResultDTO(**s.model_dump()) for s in b.sheets],
                )
            )
        self.logger.info("Import batches: %s", len(items))
        return ImportBatchListResponse(items=items)
