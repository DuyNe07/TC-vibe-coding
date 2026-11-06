"""Screen 1 - Overview: the factories and HCM side by side, the weekly Excel file and the charts."""

import streamlit as st

from backend.core.gateway import gateway
from backend.features.sewing_productivity import SewingProductivityController
from backend.features.sewing_productivity.dto.display_names import (
    EFFICIENCY_SYSTEM,
    HCM_COLUMN,
    english_name,
    english_terms,
)
from backend.features.sewing_productivity.dto.export_dto import ExportWeeklyRequest
from backend.features.sewing_productivity.dto.overview_dto import ChartsRequest, OverviewRequest, RankingMetric
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, empty_state, panel
from frontend.features.sewing_productivity.components.overview_charts import (
    daily_charts,
    group_summary,
    ranking_charts,
)
from frontend.features.sewing_productivity.components.report_cells import (
    full_table_height,
    metric_columns,
    metric_rows,
    metric_table_columns,
)
from frontend.features.sewing_productivity.components.report_filters import (
    NO_DATA_IN_RANGE,
    REPORT_SPINNER,
    load_filter_options,
    multi_filter,
    period_and_factories,
    show_data_times,
)

# BR-59 the rows of the system kind, hidden in the table until the toggle is on
SYSTEM_METRICS = frozenset({"Mục tiêu A", "Hiệu suất A", "% so với mục tiêu của hiệu suất A"})


class OverviewPage(BasePage):
    title = "Overview"
    icon = "📊"
    description = "Compare the factories over a period."
    menu_group = "Reports"

    def render(self) -> None:
        feature = gateway.open(SewingProductivityController)
        options = load_filter_options(feature)
        if options is None:
            return
        with panel("Filters", icon="🔎"):
            from_date, to_date, factories = period_and_factories(
                self.key, options.default_week_from, options.default_week_to
            )
            left, right = st.columns(2)
            with left:
                customer_groups = multi_filter("Customer group", options.customer_groups, self.key("customer_groups"))
            with right:
                product_groups = multi_filter("Product group", options.product_groups, self.key("product_groups"))
        show_data_times(options)

        filters = {
            "from_date": from_date,
            "to_date": to_date,
            "factories": factories,
            "customer_groups": customer_groups,
            "product_groups": product_groups,
        }
        with st.spinner(REPORT_SPINNER):
            data = feature.get_overview(OverviewRequest(**filters))  # BR-30 stops the page here, filters stay on screen
        if not data.has_data:
            empty_state(NO_DATA_IN_RANGE)
            return
        if data.note:
            st.info(english_terms(data.note), icon=":material/info:")

        group_summary(data.metrics, factories)
        columns = metric_table_columns(data.metrics, factories)
        with panel("Metrics by factory", icon="📋"):
            show_system = st.toggle(
                f"Show {EFFICIENCY_SYSTEM}", key=self.key("show_system"), persist_state="session"
            )  # BR-59
            metrics = data.metrics if show_system else [m for m in data.metrics if m.metric not in SYSTEM_METRICS]
            data_table(
                metric_rows(metrics, columns),
                column_config=metric_columns(columns),
                height=full_table_height(len(metrics)),
                key=self.key("metrics"),
            )
            if HCM_COLUMN in columns:
                members = " + ".join(english_name(name) for name in factories if name != "Fac 1")
                st.caption(f"HCM = {members}: calculated from their totals, not an average of their percentages.")
        export_request = ExportWeeklyRequest(**filters, english=True)
        download_button(
            lambda: feature.export_weekly_report(export_request),
            label="Download weekly report (Excel)",
            key=self.key("export"),
            primary=True,
            file_name=f"weekly-report_{from_date.isoformat()}_{to_date.isoformat()}.xlsx",
        )

        chart_area = st.container()
        rank_area = st.container()
        with rank_area:  # the choice sits under the 4 charts but all 5 charts need its value
            metric = st.segmented_control(
                "Ranking metric",
                [item.value for item in RankingMetric],
                default=RankingMetric.EFFICIENCY_B.value,
                required=True,
                format_func=english_name,
                key=self.key("ranking_metric"),
                persist_state="session",
            )
        with chart_area, st.spinner(REPORT_SPINNER):
            charts = feature.get_charts(ChartsRequest(**filters, ranking_metric=metric))
        with chart_area:
            daily_charts(charts, data.metrics, self.key)
        with rank_area:
            ranking_charts(charts, metric, self.key)
