"""Screen 2 Line Detail blocks (sửa 2026-11-12, 2026-11-13): the line table (BR-83, BR-86, BR-87) and the details of
the line picked (BR-84, BR-88)."""

from typing import Any

import streamlit as st

from backend.features.sewing_productivity.dto.display_names import english_name
from backend.features.sewing_productivity.dto.line_detail_dto import LineDetailResponse, LineOverviewDTO
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, panel, section_title
from frontend.features.sewing_productivity.components.line_trend_blocks import TrendLoader, line_trend
from frontend.features.sewing_productivity.components.number_format import format_number
from frontend.features.sewing_productivity.components.report_cells import (
    BELOW_MARK,
    BELOW_NOTE,
    ColumnSpec,
    column_rows,
    day_text,
    full_table_height,
    number_cells,
    right_text_columns,
    spec_labels,
)

LINE_COLUMN = "Line"
EFFICIENCY_COLUMN = "%Efficiency (with ratio)"
MATCHING_COLUMN = "Matching ratio"
ALERT_COLUMN = "Alert"
# plain digits (sửa 2026-11-13): the bold letters of Unicode looked thin on screen; MO 8h keeps ▼ (BR-83)
TEXT_COLUMNS: tuple[ColumnSpec, ...] = (
    ("Output", "output", 0, "", None),
    ("MO 8h", "mo8h", 2, "", "mo8h_below"),
    ("Working hours", "hours", 2, "", None),
)
CHANGEOVER_COLUMN = "Changeover"
EFFICIENCY_BAR_MAX = 120  # a bar is full from 120%; the number next to it stays exact
TABLE_HELP = (
    "%Efficiency (with ratio): output / Standard output of SMV (have efficiency ratio). Matching ratio: output of the "
    "product groups that are strong groups of the line (Line Strength file) / output counted; unclassified products "
    "and lines without a strength are left out. Changeover: customer + SMV + CM codes new on the line in the chosen "
    "dates (back after at least one working day away counts again). Pick a line to see its strength and its orders."
)
MATCH_TEXT = {True: "Yes", False: "No", None: "-"}
NO_STRENGTH = "No strength saved for this line. Upload the Line Strength file on Data Update."


def _percent_bar(label: str, maximum: float, help_text: str | None = None, pinned: bool = False) -> Any:
    """UI concept 2026-11-13: a bar with the exact number, coloured from red (low) to green (high)."""
    return st.column_config.ProgressColumn(
        label, format="%.1f%%", min_value=0, max_value=maximum, help=help_text, color="auto", pinned=pinned
    )


def _plain_columns(rows: list[LineOverviewDTO]) -> dict[str, list[str]]:
    """Plain digits, right-aligned, ▼ on MO 8h (BR-83); no Unicode bold letters (they looked thin, 2026-11-13)."""
    return {
        label: number_cells(
            [getattr(row, field) for row in rows],
            decimals,
            suffix,
            [getattr(row, flag) for row in rows] if flag else None,
        )
        for label, field, decimals, suffix, flag in TEXT_COLUMNS
    }


def _alert(row: LineOverviewDTO) -> str:
    """UI concept 2026-11-13: the ▼ of a bar cell (a bar cannot carry it), then the one of MO 8h."""
    marks = [f"{BELOW_MARK} Eff" if row.efficiency_below else "", f"{BELOW_MARK} MO 8h" if row.mo8h_below else ""]
    return "  ".join(mark for mark in marks if mark)


def line_table(page: BasePage, rows: list[LineOverviewDTO]) -> LineOverviewDTO | None:
    """BR-83 one row per line and the Total row; returns the line picked (the Total row picks nothing)."""
    with panel("Lines", icon="🧵", description=TABLE_HELP):
        texts = _plain_columns(rows)
        picked = data_table(
            column_rows(
                {
                    LINE_COLUMN: [english_name(row.line) for row in rows],
                    EFFICIENCY_COLUMN: [row.efficiency for row in rows],
                    "Output": texts["Output"],
                    "MO 8h": texts["MO 8h"],
                    "Working hours": texts["Working hours"],
                    MATCHING_COLUMN: [row.matching_ratio for row in rows],
                    CHANGEOVER_COLUMN: number_cells([row.changeover for row in rows], 0),
                    ALERT_COLUMN: [_alert(row) for row in rows],
                }
            ),
            column_config={
                LINE_COLUMN: st.column_config.TextColumn(pinned=True),
                EFFICIENCY_COLUMN: _percent_bar(EFFICIENCY_COLUMN, EFFICIENCY_BAR_MAX, pinned=True),
                MATCHING_COLUMN: _percent_bar(MATCHING_COLUMN, 100),
                **right_text_columns([*spec_labels(TEXT_COLUMNS), CHANGEOVER_COLUMN]),
            },
            column_order=[  # pinned columns always stay on the left: Line, then %Efficiency (UI concept 2026-11-13)
                LINE_COLUMN,
                EFFICIENCY_COLUMN,
                "Output",
                "MO 8h",
                "Working hours",
                MATCHING_COLUMN,
                CHANGEOVER_COLUMN,
                ALERT_COLUMN,
            ],  # fmt: skip
            height=full_table_height(len(rows)),
            selection="single",
            key=page.key("line_overview"),
        )
        st.caption(f"{BELOW_NOTE}. An empty bar cell means no number (-).")
    if not picked:
        return None
    chosen = next((row for row in rows if english_name(row.line) == picked[0][LINE_COLUMN]), None)
    return None if chosen is None or chosen.is_total else chosen


def line_details(
    page: BasePage, data: LineDetailResponse, line: str, trend: TrendLoader | None = None, filter_note: str = ""
) -> None:
    """BR-84 the strength of the line and the base orders it made in the chosen dates; BR-90 (thêm 2026-11-13 lần 2)
    its "Line trend" above the orders; BR-91 the filters in use with a link back up to them."""
    strength = next((item for item in data.strengths if item.line == line), None)
    with panel(f"{english_name(line)}: strength and orders", icon="🔍"):
        if filter_note:
            st.caption(filter_note)
        if strength is None:
            st.info(NO_STRENGTH, icon=":material/info:")
        else:
            groups = ", ".join(strength.strong_groups) or "-"
            st.markdown(
                f"**Strong item groups:** {groups}  \n**Buyer's strength:** {strength.buyers or '-'}  \n"
                f"**Changeover speed:** {strength.changeover_speed or '-'}  \n**Remark:** {strength.remark or '-'}"
            )
        if trend is not None:
            line_trend(page, english_name(line), trend)
        orders = [order for order in data.line_orders if order.line == line]
        section_title(f"Orders made in the chosen dates ({len(orders)})")
        data_table(
            [
                {
                    "Order": order.base_po,
                    "Customer": order.customers,
                    "Style": order.styles,
                    "Product type": order.product_types,
                    "SMV": format_number(order.smv, 2),  # BR-88
                    "CM price": format_number(order.cm_price, 2),
                    "Output": format_number(order.output),
                    EFFICIENCY_COLUMN: order.efficiency,  # BR-88
                    "First day on line": day_text(order.first_day),
                    "Matches strength": MATCH_TEXT[order.matches],
                }
                for order in orders
            ],
            column_config={
                **right_text_columns(["SMV", "CM price", "Output"]),
                EFFICIENCY_COLUMN: _percent_bar(
                    EFFICIENCY_COLUMN, EFFICIENCY_BAR_MAX, "Output of the order / its target with ratio"
                ),
            },
            key=page.key(f"orders_{line}"),
            empty_message="No order in the chosen dates.",
        )
