"""Report table cells (BR-28, BR-50): right-aligned text that shows "-" and 🔴 and still sorts as a number."""

from collections.abc import Iterable, Mapping, Sequence
from datetime import date
from typing import Any

import streamlit as st

from backend.features.sewing_productivity.dto.overview_dto import OverviewMetricDTO
from frontend.core.formatting import format_number

BELOW_MARK = "🔴"
NOT_AVAILABLE = "-"
PERIOD_LABEL = "Cả kỳ"
TOTAL_LABEL = "Tổng"
METRIC_COLUMN = "Chỉ số"
ROW_HEIGHT = 33  # measured in the browser with the app's theme
TABLE_EXTRA_HEIGHT = 3
LONG_TABLE_HEIGHT = 520
METRIC_COLUMN_WIDTH = 270  # the end of "% so với mục tiêu của hiệu suất A" is what tells two rows apart

# column label, DTO attribute, decimals, suffix, DTO attribute of the "below threshold" flag
ColumnSpec = tuple[str, str, int, str, str | None]


def number_cells(
    values: Sequence[float | int | None],
    decimals: int,
    suffix: str = "",
    flags: Sequence[bool] | None = None,
) -> list[str]:
    """Format a whole column at once: same width (ordinary spaces sort before digits), the mark added after padding."""
    texts = [NOT_AVAILABLE if value is None else f"{format_number(value, decimals)}{suffix}" for value in values]
    width = max((len(text) for text in texts), default=0)
    padded = [text.rjust(width) for text in texts]
    if flags is None:
        return padded
    return [f"{text} {BELOW_MARK}" if below else text for text, below in zip(padded, flags, strict=True)]


def right_text_columns(names: Iterable[str]) -> dict[str, Any]:
    """Column config for the text cells made by `number_cells`."""
    return {name: st.column_config.TextColumn(alignment="right") for name in names}


def spec_columns(rows: Sequence[Any], spec: Sequence[ColumnSpec]) -> dict[str, list[str]]:
    """Report rows -> one list of cells per numeric column of the spec."""
    columns: dict[str, list[str]] = {}
    for label, field, decimals, suffix, flag in spec:
        flags = [getattr(row, flag) for row in rows] if flag else None
        columns[label] = number_cells([getattr(row, field) for row in rows], decimals, suffix, flags)
    return columns


def spec_labels(spec: Sequence[ColumnSpec]) -> list[str]:
    return [label for label, *_ in spec]


def column_rows(columns: Mapping[str, Sequence[Any]]) -> list[dict[str, Any]]:
    """Columns -> table rows, keeping the column order."""
    return [dict(zip(columns, values, strict=True)) for values in zip(*columns.values(), strict=True)]


def day_text(value: date | None, fallback: str = NOT_AVAILABLE) -> str:
    return value.strftime("%d/%m/%Y") if value else fallback


def metric_rows(metrics: Sequence[OverviewMetricDTO], factories: Sequence[str]) -> list[dict[str, str]]:
    """One row per metric, one cell per factory. Each row mixes nothing: its unit comes with the DTO."""
    rows = []
    for metric in metrics:
        cells = {
            factory: number_cells(
                [metric.values.get(factory)], metric.decimals, metric.suffix, [metric.below.get(factory, False)]
            )[0]
            for factory in factories
        }
        rows.append({METRIC_COLUMN: metric.metric, **cells})
    return rows


def metric_columns(factories: Sequence[str]) -> dict[str, Any]:
    return {
        METRIC_COLUMN: st.column_config.TextColumn(pinned=True, width=METRIC_COLUMN_WIDTH),
        **right_text_columns(factories),
    }


def full_table_height(row_count: int) -> int:
    """Height that shows every row of a fixed table without a scroll bar."""
    return (row_count + 1) * ROW_HEIGHT + TABLE_EXTRA_HEIGHT


def long_table_height(row_count: int) -> int:
    """A long table scrolls inside a fixed height; a short one does not show empty rows."""
    return min(full_table_height(row_count), LONG_TABLE_HEIGHT)
