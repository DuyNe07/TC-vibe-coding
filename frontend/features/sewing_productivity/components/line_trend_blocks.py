"""Screen 2 Line Detail, "Line trend" of the line picked (BR-90, thêm 2026-11-13 lần 2): week / month / year buttons
and the exact numbers in a table right below.

BR-99 (sửa 2026-11-13 lần 5): ONE chart - Output as columns on the left scale, the chosen figure (%Efficiency or MO 8h)
as a line on the right scale - with the numbers written on the marks; "Show numbers" hides them (hover still shows)."""

from collections.abc import Callable

import streamlit as st

from backend.features.sewing_productivity.dto.line_detail_dto import LineTrendPointDTO, PeriodKind
from frontend.core.base_page import BasePage
from frontend.core.components import bar_chart, combo_chart, data_table, section_title
from frontend.features.sewing_productivity.components.report_cells import (
    BELOW_NOTE,
    full_table_height,
    number_cells,
    right_text_columns,
)

KINDS = (PeriodKind.WEEK, PeriodKind.MONTH, PeriodKind.YEAR)
EFFICIENCY = "%Efficiency (with ratio)"
MO8H = "MO 8h"
OUTPUT = "Output (pcs)"
CHART_X = "Period start"
FIGURE_COLUMN = "Figure"
CHART_HEIGHT = 420
# figure -> DTO field, decimals, suffix, "below threshold" flag
FIGURES = {
    OUTPUT: ("output", 0, "", None),
    EFFICIENCY: ("efficiency", 1, "%", "efficiency_below"),
    MO8H: ("mo8h", 2, "", "mo8h_below"),
}
RANGE_TEXT = {
    PeriodKind.WEEK: "last 26 weeks up to the chosen To date",
    PeriodKind.MONTH: "months from 01/01 to the chosen To date",
    PeriodKind.YEAR: "year from 01/01 to the chosen To date",
}
FILTERED_MO8H = "MO 8h is not shown while filtering by customer or product group: only Output is drawn."

TrendLoader = Callable[[PeriodKind], list[LineTrendPointDTO]]


def line_trend(page: BasePage, line: str, load: TrendLoader) -> None:
    """BR-90, BR-91, BR-99 the periods of the line up to the chosen "To" date, in one chart and a table."""
    section_title("Line trend")
    left, middle, right = st.columns([3, 2, 1.4], vertical_alignment="bottom")
    with left:
        kind = st.segmented_control(
            "Period",
            [item.value for item in KINDS],
            default=PeriodKind.WEEK.value,
            required=True,
            key=page.key("trend_kind"),
        )
    with middle:
        figure = st.segmented_control(
            "Line shows", [EFFICIENCY, MO8H], default=EFFICIENCY, required=True, key=page.key("trend_line")
        )
    with right:
        labels = st.toggle("Show numbers", value=True, key=page.key("trend_labels"), persist_state="session")
    points = load(PeriodKind(kind))
    span = RANGE_TEXT[PeriodKind(kind)]
    if not points:
        st.info(f"{line} made nothing in the {span}.", icon=":material/info:")
        return
    st.caption(f"The {span}. Columns: Output (left scale). Line: {figure} (right scale).")
    _chart(page, line, points, figure, labels)
    _number_table(page, line, points)


def _chart(page: BasePage, line: str, points: list[LineTrendPointDTO], figure: str, labels: bool) -> None:
    """BR-99 one column per period and the chosen figure as a line on its own scale."""
    field, decimals, _suffix, _flag = FIGURES[figure]
    kept = [point for point in points if point.output is not None]
    has_line = any(getattr(point, field) is not None for point in kept)
    options = {"height": CHART_HEIGHT, "key": page.key(f"trend_chart_{line}")}
    if not has_line:  # MO 8h under a customer / product filter: nothing to draw as a line
        st.caption(FILTERED_MO8H)
        bar_chart(
            [{CHART_X: point.start, OUTPUT: point.output} for point in kept],
            x=CHART_X,
            y=OUTPUT,
            stacked=False,
            labels=labels,
            **options,
        )
        return
    rows = [
        {
            CHART_X: point.start,
            OUTPUT: round(point.output),
            figure: None if (value := getattr(point, field)) is None else round(value, decimals),
        }
        for point in kept
    ]
    combo_chart(rows, x=CHART_X, bars=OUTPUT, lines=figure, secondary_y=True, labels=labels, **options)


def _number_table(page: BasePage, line: str, points: list[LineTrendPointDTO]) -> None:
    """One row per figure, one column per period (the order of the chart); ▼ below threshold (BR-76)."""
    periods = [point.period for point in points]
    rows = []
    for figure, (field, decimals, suffix, flag) in FIGURES.items():
        flags = [getattr(point, flag) for point in points] if flag else None
        cells = number_cells([getattr(point, field) for point in points], decimals, suffix, flags)
        rows.append({FIGURE_COLUMN: figure, **dict(zip(periods, cells, strict=True))})
    data_table(
        rows,
        column_config={
            FIGURE_COLUMN: st.column_config.TextColumn(pinned=True),
            **right_text_columns(periods),
        },
        height=full_table_height(len(rows)),
        key=page.key(f"trend_table_{line}"),
    )
    if any(point.efficiency_below or point.mo8h_below for point in points):
        st.caption(BELOW_NOTE)
