"""Read-only table with row selection that works for large tables.

The shared ``data_table`` turns on ``lazy`` above 1 000 rows, and Streamlit 1.64 refuses ``lazy=True`` together with
row selection (StreamlitIncompatibleParametersError). The price list (4 000+ rows) needs selection, so tables with a
selection are drawn here without ``lazy``; tables without selection keep using ``data_table`` (lazy, fast).
"""

from collections.abc import Mapping, Sequence
from typing import Any, Literal

import pandas as pd
import streamlit as st

from frontend.core.components import data_table, empty_state, frame_to_records


def pick_table(
    rows: Sequence[Mapping[str, Any]] | pd.DataFrame,
    *,
    column_config: Mapping[str, Any] | None = None,
    column_order: Sequence[str] | None = None,
    height: int | str = "auto",
    empty_message: str = "Không có dữ liệu.",
    selection: Literal["single", "multi"] | None = None,
    key: str | None = None,
) -> list[dict[str, Any]]:
    """Same contract as ``data_table``; with ``selection`` the table is never lazy (all rows sent once)."""
    if selection is None:
        return data_table(
            rows,
            column_config=column_config,
            column_order=column_order,
            height=height,
            empty_message=empty_message,
            key=key,
        )
    if key is None:
        raise ValueError("pick_table(selection=...) requires a key")
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(list(rows))
    if frame.empty:
        empty_state(empty_message)
        return []
    event = st.dataframe(
        frame,
        on_select="rerun",
        selection_mode=f"{selection}-row",
        hide_index=True,
        column_config=column_config,
        column_order=column_order,
        height=height,
        key=key,
    )
    selected = [index for index in event.selection.rows if 0 <= index < len(frame)]
    return frame_to_records(frame.iloc[selected])
