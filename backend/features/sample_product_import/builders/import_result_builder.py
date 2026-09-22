"""ImportEvaluation -> preview / commit response DTOs."""

from backend.core.base import BaseBuilder
from backend.features.sample_product_import.dto.import_dto import (
    CommitImportResponse,
    ImportRowResultDTO,
    PreviewImportResponse,
)
from backend.features.sample_product_import.models.import_row import ImportAction, ImportEvaluation, RowEvaluation


class ImportRowResultBuilder(BaseBuilder[ImportRowResultDTO]):
    def __init__(self, evaluation: RowEvaluation) -> None:
        self.evaluation = evaluation

    def build(self) -> ImportRowResultDTO:
        row = self.evaluation.row
        return ImportRowResultDTO(
            row_number=row.row_number,
            code=row.code,
            name=row.name,
            unit=row.unit,
            quantity=float(row.quantity) if row.quantity is not None else None,
            unit_price=float(row.unit_price) if row.unit_price is not None else None,
            action=self.evaluation.action,
            errors=[f"{v.rule_code}: {v.message}" for v in self.evaluation.violations],
        )


class PreviewImportResponseBuilder(BaseBuilder[PreviewImportResponse]):
    def __init__(self, evaluation: ImportEvaluation) -> None:
        self.evaluation = evaluation

    def build(self) -> PreviewImportResponse:
        valid = len(self.evaluation.valid_rows)
        return PreviewImportResponse(
            rows=[ImportRowResultBuilder(r).build() for r in self.evaluation.rows],
            total_rows=len(self.evaluation.rows),
            valid_rows=valid,
            invalid_rows=len(self.evaluation.rows) - valid,
            create_count=self.evaluation.count(ImportAction.CREATE),
            update_count=self.evaluation.count(ImportAction.UPDATE),
        )


class CommitImportResponseBuilder(BaseBuilder[CommitImportResponse]):
    def __init__(self, evaluation: ImportEvaluation) -> None:
        self.evaluation = evaluation

    def build(self) -> CommitImportResponse:
        rejected = [r for r in self.evaluation.rows if not r.is_valid]
        return CommitImportResponse(
            created=self.evaluation.count(ImportAction.CREATE),
            updated=self.evaluation.count(ImportAction.UPDATE),
            rejected=len(rejected),
            rejected_rows=[ImportRowResultBuilder(r).build() for r in rejected],
        )
