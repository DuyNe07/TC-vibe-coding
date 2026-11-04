"""Charts for every feature: one call per chart, rows in, a themed Plotly chart out.

    bar_chart(rows, x="Tháng", y="Doanh thu", key=self.key("sales"))                  # one series
    bar_chart(rows, x="Tháng", y="Doanh thu", color="Xưởng", key=self.key("by_mill"))  # one bar colour per mill
    line_chart(rows, x="Ngày", y=["Nhập", "Xuất"], key=self.key("trend"))            # several numeric columns
    pie_chart(rows, names="Trạng thái", values="Số lượng", key=self.key("status"))

Volume guards (big data never freezes the browser): bars / pie are summed per category, the biggest
``APP_CHART_MAX_CATEGORIES`` categories are kept and the rest become "Khác"; lines keep at most
``APP_CHART_MAX_POINTS`` points per series (evenly thinned, first and last kept); at most ``len(SERIES_COLORS)``
series (the others are summed into "Khác" for bars, dropped for lines) - a caption says what was trimmed.

Look: colours in a fixed order (``SERIES_COLORS``, checked for colour-blind separation; a series keeps its colour
when filters change), one y-axis only, legend only with 2+ series, Vietnamese number format, hover tooltips.
The preparation functions (``prepare_*``) are pure pandas: tested in tests/core, reusable by a chart designer.
"""

from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from backend.core.config import get_settings
from frontend.core.components.panel import empty_state
from frontend.core.formatting import format_number

Rows = Sequence[Mapping[str, Any]] | pd.DataFrame
OTHER = "Khác"
SERIES = "Chuỗi"  # column holding the series name in long form
VALUE = "Giá trị"
# Fixed categorical order from the brand (navy, orange, sky, purple, green, magenta). Validated with the dataviz
# palette checker (lightness band, chroma, adjacent CVD separation). Orange is below 3:1 contrast: hover + legend.
SERIES_COLORS = ("#2E5AAC", "#E8850F", "#1E9BD7", "#8A5CC2", "#169C4B", "#C2408C")
OTHER_COLOR = "#9AA3B2"
WEBGL_POINTS = 1_000  # more points than this: drawn with WebGL (fast in the browser)


# ---- pure preparation (no Streamlit) ----
def to_long(rows: Rows, x: str, y: str | Sequence[str], color: str | None = None) -> pd.DataFrame:
    """Rows -> long frame ``[x, SERIES, VALUE]``. ``y`` = one column (series from ``color``) or several columns."""
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(list(rows))
    ys = [y] if isinstance(y, str) else list(y)
    missing = [c for c in (x, *ys, *([color] if color else [])) if c not in frame.columns]
    if frame.empty or missing:
        if missing and not frame.empty:
            raise ValueError(f"chart: unknown columns {missing}; available: {list(frame.columns)}")
        return pd.DataFrame(columns=[x, SERIES, VALUE])
    if len(ys) == 1:
        series = frame[color].astype(str) if color else ys[0]
        long = pd.DataFrame({x: frame[x], SERIES: series, VALUE: frame[ys[0]]})
    else:
        long = frame.melt(id_vars=[x], value_vars=ys, var_name=SERIES, value_name=VALUE)
    long[VALUE] = pd.to_numeric(long[VALUE], errors="coerce").fillna(0)
    return long


def _top_series(long: pd.DataFrame, limit: int) -> list[str]:
    totals = long.groupby(SERIES, sort=False)[VALUE].apply(lambda v: v.abs().sum())
    return list(totals.sort_values(ascending=False, kind="stable").index[:limit])


def prepare_bars(long: pd.DataFrame, x: str, max_categories: int | None = None) -> tuple[pd.DataFrame, str]:
    """Sum per (category, series); keep the biggest categories and series, the rest -> "Khác". Returns (frame, note)."""
    limit = max_categories or get_settings().chart_max_categories
    notes = []
    keep_series = _top_series(long, len(SERIES_COLORS) - 1)
    if long[SERIES].nunique() > len(SERIES_COLORS):
        long = long.assign(**{SERIES: long[SERIES].where(long[SERIES].isin(keep_series), OTHER)})
        notes.append(f"{len(keep_series)} nhóm lớn nhất, còn lại gộp vào “{OTHER}”")
    totals = long.groupby(x, sort=False)[VALUE].apply(lambda v: v.abs().sum())
    if len(totals) > limit:
        keep = set(totals.sort_values(ascending=False, kind="stable").index[: limit - 1])
        long = long.assign(**{x: long[x].where(long[x].isin(keep), OTHER)})
        notes.append(f"{limit - 1}/{len(totals)} mục lớn nhất, còn lại gộp vào “{OTHER}”")
    summed = long.groupby([x, SERIES], sort=False, as_index=False)[VALUE].sum()
    return summed, "; ".join(notes)


