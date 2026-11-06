"""Screen 3 - Daily Report: the factories and HCM on one day, then the lines of one factory."""

import streamlit as st

from backend.core.gateway import gateway
from backend.features.sewing_productivity import SewingProductivityController
from backend.features.sewing_productivity.dto.daily_dto import DailyReportRequest
from backend.features.sewing_productivity.dto.display_names import english_name
from backend.features.sewing_productivity.dto.export_dto import ExportDailyRequest
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, empty_state, panel
from frontend.features.sewing_productivity.components.report_cells import (
    ColumnSpec,
    column_rows,
    full_table_height,
    metric_columns,
    metric_rows,
    metric_table_columns,
    right_text_columns,
    spec_columns,
    spec_labels,
)
from frontend.features.sewing_productivity.components.report_filters import (
    FACTORIES,
    NO_DATA_ON_DAY,
    REPORT_SPINNER,
    date_filter,
    factory_filter,
    load_filter_options,
    show_data_times,
)

LINE_COLUMNS: tuple[ColumnSpec, ...] = (
    ("Output", "output", 0, "", None),
    ("CM earning", "cm_earning", 2, "", None),
    ("Working hours", "hours", 2, "", None),
    ("Sewers", "sewers", 1, "", None),
    ("MO", "mo", 2, "", None),
    ("MO 8h", "mo8h", 2, "", "mo8h_below"),
    ("Mismatched-strength output", "mismatched_output", 0, "", None),
)


class DailyReportPage(BasePage):
    title = "Daily Report"
    icon = "📅"
    slug = "daily"
    description = "See the results of one day."
    menu_group = "Reports"

    def render(self) -> None:
        feature = gateway.open(SewingProductivityController)
        options = load_filter_options(feature)
        if options is None:
            return
        with panel("Filters", icon="🔎"):
            report_date = date_filter("Date", options.latest_date, self.key("report_date"))
        show_data_times(options)

        metrics_area = st.container()  # shown first, but its data needs the factory chosen in the block below
        with panel("Lines on this day", icon="🧵"):
            factory = factory_filter(self.key("factory"))
            with st.spinner(REPORT_SPINNER):
                data = feature.get_daily_report(DailyReportRequest(report_date=report_date, factory=factory))
            if not data.has_data:
                with metrics_area:
                    empty_state(NO_DATA_ON_DAY)
                return
            data_table(
                column_rows(
                    {
                        "Line": [english_name(row.line) for row in data.lines],
                        **spec_columns(data.lines, LINE_COLUMNS),
                    }
                ),
                column_config=right_text_columns(spec_labels(LINE_COLUMNS)),
                key=self.key("lines_table"),
                empty_message=NO_DATA_ON_DAY,
            )
        columns = metric_table_columns(data.metrics, FACTORIES)
        with metrics_area, panel("Metrics by factory", icon="📋"):
            data_table(
                metric_rows(data.metrics, columns),
                column_config=metric_columns(columns),
                height=full_table_height(len(data.metrics)),
                key=self.key("metrics"),
            )
        export_request = ExportDailyRequest(report_date=report_date, english=True)
        download_button(
            lambda: feature.export_daily_report(export_request),
            label="Download Excel",
            key=self.key("export"),
            primary=True,
            file_name=f"daily-report_{report_date.isoformat()}.xlsx",
        )
