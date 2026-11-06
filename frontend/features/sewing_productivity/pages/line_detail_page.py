"""Screen 2 - Line Detail: each line day by day, the period rows and the factory total."""

import streamlit as st

from backend.core.gateway import gateway
from backend.features.sewing_productivity import SewingProductivityController
from backend.features.sewing_productivity.dto.display_names import (
    EFFICIENCY_NO_RATIO,
    EFFICIENCY_SUM,
    EFFICIENCY_SYSTEM,
    TARGET_NO_RATIO,
    TARGET_SUM,
    TARGET_SYSTEM,
    english_name,
    english_terms,
)
from backend.features.sewing_productivity.dto.export_dto import ExportWeeklyRequest
from backend.features.sewing_productivity.dto.line_detail_dto import LineDetailRequest
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, empty_state, panel
from frontend.features.sewing_productivity.components.report_cells import (
    PERIOD_LABEL,
    ColumnSpec,
    column_rows,
    day_text,
    long_table_height,
    number_cells,
    right_text_columns,
    spec_columns,
    spec_labels,
)
from frontend.features.sewing_productivity.components.report_filters import (
    NO_DATA_IN_RANGE,
    REPORT_SPINNER,
    load_filter_options,
    multi_filter,
    period_and_factory,
    show_data_times,
)

LINE_COLUMNS: tuple[ColumnSpec, ...] = (
    ("Output", "output", 0, "", None),
    (TARGET_SYSTEM, "target_a", 0, "", None),
    (EFFICIENCY_SYSTEM, "efficiency_a", 1, "%", "efficiency_a_below"),
    (TARGET_SUM, "target_b", 0, "", None),
    (EFFICIENCY_SUM, "efficiency_b", 1, "%", "efficiency_b_below"),
    (TARGET_NO_RATIO, "target_no_ratio", 0, "", None),
    (EFFICIENCY_NO_RATIO, "efficiency_no_ratio", 1, "%", None),
    ("CM earning", "cm_earning", 2, "", None),
    ("Sewers", "sewers", 1, "", None),
    ("Working hours", "hours", 2, "", None),
    ("MO 8h", "mo8h", 2, "", "mo8h_below"),
)


class LineDetailPage(BasePage):
    title = "Line Detail"
    icon = "🧵"
    slug = "line-detail"
    description = "See each line day by day."
    menu_group = "Reports"

    def render(self) -> None:
        feature = gateway.open(SewingProductivityController)
        options = load_filter_options(feature)
        if options is None:
            return
        with panel("Filters", icon="🔎"):
            from_date, to_date, factory = period_and_factory(
                self.key, options.default_week_from, options.default_week_to
            )
            first, second, third = st.columns(3)
            with first:
                lines = multi_filter("Line", options.lines_by_factory.get(factory, []), self.key("lines"))
            with second:
                customer_groups = multi_filter("Customer group", options.customer_groups, self.key("customer_groups"))
            with third:
                product_groups = multi_filter("Product group", options.product_groups, self.key("product_groups"))
        show_data_times(options)

        with st.spinner(REPORT_SPINNER):
            data = feature.get_line_detail(
                LineDetailRequest(
                    from_date=from_date,
                    to_date=to_date,
                    factory=factory,
                    lines=lines,
                    customer_groups=customer_groups,
                    product_groups=product_groups,
                )
            )
        if not data.has_data:
            empty_state(NO_DATA_IN_RANGE)
            return
        if data.note:
            st.info(english_terms(data.note), icon=":material/info:")

        with panel("Lines by day", icon="🧵"):
            data_table(
                column_rows(
                    {
                        "Line": [english_name(row.line) for row in data.rows],
                        "Date": [day_text(row.work_date, PERIOD_LABEL) for row in data.rows],
                        **spec_columns(data.rows, LINE_COLUMNS),
                    }
                ),
                column_config={
                    "Line": st.column_config.TextColumn(pinned=True),
                    **right_text_columns(spec_labels(LINE_COLUMNS)),
                },
                height=long_table_height(len(data.rows)),
                key=self.key("lines_table"),
            )
        with panel("Factory by day", icon="🏭"):
            data_table(
                column_rows(
                    {
                        "Date": [day.work_date for day in data.factory_days],
                        "Workers": number_cells([day.workers for day in data.factory_days], 1),
                        "Working hours": number_cells([day.hours for day in data.factory_days], 2),
                    }
                ),
                column_config={
                    "Date": st.column_config.DateColumn(format="DD/MM/YYYY"),
                    **right_text_columns(["Workers", "Working hours"]),
                },
                key=self.key("factory_days"),
            )

        export_request = ExportWeeklyRequest(
            from_date=from_date,
            to_date=to_date,
            factories=[factory],
            customer_groups=customer_groups,
            product_groups=product_groups,
            english=True,
        )
        download_button(
            lambda: feature.export_weekly_report(export_request),
            label="Download weekly report (Excel)",
            key=self.key("export"),
            primary=True,
            file_name=f"weekly-report_{from_date.isoformat()}_{to_date.isoformat()}.xlsx",
        )
        if lines:
            st.caption("The Excel file has every line of the chosen factory.")
