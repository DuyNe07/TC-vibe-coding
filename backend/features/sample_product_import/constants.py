"""Constants of feature "Nhập sản phẩm từ Excel (mẫu)" (UPPER_CASE values only, no classes)."""

from typing import Final

from backend.features.sample_product_import.models.import_column import ImportColumn

FEATURE_KEY: Final = "sample_product_import"

# BR-10: accepted file formats and limits
ALLOWED_IMPORT_EXTENSIONS: Final = (".xlsx", ".xls")
MAX_IMPORT_FILE_MB: Final = 10
MAX_IMPORT_ROWS: Final = 5000

# Section 5 of docs/business/sample_product_import.md: import template columns
IMPORT_COLUMNS: Final = (
    ImportColumn(field="code", header="Mã SP", required=True, aliases=("ma sp", "ma san pham", "code")),
    ImportColumn(field="name", header="Tên sản phẩm", required=True, aliases=("ten sp", "ten san pham", "name")),
    ImportColumn(field="unit", header="Đơn vị", required=False, aliases=("don vi", "dvt", "unit")),
    ImportColumn(field="quantity", header="Số lượng", required=True, aliases=("so luong", "sl", "quantity", "qty")),
    ImportColumn(
        field="unit_price", header="Đơn giá", required=True, aliases=("don gia", "gia", "unit price", "price")
    ),
)
DEFAULT_UNIT: Final = "cái"
