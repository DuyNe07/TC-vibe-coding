"""Import decisions: validation (BR-01..05), create/update (BR-06), only valid rows (BR-07), row limit (BR-10)."""

from collections import Counter
from collections.abc import Sequence

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.core.exceptions import BusinessRuleViolation
from backend.features.sample_product_import.business.import_rules import (
    ProductCodeRule,
    ProductNameRule,
    QuantityRule,
    UniqueCodeInFileRule,
    UnitPriceRule,
)
from backend.features.sample_product_import.constants import DEFAULT_UNIT, MAX_IMPORT_ROWS
from backend.features.sample_product_import.models.import_row import (
    ImportAction,
    ImportEvaluation,
    ImportRow,
    RowEvaluation,
)
from backend.features.sample_product_import.models.product import Product


class ProductImportBusiness(BaseBusiness[ImportRow]):
    def rules(self) -> Sequence[BaseBusinessRule[ImportRow]]:
        return (ProductCodeRule(), ProductNameRule(), QuantityRule(), UnitPriceRule())

    def ensure_row_limit(self, rows: Sequence[ImportRow]) -> None:
        """BR-10."""
        if not rows:
            raise BusinessRuleViolation(message="File không có dòng dữ liệu nào.")
        if len(rows) > MAX_IMPORT_ROWS:
            raise BusinessRuleViolation(message=f"File có {len(rows)} dòng, tối đa {MAX_IMPORT_ROWS} dòng.")

    def evaluate(self, rows: Sequence[ImportRow], existing_codes: set[str]) -> ImportEvaluation:
        """Validate every row and decide its action (BR-05, BR-06)."""
        counts = Counter(row.code for row in rows if row.code)
        unique_rule = UniqueCodeInFileRule({code for code, n in counts.items() if n > 1})
        rules = (*self.rules(), unique_rule)
        evaluations = []
        for row in rows:
            violations = tuple(self.collect_violations(row, rules))
            if violations:
                action = ImportAction.REJECT
            else:
                action = ImportAction.UPDATE if row.code in existing_codes else ImportAction.CREATE
            evaluations.append(RowEvaluation(row=row, action=action, violations=violations))
        return ImportEvaluation(rows=tuple(evaluations))

    def to_product(self, row: ImportRow, existing: Product | None) -> Product:
        """BR-06: update the existing product (keep id) or create a new one. Row must be valid."""
        values = {
            "code": row.code,
            "name": row.name,
            "unit": row.unit or DEFAULT_UNIT,
            "quantity": int(row.quantity or 0),
            "unit_price": row.unit_price,
        }
        if existing is None:
            return Product(**values)
        return existing.model_copy(update=values)
