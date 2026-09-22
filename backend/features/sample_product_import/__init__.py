"""Feature "Nhập sản phẩm từ Excel (mẫu)". Business spec: docs/business/sample_product_import.md

Public API = the top layer only. Pages use: gateway.open(SampleProductImportController)
Layers below (services, business, builders, repositories, models) are internal to this feature.
"""

from backend.features.sample_product_import.controllers.sample_product_import_controller import (
    SampleProductImportController,
)

__all__ = ["SampleProductImportController"]
