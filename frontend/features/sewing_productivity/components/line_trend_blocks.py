"""Screen 2 Line Detail, "Line trend" of the line picked (BR-90, thêm 2026-11-13 lần 2): week / month / year buttons,
Output as columns, the chosen figure as a line under it on the same time axis, the exact numbers right below.

The shared charts cannot yet draw columns and a line in one frame nor write the numbers on the points: the number table
right under the charts carries them (UI concept 2026-11-13 lần 2)."""

from collections.abc import Callable

import streamlit as st

from backend.core.config import get_settings
from backend.features.sewing_productivity.dto.line_detail_dto import LineTrendPointDTO, PeriodKind
from frontend.core.base_page import BasePage
from frontend.core.components import bar_chart, data_table, line_chart, section_title
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
CHART_HEIGHT = 260
# figure -> DTO field, decimals, suffix, "below threshold" flag
FIGURES = {
    OUTPUT: ("output", 0, "", None),
    EFFICIENCY: ("efficiency", 1, "%", "efficiency_below"),
    MO8H: ("mo8h", 2, "", "mo8h_below"),
}
# BR-91 (thêm 2026-11-13 lần 3) the colour groups of the Output columns, in the order of the chart colours
ON_TARGET = "On target"
BELOW_THRESHOLD = "Below threshold"
NO_NUMBER = "No %Efficiency"
RANGE_TEXT = {
    PeriodKind.WEEK: "last 26 weeks up to the chosen To date",
    PeriodKind.MONTH: "months from 01/01 to the chosen To date",
    PeriodKind.YEAR: "year from 01/01 to the chosen To date",
}
FILTERED_MO8H = "MO 8h is not shown while filtering by customer or product group."

TrendLoader = Callable[[PeriodKind], list[LineTrendPointDTO]]


def line_trend(page: BasePage, line: str, load: TrendLoader) -> None:
    """BR-90, BR-91 the periods of the line up to the chosen "To" date."""
    section_title("Line trend")
    left, right = st.columns([3, 2])
    with left:
        kind = st.segmented_control(
            "Period",
            [item.value for item in KINDS],
            default=PeriodKind.WEEK.value,
            required=True,
            key=page.key("trend_kind"),
        )
    with right:
        figure = st.segmented_control(
            "Line shows", [EFFICIENCY, MO8H], default=EFFICIENCY, required=True, key=page.key("trend_line")
        )
    points = load(PeriodKind(kind))
    span = RANGE_TEXT[PeriodKind(kind)]
    if not points:
        st.info(f"{line} made nothing in the {span}.", icon=":material/info:")
        return
    st.caption(
        f"The {span}. Output columns: blue = %Efficiency on target, orange = below threshold. Hover a chart to read a "
        "point; the exact numbers are in the table."
    )
    _output_chart(page, line, points)
    _figure_chart(page, line, points, figure)
    _number_table(page, line, points)


def _status(point: LineTrendPointDTO) -> str:
    """BR-91 the colour group of a period's Output column."""
    if point.efficiency is None:
        return NO_NUMBER
    return BELOW_THRESHOLD if point.efficiency_below else ON_TARGET


def _output_chart(page: BasePage, line: str, points: list[LineTrendPointDTO]) -> None:
    """BR-91 one column per period, coloured by its %Efficiency. Each colour group is its own column of the rows, in a
    fixed order, so On target is always the first colour (blue) and Below threshold the second (orange)."""
    kept = [point for point in points if point.output is not None]
    groups = [ON_TARGET, BELOW_THRESHOLD] + ([NO_NUMBER] if any(_status(p) == NO_NUMBER for p in kept) else [])
    rows = [
        {CHART_X: point.start, **{group: point.output if _status(point) == group else 0 for group in groups}}
        for point in kept
    ]
    options = {"x": CHART_X, "y": groups, "height": CHART_HEIGHT, "key": page.key(f"trend_output_{line}")}
    if len(rows) < get_settings().chart_max_categories:
        bar_chart(rows, **options)
    else:  # the shared column chart keeps 30 columns and merges the rest: a filled line instead (as Sewing metrics)
        line_chart([{CHART_X: point.start, OUTPUT: point.output} for point in kept], **{**options, "y": OUTPUT})


def _figure_chart(page: BasePage, line: str, points: list[LineTrendPointDTO], figure: str) -> None:
    field, decimals, _suffix, _flag = FIGURES[figure]
    rows = [
        {CHART_X: point.start, figure: round(value, decimals)}
        for point in points
        if (value := getattr(point, field)) is not None
    ]
    line_chart(
        rows,
        x=CHART_X,
        y=figure,
        height=CHART_HEIGHT,
        key=page.key(f"trend_{field}_{line}"),
        empty_message=FILTERED_MO8H if figure == MO8H else "No number to draw.",
    )


def _number_table(page: BasePage, line: str, points: list[LineTrendPointDTO]) -> None:
    """One row per figure, one column per period (the order of the charts); ▼ below threshold (BR-76)."""
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
