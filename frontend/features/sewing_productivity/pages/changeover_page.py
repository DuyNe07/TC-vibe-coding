"""Screen 6 - Đổi mã hàng: the changeover KPI and the counts including re-runs, in 4 tabs."""

import streamlit as st

from backend.core.gateway import gateway
from backend.features.sewing_productivity import SewingProductivityController
from backend.features.sewing_productivity.dto.changeover_dto import ChangeoverRequest
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, empty_state, panel
from frontend.features.sewing_productivity.components.report_cells import (
    ColumnSpec,
    column_rows,
    long_table_height,
    right_text_columns,
    spec_columns,
    spec_labels,
)
from frontend.features.sewing_productivity.components.report_filters import (
    NO_DATA_IN_RANGE,
    REPORT_SPINNER,
    lines_of,
    load_filter_options,
    multi_filter,
    period_and_factories,
    show_data_times,
)

TAB_LABELS = ("Theo xưởng", "Theo tháng", "Theo chuyền", "Chi tiết")
FACTORY_COLUMNS: tuple[ColumnSpec, ...] = (
    ("Số lần đổi KPI", "kpi_count", 0, "", None),
    ("Số ngày làm việc", "working_days", 0, "", None),
    ("Số chuyền", "line_count", 0, "", None),
    ("KPI đổi mã hàng", "kpi", 3, "", None),
    ("Số lần đổi gồm cả lên lại", "rerun_count", 0, "", None),
    ("Đổi mã hàng tuần", "weekly_count", 0, "", None),
)
MONTH_COLUMNS = FACTORY_COLUMNS[:-1]
LINE_COLUMNS: tuple[ColumnSpec, ...] = (
    ("Số lần đổi KPI", "kpi_count", 0, "", None),
    ("Số lần đổi gồm cả lên lại", "rerun_count", 0, "", None),
)
DETAIL_COLUMNS: tuple[ColumnSpec, ...] = (
    ("SMV", "smv", 2, "", None),
    ("Giá CM", "cm_price", 2, "", None),
)


class ChangeoverPage(BasePage):
    title = "Đổi mã hàng"
    icon = "🔄"
    slug = "changeover"
    description = "Theo dõi KPI đổi mã hàng và số lần đổi gồm cả lên lại."
    menu_group = "Báo cáo"

    def render(self) -> None:
        feature = gateway.open(SewingProductivityController)
        options = load_filter_options(feature)
        if options is None:
            return
        with panel("Bộ lọc", icon="🔎"):
            from_date, to_date, factories = period_and_factories(
                self.key, options.default_month_from, options.latest_date
            )
            lines = multi_filter("Chuyền", lines_of(options, factories), self.key("lines"))
        show_data_times(options)

        request = ChangeoverRequest(from_date=from_date, to_date=to_date, factories=factories, lines=lines)
        with st.spinner(REPORT_SPINNER):
            data = feature.get_changeover(request)
        if not data.has_data:
            empty_state(NO_DATA_IN_RANGE)
            return

        by_factory, by_month, by_line, details = st.tabs(TAB_LABELS, key=self.key("tabs"), on_change="rerun")
        with by_factory:
            if by_factory.open:
                data_table(
                    column_rows(
                        {
                            "Xưởng": [row.factory for row in data.by_factory],
                            **spec_columns(data.by_factory, FACTORY_COLUMNS),
                        }
                    ),
                    column_config=right_text_columns(spec_labels(FACTORY_COLUMNS)),
                    key=self.key("by_factory"),
                )
        with by_month:
            if by_month.open:
                data_table(
                    column_rows(
                        {
                            "Tháng": [row.month for row in data.by_month],
                            "Xưởng": [row.factory for row in data.by_month],
                            **spec_columns(data.by_month, MONTH_COLUMNS),
                        }
                    ),
                    column_config=right_text_columns(spec_labels(MONTH_COLUMNS)),
                    key=self.key("by_month"),
                )
        with by_line:
            if by_line.open:
                data_table(
                    column_rows(
                        {
                            "Xưởng": [row.factory for row in data.by_line],
                            "Chuyền": [row.line for row in data.by_line],
                            **spec_columns(data.by_line, LINE_COLUMNS),
                        }
                    ),
                    column_config=right_text_columns(spec_labels(LINE_COLUMNS)),
                    key=self.key("by_line"),
                )
        with details:
            if details.open:
                data_table(
                    column_rows(
                        {
                            "Ngày": [row.work_date for row in data.details],
                            "Xưởng": [row.factory for row in data.details],
                            "Chuyền": [row.line for row in data.details],
                            "Mã đơn gốc": [row.base_po for row in data.details],
                            "Style": [row.style for row in data.details],
                            **spec_columns(data.details, DETAIL_COLUMNS),
                        }
                    ),
                    column_config={
                        "Ngày": st.column_config.DateColumn(format="DD/MM/YYYY"),
                        **right_text_columns(spec_labels(DETAIL_COLUMNS)),
                    },
                    height=long_table_height(len(data.details)),
                    key=self.key("details"),
                )
        download_button(
            lambda: feature.export_changeover(request),
            label="Tải Excel",
            key=self.key("export"),
            primary=True,
            file_name=f"doi-ma-hang_{from_date.isoformat()}_{to_date.isoformat()}.xlsx",
        )
