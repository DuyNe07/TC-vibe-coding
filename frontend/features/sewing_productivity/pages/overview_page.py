"""Screen 1 - Tổng quan: the 4 factories side by side, the weekly Excel file and the charts."""

import streamlit as st

from backend.core.gateway import gateway
from backend.features.sewing_productivity import SewingProductivityController
from backend.features.sewing_productivity.dto.export_dto import ExportWeeklyRequest
from backend.features.sewing_productivity.dto.overview_dto import ChartsRequest, OverviewRequest, RankingMetric
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, empty_state, panel
from frontend.features.sewing_productivity.components.overview_charts import daily_charts, ranking_charts
from frontend.features.sewing_productivity.components.report_cells import (
    full_table_height,
    metric_columns,
    metric_rows,
)
from frontend.features.sewing_productivity.components.report_filters import (
    NO_DATA_IN_RANGE,
    REPORT_SPINNER,
    load_filter_options,
    multi_filter,
    period_and_factories,
    show_data_times,
)


class OverviewPage(BasePage):
    title = "Tổng quan"
    icon = "📊"
    description = "So sánh 4 xưởng theo khoảng thời gian."
    menu_group = "Báo cáo"

    def render(self) -> None:
        feature = gateway.open(SewingProductivityController)
        options = load_filter_options(feature)
        if options is None:
            return
        with panel("Bộ lọc", icon="🔎"):
            from_date, to_date, factories = period_and_factories(
                self.key, options.default_week_from, options.default_week_to
            )
            left, right = st.columns(2)
            with left:
                customer_groups = multi_filter("Nhóm khách hàng", options.customer_groups, self.key("customer_groups"))
            with right:
                product_groups = multi_filter("Nhóm sản phẩm", options.product_groups, self.key("product_groups"))
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
            st.info(data.note, icon=":material/info:")

        with panel("Chỉ số theo xưởng", icon="📋"):
            data_table(
                metric_rows(data.metrics, factories),
                column_config=metric_columns(factories),
                height=full_table_height(len(data.metrics)),
                key=self.key("metrics"),
            )
        export_request = ExportWeeklyRequest(**filters)
        download_button(
            lambda: feature.export_weekly_report(export_request),
            label="Tải Excel báo cáo tuần",
            key=self.key("export"),
            primary=True,
            file_name=f"bao-cao-tuan_{from_date.isoformat()}_{to_date.isoformat()}.xlsx",
        )

        chart_area = st.container()
        rank_area = st.container()
        with rank_area:  # the choice sits under the 4 charts but all 5 charts need its value
            metric = st.segmented_control(
                "Chỉ số xếp hạng",
                [item.value for item in RankingMetric],
                default=RankingMetric.EFFICIENCY_B.value,
                required=True,
                key=self.key("ranking_metric"),
                persist_state="session",
            )
        with chart_area, st.spinner(REPORT_SPINNER):
            charts = feature.get_charts(ChartsRequest(**filters, ranking_metric=metric))
        with chart_area:
            daily_charts(charts, self.key)
        with rank_area:
            ranking_charts(charts, metric, self.key)
