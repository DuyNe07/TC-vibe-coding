"""Row-level rules BR-01..BR-05 (docs/business/sample_product_import.md, section 7)."""

import re

from backend.core.base import BaseBusinessRule
from backend.features.sample_product_import.models.import_row import ImportRow

CODE_PATTERN = re.compile(r"^[A-Z0-9-]{1,20}$")


class ProductCodeRule(BaseBusinessRule[ImportRow]):
    code = "BR-01"
    message = "Mã SP bắt buộc, chỉ gồm chữ in hoa, số, dấu '-' và tối đa 20 ký tự."
    field = "code"

    def is_satisfied_by(self, target: ImportRow) -> bool:
        return bool(CODE_PATTERN.match(target.code))


class ProductNameRule(BaseBusinessRule[ImportRow]):
    code = "BR-02"
    message = "Tên sản phẩm bắt buộc và tối đa 200 ký tự."
    field = "name"

    def is_satisfied_by(self, target: ImportRow) -> bool:
        return 0 < len(target.name) <= 200


class QuantityRule(BaseBusinessRule[ImportRow]):
    code = "BR-03"
    message = "Số lượng bắt buộc, phải là số nguyên ≥ 0."
    field = "quantity"

    def is_satisfied_by(self, target: ImportRow) -> bool:
        value = target.quantity
        return value is not None and value >= 0 and value == value.to_integral_value()


class UnitPriceRule(BaseBusinessRule[ImportRow]):
    code = "BR-04"
    message = "Đơn giá bắt buộc và phải lớn hơn 0."
    field = "unit_price"

    def is_satisfied_by(self, target: ImportRow) -> bool:
        return target.unit_price is not None and target.unit_price > 0


class UniqueCodeInFileRule(BaseBusinessRule[ImportRow]):
    code = "BR-05"
    message = "Mã SP bị trùng trong file."
    field = "code"

    def __init__(self, duplicated_codes: set[str]) -> None:
        self.duplicated_codes = duplicated_codes

    def is_satisfied_by(self, target: ImportRow) -> bool:
        return target.code not in self.duplicated_codes

    def describe_violation(self, target: ImportRow) -> str:
        return f"Mã SP '{target.code}' bị trùng trong file."
