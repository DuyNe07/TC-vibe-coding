"""How "Năng suất xưởng may" appears on Home (card) and in its own sidebar menu."""

from frontend.core.feature_manifest import FeatureManifest
from frontend.features.sewing_productivity.pages.catalogs_page import CatalogsPage
from frontend.features.sewing_productivity.pages.changeover_page import ChangeoverPage
from frontend.features.sewing_productivity.pages.daily_report_page import DailyReportPage
from frontend.features.sewing_productivity.pages.data_update_page import DataUpdatePage
from frontend.features.sewing_productivity.pages.goals_page import GoalsPage
from frontend.features.sewing_productivity.pages.line_detail_page import LineDetailPage
from frontend.features.sewing_productivity.pages.line_mo_page import LineMoPage
from frontend.features.sewing_productivity.pages.monthly_report_page import MonthlyReportPage
from frontend.features.sewing_productivity.pages.overview_page import OverviewPage

FEATURE = FeatureManifest(
    key="sewing_productivity",
    title="Năng suất xưởng may",
    description="Theo dõi và phân tích năng suất các xưởng may theo khoảng thời gian bất kỳ.",
    icon="🧵",
    group="Sản xuất",
    owner="Nhóm PI - SO",
    roles=(("UPDATER", "Người cập nhật dữ liệu"),),
    pages=(
        OverviewPage,
        LineDetailPage,
        DailyReportPage,
        MonthlyReportPage,
        LineMoPage,
        ChangeoverPage,
        DataUpdatePage,
        GoalsPage,
        CatalogsPage,
    ),
)
