"""Report table cells (BR-28, BR-50, BR-53): right-aligned text that shows "-", 🔴 and bold, and still sorts as a number."""

from collections.abc import Iterable, Mapping, Sequence
from datetime import date
from typing import Any

import streamlit as st

from backend.features.sewing_productivity.dto.display_names import (
    EFFICIENCY_NO_RATIO,
    EFFICIENCY_SUM,
    EFFICIENCY_SYSTEM,
    HCM_COLUMN,
    english_name,
)
from backend.features.sewing_productivity.dto.overview_dto import OverviewMetricDTO
from frontend.core.formatting import format_number

BELOW_MARK = "🔴"
NOT_AVAILABLE = "-"
PERIOD_LABEL = "Whole period"
TOTAL_LABEL = "Total"
METRIC_COLUMN = "Metric"
BOLD_LABELS = frozenset({EFFICIENCY_SYSTEM, EFFICIENCY_SUM, EFFICIENCY_NO_RATIO, "MO 8h"})  # BR-53
# The shared table draws plain text only (Markdown cells show their asterisks), so BR-53 uses the bold letters of
# Unicode. They keep their order, so a padded column still sorts as numbers.
BOLD_LETTERS = str.maketrans(
    {
        **{chr(ord("0") + index): chr(0x1D7EC + index) for index in range(10)},
        **{chr(ord("A") + index): chr(0x1D5D4 + index) for index in range(26)},
        **{chr(ord("a") + index): chr(0x1D5EE + index) for index in range(26)},
    }
)
ROW_HEIGHT = 33  # measured in the browser with the app's theme
TABLE_EXTRA_HEIGHT = 3
LONG_TABLE_HEIGHT = 520
METRIC_COLUMN_WIDTH = 320  # the end of "%Efficiency (with ratio - system) vs target" tells two rows apart

# column label, DTO attribute, decimals, suffix, DTO attribute of the "below threshold" flag
ColumnSpec = tuple[str, str, int, str, str | None]


def bold_text(text: str) -> str:
    return text.translate(BOLD_LETTERS)


def number_cells(
    values: Sequence[float | int | None],
    decimals: int,
    suffix: str = "",
    flags: Sequence[bool] | None = None,
    bold: bool = False,
) -> list[str]:
    """Format a whole column at once: same width (padding sorts before digits), the mark added after padding."""
    texts = [NOT_AVAILABLE if value is None else f"{format_number(value, decimals)}{suffix}" for value in values]
    width = max((len(text) for text in texts), default=0)
    padded = [bold_text(text.rjust(width)) if bold else text.rjust(width) for text in texts]
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
        columns[label] = number_cells(
            [getattr(row, field) for row in rows], decimals, suffix, flags, bold=label in BOLD_LABELS
        )
    return columns


def spec_labels(spec: Sequence[ColumnSpec]) -> list[str]:
    return [label for label, *_ in spec]


def column_rows(columns: Mapping[str, Sequence[Any]]) -> list[dict[str, Any]]:
    """Columns -> table rows, keeping the column order."""
    return [dict(zip(columns, values, strict=True)) for values in zip(*columns.values(), strict=True)]


def day_text(value: date | None, fallback: str = NOT_AVAILABLE) -> str:
    return value.strftime("%d/%m/%Y") if value else fallback


def metric_table_columns(metrics: Sequence[OverviewMetricDTO], factories: Sequence[str]) -> list[str]:
    """The factories in their fixed order, then HCM when the backend calculated it (BR-51)."""
    has_hcm = any(HCM_COLUMN in metric.values for metric in metrics)
    return [*factories, HCM_COLUMN] if has_hcm else list(factories)


def metric_rows(metrics: Sequence[OverviewMetricDTO], columns: Sequence[str]) -> list[dict[str, str]]:
    """One row per metric, one cell per column. Each row mixes nothing: its unit comes with the DTO."""
    rows = []
    for metric in metrics:
        label = english_name(metric.metric)
        bold = label in BOLD_LABELS
        cells = {
            english_name(column): number_cells(
                [metric.values.get(column)],
                metric.decimals,
                metric.suffix,
                [metric.below.get(column, False)],
                bold=bold,
            )[0]
            for column in columns
        }
        rows.append({METRIC_COLUMN: bold_text(label) if bold else label, **cells})
    return rows


def metric_columns(columns: Sequence[str]) -> dict[str, Any]:
    return {
        METRIC_COLUMN: st.column_config.TextColumn(pinned=True, width=METRIC_COLUMN_WIDTH),
        **right_text_columns(english_name(column) for column in columns),
    }


def full_table_height(row_count: int) -> int:
    """Height that shows every row of a fixed table without a scroll bar."""
    return (row_count + 1) * ROW_HEIGHT + TABLE_EXTRA_HEIGHT


def long_table_height(row_count: int) -> int:
    """A long table scrolls inside a fixed height; a short one does not show empty rows."""
    return min(full_table_height(row_count), LONG_TABLE_HEIGHT)
