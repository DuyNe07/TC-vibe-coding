from decimal import Decimal
from enum import StrEnum

from backend.core.base import BaseValueObject, RuleViolation


class ImportAction(StrEnum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    REJECT = "REJECT"


class ImportRow(BaseValueObject):
    """One data row of the uploaded Excel file, normalized but NOT yet validated."""

    row_number: int
    code: str = ""
    name: str = ""
    unit: str = ""
    quantity: Decimal | None = None
    unit_price: Decimal | None = None


class RowEvaluation(BaseValueObject):
    row: ImportRow
    action: ImportAction
    violations: tuple[RuleViolation, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.violations


class ImportEvaluation(BaseValueObject):
    rows: tuple[RowEvaluation, ...]

    @property
    def valid_rows(self) -> list[RowEvaluation]:
        return [r for r in self.rows if r.is_valid]

    def count(self, action: ImportAction) -> int:
        return sum(1 for r in self.rows if r.action == action)
