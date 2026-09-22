"""How "Nhập sản phẩm từ Excel (mẫu)" appears on Home and in the sidebar menu."""

from frontend.core.feature_manifest import FeatureManifest
from frontend.features.sample_product_import.pages.import_page import ImportPage
from frontend.features.sample_product_import.pages.product_list_page import ProductListPage

FEATURE = FeatureManifest(
    key="sample_product_import",
    title="Nhập sản phẩm từ Excel (mẫu)",
    description="Chức năng mẫu: nhập danh sách sản phẩm từ Excel, kiểm tra quy tắc nghiệp vụ, lưu và xuất báo cáo tồn kho.",
    icon="📦",
    group="Chức năng mẫu",
    owner="TC Vibe Coding",
    order=900,
    pages=(ImportPage, ProductListPage),
)
