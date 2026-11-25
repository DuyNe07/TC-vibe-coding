"""How "Tính giá vải dệt" appears on Home (card) and in its own sidebar menu."""

from backend.features.woven_costing.dto.common_dto import ROLE_LABELS, RoleCode
from frontend.core.feature_manifest import FeatureManifest
from frontend.features.woven_costing.pages.costsheet_list_page import CostsheetListPage
from frontend.features.woven_costing.pages.costsheet_page import CostsheetPage
from frontend.features.woven_costing.pages.customer_page import CustomerPage
from frontend.features.woven_costing.pages.dyeing_job_page import DyeingJobPage
from frontend.features.woven_costing.pages.exchange_rate_page import ExchangeRatePage
from frontend.features.woven_costing.pages.fabric_data_page import FabricDataPage
from frontend.features.woven_costing.pages.my_tasks_page import MyTasksPage
from frontend.features.woven_costing.pages.norm_parameter_page import NormParameterPage

FEATURE = FeatureManifest(
    key="woven_costing",
    title="Tính giá vải dệt",
    description="Sales Woven lập, lưu, duyệt costsheet vải dệt trên một ứng dụng dùng chung dữ liệu gốc do SO cập nhật, thay cho các file Excel tính giá.",
    icon="🧵",
    group="Kinh doanh Woven",
    owner="Sales Woven (team FS)",
    pages=(
        # nhóm Sales
        CostsheetListPage,
        CostsheetPage,
        DyeingJobPage,
        MyTasksPage,
        # nhóm Phòng SO
        FabricDataPage,
        NormParameterPage,
        ExchangeRatePage,
        CustomerPage,
    ),
    # Vai trò của ứng dụng (BR-51): quản trị viên tích cho từng tài khoản / nhóm ở trang /admin.
    roles=tuple((code.value, ROLE_LABELS[code]) for code in RoleCode),
)
