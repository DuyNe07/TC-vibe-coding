"""Screen 1 "Products & customers" (BR-93 to BR-96, thêm 2026-11-13 lần 4): what each factory makes and for whom.

The shared charts keep 6 colours and write no numbers on the marks: the backend sends the 5 biggest product groups and
"Other"; the exact numbers are in the table beside the mix chart and in the hover."""

from collections.abc import Callable

import streamlit as st

from backend.features.sewing_productivity.dto.display_names import english_name
from backend.features.sewing_productivity.dto.overview_dto import ChartsResponse
from frontend.core.components import bar_chart, data_table, panel
from frontend.features.sewing_productivity.components.number_format import format_number
from frontend.features.sewing_productivity.components.report_cells import full_table_height, right_text_columns
from frontend.features.sewing_productivity.components.report_filters import NO_DATA_IN_RANGE

FACTORY = "Factory"
GROUP = "Product group"
CUSTOMER = " "  # the axis title of a horizontal chart: blank, it would cover the names
SHARE = "Share of output (%)"
OUTPUT = "Output (pcs)"
CM_PRICE = "Avg CM price (USD/pc)"
MONTH = "Month"
CHART_HEIGHT = 340

KeyFn = Callable[[str], str]


def products_section(charts: ChartsResponse, key: KeyFn) -> None:
    """BR-92 the area under the daily charts: mix | mix table, top customers | CM price, then the months."""
    st.subheader("👕 Products & customers", anchor=False)
    left, right = st.columns(2)
    with left:
        _mix_chart(charts, key("mix_chart"))
    with right:
        _mix_table(charts, key("mix_table"))
    left, right = st.columns(2)
    with left:
        _customers_chart(charts, key("customers_chart"))
    with right:
        _cm_chart(charts, key("cm_chart"))
    _monthly_chart(charts, key("monthly_chart"))


def _mix_chart(charts: ChartsResponse, key: str) -> None:
    """BR-93 one 100% column per factory and Total, one colour per product group."""
    with panel("Product mix by factory", description="Share of each factory's output. Hover a colour for the number."):
        columns = list(dict.fromkeys(item.column for item in charts.product_shares))
        total = columns[-1] if columns else ""
        groups = [item.group for item in charts.product_shares if item.column == total]  # the colour order
        shares = {(item.column, item.group): item.share or 0 for item in charts.product_shares}
        # every group in every column (0 when absent): the colours follow the first appearance, so they stay the
        # same in every column and match "Product mix by month"
        rows = [
            {FACTORY: english_name(column), GROUP: group, SHARE: round(shares.get((column, group), 0), 1)}
            for column in columns
            for group in groups
        ]
        bar_chart(rows, x=FACTORY, y=SHARE, color=GROUP, height=CHART_HEIGHT, key=key, empty_message=NO_DATA_IN_RANGE)


def _mix_table(charts: ChartsResponse, key: str) -> None:
    """BR-93 every product group: pieces and share per factory and Total, biggest Total first."""
    with panel("Product mix in pieces", description="Pieces (share of the factory's output)."):
        columns = list(dict.fromkeys(item.column for item in charts.product_table))
        cells = {(item.group, item.column): item for item in charts.product_table}
        total = columns[-1] if columns else ""
        groups = [item.group for item in charts.product_table if item.column == total]
        names = [english_name(column) for column in columns]
        rows = []
        for group in groups:
            row: dict[str, str] = {GROUP: group}
            for column, name in zip(columns, names, strict=True):
                item = cells.get((group, column))
                row[name] = (
                    f"{format_number(item.output)} ({format_number(item.share, 1)}%)"
                    if item and item.share is not None
                    else "-"
                )
            rows.append(row)
        data_table(
            rows,
            column_config={GROUP: st.column_config.TextColumn(pinned=True), **right_text_columns(names)},
            height=min(full_table_height(len(rows)), CHART_HEIGHT + 40),
            key=key,
            empty_message=NO_DATA_IN_RANGE,
        )


def _customers_chart(charts: ChartsResponse, key: str) -> None:
    """BR-94 the 10 biggest customer groups, one bar each, coloured by factory (biggest at the top)."""
    with panel("Top 10 customers", description="Output in the chosen dates, split by factory."):
        rows = [
            {CUSTOMER: item.customer, FACTORY: english_name(item.factory), OUTPUT: round(item.output)}
            for item in reversed(charts.top_customers)  # a horizontal chart draws its first row at the bottom
        ]
        bar_chart(
            rows,
            x=CUSTOMER,
            y=OUTPUT,
            color=FACTORY,
            horizontal=True,
            height=CHART_HEIGHT,
            key=key,
            empty_message=NO_DATA_IN_RANGE,
        )


def _cm_chart(charts: ChartsResponse, key: str) -> None:
    """BR-95 the average CM price of each product group, highest first."""
    with panel("Avg CM price by product group", description="CM earning / output of each group (USD per piece)."):
        rows = [{GROUP: item.group, CM_PRICE: round(item.cm_price, 2)} for item in charts.cm_by_group]
        bar_chart(
            rows, x=GROUP, y=CM_PRICE, stacked=False, height=CHART_HEIGHT, key=key, empty_message=NO_DATA_IN_RANGE
        )


def _monthly_chart(charts: ChartsResponse, key: str) -> None:
    """BR-96 the months from 01/01 to the chosen To date, output by product group."""
    with panel("Product mix by month", description="From 01/01 to the chosen To date, output in pieces."):
        rows = [{MONTH: item.start, GROUP: item.group, OUTPUT: round(item.output)} for item in charts.monthly_mix]
        bar_chart(rows, x=MONTH, y=OUTPUT, color=GROUP, height=CHART_HEIGHT, key=key, empty_message=NO_DATA_IN_RANGE)
