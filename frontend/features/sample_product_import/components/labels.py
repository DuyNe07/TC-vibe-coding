"""Vietnamese labels for enums of this feature."""

from backend.features.sample_product_import.dto.import_dto import ImportAction
from backend.features.sample_product_import.dto.product_dto import StockStatus

STOCK_STATUS_LABELS = {
    StockStatus.OUT_OF_STOCK: "🔴 Hết hàng",
    StockStatus.LOW: "🟠 Sắp hết",
    StockStatus.IN_STOCK: "🟢 Còn hàng",
}
ACTION_LABELS = {
    ImportAction.CREATE: "➕ Tạo mới",
    ImportAction.UPDATE: "✏️ Cập nhật",
    ImportAction.REJECT: "⛔ Bị loại",
}
