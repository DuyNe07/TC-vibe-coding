"""Validation rules of the data file: BR-01 to BR-06 and BR-16."""

import re

from backend.core.base import BaseBusinessRule
from backend.features.sewing_productivity.constants import (
    ALLOWED_EXTENSION,
    FACTORY_BY_SOURCE_NAME,
    MAX_FILE_MB,
    MESSAGE_BR01,
    MESSAGE_BR04,
    PRODUCTION_REQUIRED_COLUMNS,
    SHEET_TARGET,
    TARGET_REQUIRED_COLUMNS,
)
from backend.features.sewing_productivity.models.upload_values import (
    ProductionResultFacts,
    RawProductionRow,
    RawTargetRow,
    SheetColumns,
    SheetNames,
    UploadFileFacts,
)
from backend.shared.utils import normalize_key

TARGET_LINE_PATTERN = re.compile(r"^\s*(SFVL|SF2|SF3|SF5)\s*-\s*Sewing\s+Line\s+0*(\d+)\s*$", re.IGNORECASE)


def _label(columns: dict[str, tuple[str, ...]], field: str) -> str:
    return columns[field][0]


class UploadFileRule(BaseBusinessRule[UploadFileFacts]):
    code = "BR-01"
    message = MESSAGE_BR01

    def is_satisfied_by(self, target: UploadFileFacts) -> bool:
        return target.extension == ALLOWED_EXTENSION and target.size_mb <= MAX_FILE_MB


class RequiredSheetsRule(BaseBusinessRule[SheetNames]):
    code = "BR-02"
    message = "File thiếu sheet. Hãy dùng đúng file Data sewing."

    def is_satisfied_by(self, target: SheetNames) -> bool:
        return not target.missing

    def describe_violation(self, target: SheetNames) -> str:
        return f"File thiếu sheet: {', '.join(target.missing)}. Hãy dùng đúng file Data sewing."


class RequiredColumnsRule(BaseBusinessRule[SheetColumns]):
    code = "BR-03"
    message = "Sheet thiếu cột. Hãy kiểm tra dòng tiêu đề của sheet."

    def is_satisfied_by(self, target: SheetColumns) -> bool:
        return not target.missing

    def describe_violation(self, target: SheetColumns) -> str:
        return f"Sheet {target.sheet} thiếu cột: {', '.join(target.missing)}. Hãy kiểm tra dòng tiêu đề của sheet."


class FormulaResultsRule(BaseBusinessRule[ProductionResultFacts]):
    code = "BR-04"
    message = MESSAGE_BR04

    def is_satisfied_by(self, target: ProductionResultFacts) -> bool:
        return target.valid_rows > 0 and target.standard_output_cells > 0


class ProductionRowRule(BaseBusinessRule[RawProductionRow]):
    code = "BR-05"
    message = "Dòng thiếu hoặc sai dữ liệu."

    def wrong_columns(self, row: RawProductionRow) -> list[str]:
        checks = {
            "production_date": row.production_date is not None,
            "factory_text": bool(row.factory_text),
            "customer_name": bool(row.customer_name),
            "style": bool(row.style),
            "po_number": bool(row.po_number),
            "source_line": bool(row.source_line),
            "quantity": row.quantity is not None and row.quantity >= 0,
            "cm_price": row.cm_price is not None and row.cm_price > 0,
            "sewers": row.sewers is not None and row.sewers > 0,
            "working_hours": row.working_hours is not None and row.working_hours > 0,
        }
        return [_label(PRODUCTION_REQUIRED_COLUMNS, field) for field, passed in checks.items() if not passed]

    def is_satisfied_by(self, target: RawProductionRow) -> bool:
        return not self.wrong_columns(target)

    def describe_violation(self, target: RawProductionRow) -> str:
        return f"Dòng {target.row_number}: thiếu hoặc sai {', '.join(self.wrong_columns(target))}."


class KnownFactoryRule(BaseBusinessRule[RawProductionRow]):
    code = "BR-06"
    message = "Dòng có xưởng chưa nhận diện được."

    def is_satisfied_by(self, target: RawProductionRow) -> bool:
        return not target.factory_text or normalize_key(target.factory_text) in FACTORY_BY_SOURCE_NAME

    def describe_violation(self, target: RawProductionRow) -> str:
        return f'Dòng {target.row_number}: chưa nhận diện được xưởng "{target.factory_text}".'


class TargetRowRule(BaseBusinessRule[RawTargetRow]):
    code = "BR-16"
    message = "Sheet Target system có dòng sai dữ liệu."

    def wrong_columns(self, row: RawTargetRow) -> list[str]:
        checks = {
            "line_text": bool(TARGET_LINE_PATTERN.match(row.line_text)),
            "target_date": row.target_date is not None,
            "daily_target_qty": row.daily_target_qty is not None and row.daily_target_qty >= 0,
        }
        return [_label(TARGET_REQUIRED_COLUMNS, field) for field, passed in checks.items() if not passed]

    def is_satisfied_by(self, target: RawTargetRow) -> bool:
        return not self.wrong_columns(target)

    def describe_violation(self, target: RawTargetRow) -> str:
        return f"Sheet {SHEET_TARGET}, dòng {target.row_number}: sai {', '.join(self.wrong_columns(target))}."
