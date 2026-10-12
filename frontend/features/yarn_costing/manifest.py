"""How "Tính giá sợi" appears on Home and in the sidebar menu."""

from frontend.core.feature_manifest import FeatureManifest
from frontend.features.yarn_costing.pages.dashboard_page import DashboardPage
from frontend.features.yarn_costing.pages.excel_import_page import ExcelImportPage
from frontend.features.yarn_costing.pages.loss_group_page import LossGroupPage
from frontend.features.yarn_costing.pages.master_data_page import MasterDataPage
from frontend.features.yarn_costing.pages.nsm_pricing_page import NsmPricingPage
from frontend.features.yarn_costing.pages.price_list_page import PriceListPage
from frontend.features.yarn_costing.pages.user_audit_page import UserAuditPage
from frontend.features.yarn_costing.pages.yarn_request_page import YarnRequestPage

FEATURE = FeatureManifest(
    key="yarn_costing",
    title="Tính giá sợi",
    description="Thay thế hoàn toàn file Excel tính giá sợi của Xưởng Sợi 1 và Sợi 4: từ yêu cầu của Sales đến bảng giá có mã kế toán.",
    icon="🧵",
    group="Tính Giá Sợi",
    owner="Phòng SO",
    pages=(
        # sắp theo nhóm người dùng: Dùng chung, Sales, Xưởng sợi, Phòng SO (Kế toán dùng Bảng giá)
        PriceListPage,
        DashboardPage,
        YarnRequestPage,
        NsmPricingPage,
        LossGroupPage,
        MasterDataPage,
        ExcelImportPage,
        UserAuditPage,
    ),
)
