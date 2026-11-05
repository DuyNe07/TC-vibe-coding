"""Screen 5 - MO theo chuyền: 5 tabs, lines in rows and days in columns."""

from collections.abc import Sequence
from datetime import date
from typing import Any

import streamlit as st

from backend.core.gateway import gateway
from backend.features.sewing_productivity import SewingProductivityController
from backend.features.sewing_productivity.dto.line_mo_dto import LineMoCellDTO, LineMoRequest, LineMoTableDTO
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, empty_state, panel
from frontend.features.sewing_productivity.components.report_cells import (
    PERIOD_LABEL,
    column_rows,
    long_table_height,
    number_cells,
    right_text_columns,
)
from frontend.features.sewing_productivity.components.report_filters import (
    NO_DATA_IN_RANGE,
    REPORT_SPINNER,
    load_filter_options,
    multi_filter,
    period_and_factory,
    show_data_times,
)

MISSING_CELL = LineMoCellDTO()  # a day the line did not work


def day_labels(dates: Sequence[date]) -> list[str]:
    """`DD/MM`; a period over two years needs the year, or the same day of two years would share a column."""
    pattern = "%d/%m/%y" if len({day.year for day in dates}) > 1 else "%d/%m"
    return [day.strftime(pattern) for day in dates]


def _cells(table: LineMoTableDTO, cells: Sequence[LineMoCellDTO]) -> list[str]:
    """Each column is padded on its own, so every column sorts as numbers."""
    return number_cells([cell.value for cell in cells], table.decimals, table.suffix, [cell.below for cell in cells])


def matrix_rows(table: LineMoTableDTO, dates: Sequence[date], labels: Sequence[str]) -> list[dict[str, Any]]:
    columns: dict[str, list[str]] = {"Chuyền": [row.line for row in table.rows]}
    for day, label in zip(dates, labels, strict=True):
        columns[label] = _cells(table, [row.cells.get(day, MISSING_CELL) for row in table.rows])
    columns[PERIOD_LABEL] = _cells(table, [row.period for row in table.rows])
    return column_rows(columns)


class LineMoPage(BasePage):
    title = "MO theo chuyền"
    icon = "💵"
    slug = "line-mo"
    description = "Xem MO 8h của từng chuyền theo ngày."
    menu_group = "Báo cáo"

    def render(self) -> None:
        feature = gateway.open(SewingProductivityController)
        options = load_filter_options(feature)
        if options is None:
            return
        with panel("Bộ lọc", icon="🔎"):
            from_date, to_date, factory = period_and_factory(self.key, options.default_month_from, options.latest_date)
            lines = multi_filter("Chuyền", options.lines_by_factory.get(factory, []), self.key("lines"))
        show_data_times(options)

        request = LineMoRequest(from_date=from_date, to_date=to_date, factory=factory, lines=lines)
        with st.spinner(REPORT_SPINNER):
            data = feature.get_line_mo(request)
        if not data.has_data:
            empty_state(NO_DATA_IN_RANGE)
            return

        labels = day_labels(data.dates)
        column_config = {
            "Chuyền": st.column_config.TextColumn(pinned=True),
            **right_text_columns([*labels, PERIOD_LABEL]),
        }
        tabs = st.tabs([table.title for table in data.tables], key=self.key("tabs"), on_change="rerun")
        for index, (tab, table) in enumerate(zip(tabs, data.tables, strict=True)):
            with tab:
                if tab.open:
                    data_table(
                        matrix_rows(table, data.dates, labels),
                        column_config=column_config,
                        height=long_table_height(len(table.rows)),
                        key=self.key(f"table_{index}"),
                    )
        download_button(
            lambda: feature.export_line_mo(request),
            label="Tải Excel",
            key=self.key("export"),
            primary=True,
            file_name=f"mo-theo-chuyen_{factory}_{from_date.isoformat()}_{to_date.isoformat()}.xlsx",
        )
