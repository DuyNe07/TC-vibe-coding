"""Standard read-only table with an empty state."""

from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd
import streamlit as st

from frontend.core.components.panel import empty_state


def data_table(
    rows: Sequence[Mapping[str, Any]] | pd.DataFrame,
    *,
    column_config: Mapping[str, Any] | None = None,
    height: int | str = "auto",
    empty_message: str = "Không có dữ liệu.",
    key: str | None = None,
) -> None:
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(list(rows))
    if frame.empty:
        empty_state(empty_message)
        return
    st.dataframe(frame, hide_index=True, column_config=column_config, height=height, key=key)
