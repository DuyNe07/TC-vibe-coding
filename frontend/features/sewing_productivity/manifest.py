"""How "Sewing Performance" appears on Home (card) and in its own sidebar menu."""

from frontend.core.feature_manifest import FeatureManifest
from frontend.features.sewing_productivity.pages.catalogs_page import CatalogsPage
from frontend.features.sewing_productivity.pages.data_update_page import DataUpdatePage
from frontend.features.sewing_productivity.pages.goals_page import GoalsPage
from frontend.features.sewing_productivity.pages.line_detail_page import LineDetailPage
from frontend.features.sewing_productivity.pages.monthly_report_page import MonthlyReportPage
from frontend.features.sewing_productivity.pages.overview_page import OverviewPage

FEATURE = FeatureManifest(
    key="sewing_productivity",
    title="Sewing Performance",
    description="Track and analyse the performance of the sewing factories over any period.",
    icon="🧵",
    group="Production",
    owner="PI - SO team",
    roles=(("UPDATER", "Data updater"),),
    pages=(
        OverviewPage,
        LineDetailPage,
        MonthlyReportPage,  # Sewing metrics
        # Daily Report and MO by Line left the menu on 2026-11-12, Line performance on 2026-11-13 (merged into Line
        # Detail, which downloads its Excel file) - user's requests; their data stays
        DataUpdatePage,
        GoalsPage,
        CatalogsPage,
    ),
)