def prepare_lines(long: pd.DataFrame, x: str, max_points: int | None = None) -> tuple[pd.DataFrame, str]:
    """Sort by x, keep the biggest series, thin each series to ``max_points`` (first and last kept)."""
    limit = max_points or get_settings().chart_max_points
    notes = []
    if long[SERIES].nunique() > len(SERIES_COLORS):
        keep = _top_series(long, len(SERIES_COLORS))
        notes.append(f"{len(keep)}/{long[SERIES].nunique()} đường lớn nhất")
        long = long[long[SERIES].isin(keep)]
    long = long.groupby([x, SERIES], sort=False, as_index=False)[VALUE].sum().sort_values(x, kind="stable")
    parts = []
    for _, part in long.groupby(SERIES, sort=False):
        if len(part) > limit:
            step = -(-len(part) // limit)  # ceil: at most `limit` points
            part = pd.concat([part.iloc[::step], part.iloc[[-1]]]).drop_duplicates()
            notes.append(f"rút gọn còn khoảng {format_number(limit)} điểm mỗi đường")
        parts.append(part)
    return (pd.concat(parts) if parts else long), "; ".join(dict.fromkeys(notes))


def color_map(series: Sequence[str]) -> dict[str, str]:
    """Series -> colour in the fixed order of first appearance; "Khác" is always grey."""
    names = [s for s in dict.fromkeys(series) if s != OTHER]
    mapping = {name: SERIES_COLORS[i % len(SERIES_COLORS)] for i, name in enumerate(names)}
    return {**mapping, OTHER: OTHER_COLOR}


# ---- rendering ----
def _show(figure: go.Figure, *, key: str, note: str, height: int, series_count: int) -> None:
    figure.update_layout(
        height=height,
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        separators=",.",  # Vietnamese: 1.234.567,5
        showlegend=series_count > 1,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0, "title": None},
        hoverlabel={"namelength": -1},
        barcornerradius=4,
        bargap=0.25,
        xaxis_title=None,
    )
    st.plotly_chart(
        figure,
        key=key,
        config={"displaylogo": False, "modeBarButtonsToRemove": ["select2d", "lasso2d"]},
    )
    if note:
        st.caption(f"Biểu đồ hiển thị {note}.")


def bar_chart(
    rows: Rows,
    *,
    x: str,
    y: str | Sequence[str],
    key: str,
    color: str | None = None,
    horizontal: bool = False,
    stacked: bool = True,
    height: int = 360,
    empty_message: str = "Chưa có dữ liệu để vẽ biểu đồ.",
) -> None:
    """Bars summed per ``x`` (category). Several series: ``color=<column>`` or ``y=[col1, col2]``."""
    long = to_long(rows, x, y, color)
    if long.empty:
        empty_state(empty_message)
        return
    data, note = prepare_bars(long, x)
    series = list(dict.fromkeys(data[SERIES]))
    axes = {"x": VALUE, "y": x} if horizontal else {"x": x, "y": VALUE}
    figure = px.bar(
        data, **axes, color=SERIES, color_discrete_map=color_map(series),
        barmode="relative" if stacked else "group", orientation="h" if horizontal else "v",
        labels={VALUE: y if isinstance(y, str) else "", SERIES: ""},
    )  # fmt: skip
    figure.update_traces(marker_line_width=0)
    _show(figure, key=key, note=note, height=height, series_count=len(series))


def line_chart(
    rows: Rows,
    *,
    x: str,
    y: str | Sequence[str],
    key: str,
    color: str | None = None,
    area: bool = False,
    height: int = 360,
    empty_message: str = "Chưa có dữ liệu để vẽ biểu đồ.",
) -> None:
    """Change over ``x`` (dates, months, numbers). ``area=True`` fills under the lines (stacked)."""
    long = to_long(rows, x, y, color)
    if long.empty:
        empty_state(empty_message)
        return
    data, note = prepare_lines(long, x)
    series = list(dict.fromkeys(data[SERIES]))
    options: dict[str, Any] = {
        "x": x, "y": VALUE, "color": SERIES, "color_discrete_map": color_map(series),
        "labels": {VALUE: y if isinstance(y, str) else "", SERIES: ""},
    }  # fmt: skip
    if area:
        figure = px.area(data, **options)
    else:
        figure = px.line(data, **options, render_mode="webgl" if len(data) > WEBGL_POINTS else "auto")
    figure.update_traces(line_width=2)
    figure.update_layout(hovermode="x unified")
    _show(figure, key=key, note=note, height=height, series_count=len(series))


def pie_chart(
    rows: Rows,
    *,
    names: str,
    values: str,
    key: str,
    height: int = 300,
    empty_message: str = "Chưa có dữ liệu để vẽ biểu đồ.",
) -> None:
    """Share of a whole (donut). At most ``len(SERIES_COLORS)`` slices: the smallest are grouped as "Khác"."""
    long = to_long(rows, names, values)
    if long.empty or not long[VALUE].any():
        empty_state(empty_message)
        return
    data, note = prepare_bars(long, names, max_categories=len(SERIES_COLORS))
    data = data.groupby(names, sort=False, as_index=False)[VALUE].sum()
    figure = px.pie(
        data, names=names, values=VALUE, hole=0.55, color=names,
        color_discrete_map=color_map(list(data[names].astype(str))),
    )  # fmt: skip
    figure.update_traces(sort=False, marker_line_width=2, marker_line_color="#FFFFFF")
    _show(figure, key=key, note=note, height=height, series_count=len(data))
