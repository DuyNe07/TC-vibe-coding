"""Excel-like tables: read-only (optionally with row selection) and editable."""

import math
from collections.abc import Mapping, Sequence
from typing import Any, Literal

import pandas as pd
import streamlit as st

from frontend.core.components.panel import empty_state

Rows = Sequence[Mapping[str, Any]] | pd.DataFrame


def _to_frame(rows: Rows, columns: Sequence[str] | None = None) -> pd.DataFrame:
    if isinstance(rows, pd.DataFrame):
        return rows
    return pd.DataFrame(list(rows), columns=list(columns) if columns else None)


def _clean_value(value: Any) -> Any:
    """Cell value -> plain Python: NaN/NaT -> None, numpy scalars -> int/float, Timestamp -> datetime."""
    if value is None or value is pd.NaT:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            value = value.item()
        except (TypeError, ValueError):
            return value
        return None if isinstance(value, float) and math.isnan(value) else value
    return value


def frame_to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """DataFrame -> list of dicts ready for DTOs (empty cells become None, never NaN)."""
    return [{str(k): _clean_value(v) for k, v in record.items()} for record in frame.to_dict("records")]


def data_table(
    rows: Rows,
    *,
    column_config: Mapping[str, Any] | None = None,
    column_order: Sequence[str] | None = None,
    height: int | str = "auto",
    empty_message: str = "Không có dữ liệu.",
    selection: Literal["single", "multi"] | None = None,
    key: str | None = None,
) -> list[dict[str, Any]]:
    """Read-only table (sort, search, fullscreen, download CSV built in).

    With ``selection="single" | "multi"`` the user can tick rows; the selected rows are returned
    (``[]`` when nothing is selected or without selection). A ``key`` is required with ``selection``.
    """
    frame = _to_frame(rows)
    if frame.empty:
        empty_state(empty_message)
        return []
    options: dict[str, Any] = {
        "hide_index": True,
        "column_config": column_config,
        "column_order": column_order,
        "height": height,
        "key": key,
    }
    if selection is None:
        st.dataframe(frame, **options)
        return []
    if key is None:
        raise ValueError("data_table(selection=...) requires a key")
    event = st.dataframe(frame, on_select="rerun", selection_mode=f"{selection}-row", **options)
    selected = [index for index in event.selection.rows if 0 <= index < len(frame)]
    return frame_to_records(frame.iloc[selected])


def editable_table(
    rows: Rows,
    *,
    key: str,
    columns: Sequence[str] | None = None,
    column_config: Mapping[str, Any] | None = None,
    column_order: Sequence[str] | None = None,
    disabled: Sequence[str] = (),
    allow_add_delete: bool = False,
    height: int | str = "auto",
) -> list[dict[str, Any]]:
    """Editable grid like an Excel sheet. Returns the edited rows as dicts (empty cells = None).

    Pass ``columns`` so an empty table still shows its headers. Validation stays in the backend: send the
    returned rows to a use case when the user clicks a button, e.g. ``feature.save_rows(SaveRowsRequest(rows=...))``.
    """
    frame = _to_frame(rows, columns)
    edited = st.data_editor(
        frame,
        key=key,
        hide_index=True,
        column_config=column_config,
        column_order=column_order,
        disabled=list(disabled),
        num_rows="dynamic" if allow_add_delete else "fixed",
        height=height,
    )
    return frame_to_records(edited)
