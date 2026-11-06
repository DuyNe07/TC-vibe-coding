"""Screen 4 - Monthly Report: each factory day by day, with a total row."""

import streamlit as st

from backend.core.gateway import gateway
from backend.features.sewing_productivity import SewingProductivityController
from backend.features.sewing_productivity.dto.display_names import (
    EFFICIENCY_NO_RATIO,
    EFFICIENCY_SUM,
    TARGET_NO_RATIO,
    TARGET_SUM,
    english_name,
)
from backend.features.sewing_productivity.dto.monthly_dto import MonthlyReportRequest
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, empty_state, panel
from frontend.features.sewing_productivity.components.report_cells import (
    TOTAL_LABEL,
    ColumnSpec,
    column_rows,
    day_text,
    long_table_height,
    right_text_columns,
    spec_columns,
    spec_labels,
)
from frontend.features.sewing_productivity.components.report_filters import (
    NO_DATA_IN_RANGE,
    REPORT_SPINNER,
    load_filter_options,
    period_and_factories,
    show_data_times,
)

MONTHLY_COLUMNS: tuple[ColumnSpec, ...] = (
    ("MO", "mo", 2, "", None),
    ("Working hours", "hours", 2, "", None),
    ("MO 8h", "mo8h", 2, "", "mo8h_below"),
    ("Output", "output", 0, "", None),
    (TARGET_SUM, "target_b", 0, "", None),
    (EFFICIENCY_SUM, "efficiency_b", 1, "%", "efficiency_b_below"),
    (TARGET_NO_RATIO, "target_no_ratio", 0, "", None),
    (EFFICIENCY_NO_RATIO, "efficiency_no_ratio", 1, "%", None),
    ("CM earning", "cm_earning", 2, "", None),
    ("Workers", "workers", 1, "", None),
)


class MonthlyReportPage(BasePage):
    title = "Monthly Report"
    icon = "🗓️"
    slug = "monthly"
    description = "See each factory day by day."
    menu_group = "Reports"

    def render(self) -> None:
        feature = gateway.open(SewingProductivityController)
        options = load_filter_options(feature)
        if options is None:
            return
        with panel("Filters", icon="🔎"):
            from_date, to_date, factories = period_and_factories(
                self.key, options.default_month_from, options.latest_date
            )
        show_data_times(options)

        request = MonthlyReportRequest(from_date=from_date, to_date=to_date, factories=factories, english=True)
        with st.spinner(REPORT_SPINNER):
            data = feature.get_monthly_report(request)
        if not data.has_data:
            empty_state(NO_DATA_IN_RANGE)
            return

        for factory in data.factories:
            with panel(english_name(factory.factory), icon="🏭"):
                data_table(
                    column_rows(
                        {
                            "Date": [day_text(row.work_date, TOTAL_LABEL) for row in factory.rows],
                            **spec_columns(factory.rows, MONTHLY_COLUMNS),
                        }
                    ),
                    column_config=right_text_columns(spec_labels(MONTHLY_COLUMNS)),
                    height=long_table_height(len(factory.rows)),
                    key=self.key(f"table_{factory.factory}"),
                    empty_message=NO_DATA_IN_RANGE,
                )
        download_button(
            lambda: feature.export_monthly_report(request),
            label="Download Excel",
            key=self.key("export"),
            primary=True,
            file_name=f"monthly-report_{from_date.isoformat()}_{to_date.isoformat()}.xlsx",
        )
