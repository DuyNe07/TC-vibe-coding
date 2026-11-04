"""Excel-like tables: read-only (optionally with row selection) and editable."""

import math
from collections.abc import Mapping, Sequence
from typing import Any, Literal

import pandas as pd
import streamlit as st

from backend.core.config import get_settings
from frontend.core.components.panel import empty_state
from frontend.core.formatting import format_number

Rows = Sequence[Mapping[str, Any]] | pd.DataFrame
LAZY_ROWS = 1000  # bigger tables send only the rows on screen to the browser (fast reruns)


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


def _capped(frame: pd.DataFrame, limit: int) -> pd.DataFrame:
    """The first ``limit`` rows, with a Vietnamese note when rows were cut (filter or export to see the rest)."""
    if len(frame) <= limit:
        return frame
    st.caption(
        f"Đang hiện {format_number(limit)}/{format_number(len(frame))} dòng đầu tiên. Hãy lọc bớt, hoặc xuất Excel để xem đủ."
    )
    return frame.head(limit)


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
    settings = get_settings()
    # selection tables cannot be lazy: every row goes to the browser, so their cap is much lower
    frame = _capped(frame, settings.table_max_rows if selection is None else settings.select_max_rows)
    options: dict[str, Any] = {
        "lazy": selection is None and len(frame) > LAZY_ROWS,  # Streamlit 1.64: lazy cannot be combined with on_select
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
    limit = get_settings().edit_max_rows
    if len(frame) > limit:  # never return [] or a cut list: a "save" would then delete the rows not shown
        st.warning(
            f"Bảng có {format_number(len(frame))} dòng, quá nhiều để sửa trực tiếp (tối đa {format_number(limit)}). "
            "Hãy lọc bớt rồi sửa; bảng dưới đây chỉ để xem.",
            icon=":material/warning:",
        )
        data_table(frame, column_config=column_config, column_order=column_order, height=height, key=f"{key}.view")
        return frame_to_records(frame)
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
