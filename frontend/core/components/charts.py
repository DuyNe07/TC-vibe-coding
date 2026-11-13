"""Charts for every feature: one call per chart, rows in, a themed Plotly chart out.

    bar_chart(rows, x="Tháng", y="Doanh thu", key=self.key("sales"), labels=True)     # numbers printed on the bars
    bar_chart(rows, x="Tháng", y="Doanh thu", color="Xưởng", key=self.key("by_mill"))  # one bar colour per mill
    line_chart(rows, x="Ngày", y=["Nhập", "Xuất"], key=self.key("trend"))            # several numeric columns
    pie_chart(rows, names="Trạng thái", values="Số lượng", key=self.key("status"))
    combo_chart(rows, x="Tháng", bars="Doanh thu", lines="Tỷ lệ (%)", secondary_y=True, key=self.key("combo"))
    scatter_chart(rows, x="Giá", y="Số lượng", color="Nhóm", size="Doanh thu", key=self.key("scatter"))
    histogram_chart(rows, x="Thời gian (phút)", bins=20, key=self.key("hist"))
    box_chart(rows, x="Xưởng", y="Năng suất", violin=True, key=self.key("box"))
    heatmap_chart(rows, x="Tuần", y="Xưởng", values="Sản lượng", labels=True, key=self.key("heat"))
    waterfall_chart(rows, x="Khoản mục", y="Số tiền", key=self.key("waterfall"))
    funnel_chart(rows, stage="Bước", values="Số đơn", key=self.key("funnel"))
    treemap_chart(rows, path=["Ngành", "Nhóm"], values="Doanh thu", sunburst=False, key=self.key("tree"))
    pyplot_chart(rows, lambda data, ax: sns.violinplot(data=data, x="Xưởng", y="Năng suất", ax=ax))  # seaborn

Volume guards (big data never freezes the browser): bars / pie / waterfall / funnel are summed per category, the
biggest ``APP_CHART_MAX_CATEGORIES`` are kept and the rest become "Khác" (heatmap: per axis); lines / combo keep at
most ``APP_CHART_MAX_POINTS`` points per series (evenly thinned, first and last kept); scatter / box / pyplot use a
random sample of ``APP_CHART_MAX_POINTS`` rows; histograms are binned here (only the bins reach the browser); at most
``len(SERIES_COLORS)`` series. ``labels=True`` prints the values on the marks, hidden past ``LABEL_MAX_MARKS``.
A caption says what was trimmed.

Look: colours in a fixed order (``SERIES_COLORS``, checked for colour-blind separation; a series keeps its colour
when filters change), legend only with 2+ series, Vietnamese number format, hover tooltips. A second y-axis only in
``combo_chart(secondary_y=True)``. The preparation functions (``prepare_*``, ``keep_top``, ``sample_rows``) are pure
pandas: tested in tests/core, reusable by a chart designer.
"""

from collections.abc import Callable, Mapping, Sequence
from typing import Any

import numpy as np
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
BIN = "Khoảng"  # histogram bin label
# Fixed categorical order from the brand (navy, orange, sky, purple, green, magenta). Validated with the dataviz
# palette checker (lightness band, chroma, adjacent CVD separation). Orange is below 3:1 contrast: hover + legend.
SERIES_COLORS = ("#2E5AAC", "#E8850F", "#1E9BD7", "#8A5CC2", "#169C4B", "#C2408C")
OTHER_COLOR = "#9AA3B2"
WEBGL_POINTS = 1_000  # more points than this: drawn with WebGL (fast in the browser)
LABEL_MAX_MARKS = 60  # labels=True: more bars / points than this and the numbers would overlap -> hidden
NUMBER = ",.2~f"  # d3 format of printed values; layout separators make it Vietnamese (1.234.567,5)
EMPTY = "Chưa có dữ liệu để vẽ biểu đồ."


# ---- pure preparation (no Streamlit) ----
def _frame(rows: Rows, columns: Sequence[str | None]) -> pd.DataFrame:
    """Rows -> DataFrame; an unknown column is a programming error (raised) unless there is no data at all."""
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(list(rows))
    missing = [c for c in dict.fromkeys(columns) if c and c not in frame.columns]
    if missing and not frame.empty:
        raise ValueError(f"chart: unknown columns {missing}; available: {list(frame.columns)}")
    return frame if not missing else frame.iloc[0:0]


def _as_list(columns: str | Sequence[str]) -> list[str]:
    return [columns] if isinstance(columns, str) else list(columns)


def _join(*notes: str) -> str:
    return "; ".join(dict.fromkeys(n for n in notes if n))


def to_long(rows: Rows, x: str, y: str | Sequence[str], color: str | None = None) -> pd.DataFrame:
    """Rows -> long frame ``[x, SERIES, VALUE]``. ``y`` = one column (series from ``color``) or several columns."""
    ys = _as_list(y)
    frame = _frame(rows, [x, *ys, color])
    if frame.empty:
        return pd.DataFrame(columns=[x, SERIES, VALUE])
    if len(ys) == 1:
        series = frame[color].astype(str) if color else ys[0]
        long = pd.DataFrame({x: frame[x], SERIES: series, VALUE: frame[ys[0]]})
    else:
        long = frame.melt(id_vars=[x], value_vars=ys, var_name=SERIES, value_name=VALUE)
    long[VALUE] = pd.to_numeric(long[VALUE], errors="coerce").fillna(0)
    return long


def keep_top(frame: pd.DataFrame, column: str, weights: pd.Series, limit: int) -> tuple[pd.DataFrame, str]:
    """More than ``limit`` values in ``column``: keep the ``limit - 1`` heaviest, the rest become "Khác"."""
    totals = weights.groupby(frame[column], sort=False).sum()
    if len(totals) <= limit:
        return frame, ""
    keep = set(totals.sort_values(ascending=False, kind="stable").index[: limit - 1])
    frame = frame.assign(**{column: frame[column].where(frame[column].isin(keep), OTHER)})
    return frame, f"{limit - 1}/{len(totals)} mục lớn nhất, còn lại gộp vào “{OTHER}”"


def sample_rows(frame: pd.DataFrame, limit: int | None = None) -> tuple[pd.DataFrame, str]:
    """At most ``limit`` rows (a fixed random sample, original order kept): points / boxes / pyplot charts."""
    limit = limit or get_settings().chart_max_points
    if len(frame) <= limit:
        return frame, ""
    note = f"mẫu ngẫu nhiên {format_number(limit)}/{format_number(len(frame))} dòng"
    return frame.sample(limit, random_state=0).sort_index(), note


def sortable(values: pd.Series) -> bool:
    """Dates / numbers are drawn in order; text labels ("T1".."T12", names) keep the order of the rows."""
    return not (pd.api.types.is_string_dtype(values) or pd.api.types.is_object_dtype(values))


def _top_series(long: pd.DataFrame, limit: int) -> list[str]:
    totals = long.groupby(SERIES, sort=False)[VALUE].apply(lambda v: v.abs().sum())
    return list(totals.sort_values(ascending=False, kind="stable").index[:limit])


def prepare_bars(long: pd.DataFrame, x: str, max_categories: int | None = None) -> tuple[pd.DataFrame, str]:
    """Sum per (category, series); keep the biggest categories and series, the rest -> "Khác". Returns (frame, note)."""
    series_note = ""
    if long[SERIES].nunique() > len(SERIES_COLORS):
        keep_series = _top_series(long, len(SERIES_COLORS) - 1)
        long = long.assign(**{SERIES: long[SERIES].where(long[SERIES].isin(keep_series), OTHER)})
        series_note = f"{len(keep_series)} nhóm lớn nhất, còn lại gộp vào “{OTHER}”"
    long, category_note = keep_top(long, x, long[VALUE].abs(), max_categories or get_settings().chart_max_categories)
    summed = long.groupby([x, SERIES], sort=False, as_index=False)[VALUE].sum()
    return summed, _join(series_note, category_note)


def prepare_lines(long: pd.DataFrame, x: str, max_points: int | None = None) -> tuple[pd.DataFrame, str]:
    """Sort by x (dates / numbers only), keep the biggest series, thin each series to ``max_points`` (first and last kept)."""
    limit = max_points or get_settings().chart_max_points
    notes = []
    if long[SERIES].nunique() > len(SERIES_COLORS):
        keep = _top_series(long, len(SERIES_COLORS))
        notes.append(f"{len(keep)}/{long[SERIES].nunique()} đường lớn nhất")
        long = long[long[SERIES].isin(keep)]
    long = long.groupby([x, SERIES], sort=False, as_index=False)[VALUE].sum()
    if sortable(long[x]):
        long = long.sort_values(x, kind="stable")
    parts = []
    for _, part in long.groupby(SERIES, sort=False):
        if len(part) > limit:
            step = -(-len(part) // limit)  # ceil: at most `limit` points
            part = pd.concat([part.iloc[::step], part.iloc[[-1]]]).drop_duplicates()
            notes.append(f"rút gọn còn khoảng {format_number(limit)} điểm mỗi đường")
        parts.append(part)
    return (pd.concat(parts) if parts else long), _join(*notes)


def prepare_histogram(long: pd.DataFrame, bins: int = 20) -> pd.DataFrame:
    """Values -> counts per bin and series ``[BIN, SERIES, VALUE]`` (same edges for every series, in order)."""
    values = long[VALUE].to_numpy(dtype=float)
    edges = np.histogram_bin_edges(values, bins=max(1, bins))
    names = [f"{format_number(a)} – {format_number(b)}" for a, b in zip(edges[:-1], edges[1:], strict=True)]
    parts = [
        pd.DataFrame({BIN: names, SERIES: name, VALUE: np.histogram(part[VALUE].to_numpy(dtype=float), edges)[0]})
        for name, part in long.groupby(SERIES, sort=False)
    ]
    return pd.concat(parts, ignore_index=True)


def color_map(series: Sequence[str]) -> dict[str, str]:
    """Series -> colour in the fixed order of first appearance; "Khác" is always grey."""
    names = [s for s in dict.fromkeys(series) if s != OTHER]
    mapping = {name: SERIES_COLORS[i % len(SERIES_COLORS)] for i, name in enumerate(names)}
    return {**mapping, OTHER: OTHER_COLOR}


def show_labels(labels: bool, marks: int, limit: int = LABEL_MAX_MARKS) -> tuple[bool, str]:
    """``labels=True`` and few enough marks to read -> (True, ""); too many -> (False, note for the caption)."""
    if not labels or marks <= limit:
        return labels, ""
    return False, f"ẩn số trên biểu đồ vì có hơn {limit} điểm (rê chuột để xem)"


# ---- rendering ----
def _show(figure: go.Figure, *, key: str, note: str, height: int, series_count: int, **layout: Any) -> None:
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
    figure.update_layout(**layout)  # per-chart overrides of the defaults above
    st.plotly_chart(
        figure,
        key=key,
        config={"displaylogo": False, "modeBarButtonsToRemove": ["select2d", "lasso2d"]},
    )
    _caption(note)


def _caption(note: str) -> None:
    if note:
        st.caption(f"Biểu đồ hiển thị {note}.")


def _bar_text(stacked: bool, upright: bool) -> dict[str, Any]:
    """Printed values keep a readable size (never squeezed to the bar width); many bars -> written upwards."""
    return {
        "textposition": "inside" if stacked else "outside", "cliponaxis": False, "constraintext": "none",
        "textfont_size": 11, "textangle": -90 if upright else 0,
    }  # fmt: skip


def headroom(values: pd.Series) -> list[float]:
    """Axis range with 20 % free above (below for negatives): values printed outside the bars are never cut."""
    low, high = min(float(values.min()), 0.0), max(float(values.max()), 0.0)
    pad = (high - low) * 0.2 or 1.0
    return [low - pad if low < 0 else 0.0, high + pad]


def _point_labels(figure: go.Figure) -> None:
    """Lines / areas: the value above every point."""
    figure.update_traces(mode="lines+markers+text", textposition="top center", texttemplate=f"%{{text:{NUMBER}}}")


def bar_chart(
    rows: Rows,
    *,
    x: str,
    y: str | Sequence[str],
    key: str,
    color: str | None = None,
    horizontal: bool = False,
    stacked: bool = True,
    labels: bool = False,
    height: int = 360,
    empty_message: str = EMPTY,
) -> None:
    """Bars summed per ``x`` (category). Several series: ``color=<column>`` or ``y=[col1, col2]``."""
    long = to_long(rows, x, y, color)
    if long.empty:
        empty_state(empty_message)
        return
    data, note = prepare_bars(long, x)
    show, label_note = show_labels(labels, len(data))
    series = list(dict.fromkeys(data[SERIES]))
    axes = {"x": VALUE, "y": x} if horizontal else {"x": x, "y": VALUE}
    figure = px.bar(
        data, **axes, color=SERIES, color_discrete_map=color_map(series),
        barmode="relative" if stacked else "group", orientation="h" if horizontal else "v",
        labels={VALUE: y if isinstance(y, str) else "", SERIES: ""}, text_auto=NUMBER if show else False,
    )  # fmt: skip
    figure.update_traces(marker_line_width=0, **_bar_text(stacked, upright=not horizontal and len(data) > 8))
    if show and not stacked:
        figure.update_layout({"xaxis" if horizontal else "yaxis": {"range": headroom(data[VALUE])}})
    _show(figure, key=key, note=_join(note, label_note), height=height, series_count=len(series))


def line_chart(
    rows: Rows,
    *,
    x: str,
    y: str | Sequence[str],
    key: str,
    color: str | None = None,
    area: bool = False,
    labels: bool = False,
    height: int = 360,
    empty_message: str = EMPTY,
) -> None:
    """Change over ``x`` (dates, months, numbers). ``area=True`` fills under the lines (stacked)."""
    long = to_long(rows, x, y, color)
    if long.empty:
        empty_state(empty_message)
        return
    data, note = prepare_lines(long, x)
    show, label_note = show_labels(labels, len(data))
    series = list(dict.fromkeys(data[SERIES]))
    options: dict[str, Any] = {
        "x": x, "y": VALUE, "color": SERIES, "color_discrete_map": color_map(series),
        "labels": {VALUE: y if isinstance(y, str) else "", SERIES: ""}, "text": VALUE if show else None,
    }  # fmt: skip
    if area:
        figure = px.area(data, **options)
    else:
        figure = px.line(data, **options, render_mode="webgl" if len(data) > WEBGL_POINTS else "auto")
    figure.update_traces(line_width=2)
    if show:
        _point_labels(figure)
    figure.update_layout(hovermode="x unified")
    _show(figure, key=key, note=_join(note, label_note), height=height, series_count=len(series))


def pie_chart(
    rows: Rows,
    *,
    names: str,
    values: str,
    key: str,
    labels: bool = False,
    height: int = 300,
    empty_message: str = EMPTY,
) -> None:
    """Share of a whole (donut). At most ``len(SERIES_COLORS)`` slices: the smallest are grouped as "Khác".
    ``labels=True`` prints the value and the share on every slice (default: the share only)."""
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
    if labels:
        figure.update_traces(texttemplate=f"%{{value:{NUMBER}}}<br>%{{percent}}")
    _show(figure, key=key, note=note, height=height, series_count=len(data))


def combo_chart(
    rows: Rows,
    *,
    x: str,
    bars: str | Sequence[str],
    lines: str | Sequence[str],
    key: str,
    secondary_y: bool = False,
    stacked: bool = False,
    labels: bool = False,
    height: int = 380,
    empty_message: str = EMPTY,
) -> None:
    """Bars and lines on the same ``x`` (e.g. revenue as bars, rate as a line). ``secondary_y=True`` puts the lines
    on a second y-axis on the right (two measures of different scale)."""
    bar_columns, line_columns = _as_list(bars), _as_list(lines)
    long = to_long(rows, x, [*bar_columns, *line_columns])
    if long.empty:
        empty_state(empty_message)
        return
    data, note = prepare_lines(long, x)
    show, label_note = show_labels(labels, len(data))
    colors = color_map(list(dict.fromkeys(data[SERIES])))
    text = {"texttemplate": f"%{{y:{NUMBER}}}"} if show else {}
    figure = go.Figure()
    for name, part in data.groupby(SERIES, sort=False):
        common = {"x": part[x], "y": part[VALUE], "name": name, "marker_color": colors[name], **text}
        if name in bar_columns:
            figure.add_bar(**common, marker_line_width=0, **_bar_text(stacked, upright=len(data) > 8))
        else:
            figure.add_scatter(
                **common, mode="lines+markers+text" if show else "lines+markers", line_width=2,
                textposition="top center", yaxis="y2" if secondary_y else "y",
            )  # fmt: skip
    figure.update_layout(barmode="relative" if stacked else "group", hovermode="x unified")
    if show and not stacked:
        left = data[data[SERIES].isin(bar_columns)] if secondary_y else data  # what the left axis shows
        figure.update_layout(yaxis_range=headroom(left[VALUE]))
    if secondary_y:
        figure.update_layout(
            yaxis_title=", ".join(bar_columns),
            yaxis2={"title": ", ".join(line_columns), "overlaying": "y", "side": "right", "showgrid": False},
        )
    _show(figure, key=key, note=_join(note, label_note), height=height, series_count=data[SERIES].nunique())


def scatter_chart(
    rows: Rows,
    *,
    x: str,
    y: str,
    key: str,
    color: str | None = None,
    size: str | None = None,
    height: int = 380,
    empty_message: str = EMPTY,
) -> None:
    """One point per row (relationship between two numbers). ``size=<column>`` = bubble chart."""
    frame = _frame(rows, [x, y, color, size])
    if frame.empty:
        empty_state(empty_message)
        return
    data, note = sample_rows(frame)
    if color:
        data = data.assign(**{color: data[color].astype(str)})
    figure = px.scatter(
        data, x=x, y=y, color=color, size=size, size_max=40,
        color_discrete_map=color_map(list(data[color])) if color else None,
        color_discrete_sequence=SERIES_COLORS, render_mode="webgl" if len(data) > WEBGL_POINTS else "auto",
    )  # fmt: skip
    count = data[color].nunique() if color else 1
    _show(figure, key=key, note=note, height=height, series_count=count, xaxis_title=x, legend_title=None)


def histogram_chart(
    rows: Rows,
    *,
    x: str,
    key: str,
    color: str | None = None,
    bins: int = 20,
    labels: bool = False,
    height: int = 360,
    empty_message: str = EMPTY,
) -> None:
    """How the values of ``x`` are spread: count of rows per range. Binned here, only the bins reach the browser."""
    long = to_long(rows, x, x, color)
    if long.empty:
        empty_state(empty_message)
        return
    data = prepare_histogram(long, bins)
    show, label_note = show_labels(labels, len(data))
    series = list(dict.fromkeys(data[SERIES]))
    figure = px.bar(
        data, x=BIN, y=VALUE, color=SERIES, color_discrete_map=color_map(series), barmode="group",
        labels={VALUE: "Số dòng", SERIES: ""}, text_auto=NUMBER if show else False,
    )  # fmt: skip
    figure.update_traces(marker_line_width=0, **_bar_text(False, upright=len(data) > 8))
    if show:
        figure.update_layout(yaxis_range=headroom(data[VALUE]))
    _show(figure, key=key, note=label_note, height=height, series_count=len(series), bargap=0.05)


def box_chart(
    rows: Rows,
    *,
    y: str,
    key: str,
    x: str | None = None,
    violin: bool = False,
    height: int = 380,
    empty_message: str = EMPTY,
) -> None:
    """Spread of ``y`` (median, quartiles, outliers) per group ``x``. ``violin=True`` also shows the density."""
    frame = _frame(rows, [x, y])
    if frame.empty:
        empty_state(empty_message)
        return
    data, note = sample_rows(frame)
    group_note = ""
    if x:
        data = data.assign(**{x: data[x].astype(str)})
        data, group_note = keep_top(data, x, pd.Series(1, index=data.index), get_settings().chart_max_categories)
    options: dict[str, Any] = {
        "x": x, "y": y, "color": x, "color_discrete_map": color_map(list(data[x])) if x else None,
        "color_discrete_sequence": SERIES_COLORS,
    }  # fmt: skip
    figure = px.violin(data, **options, box=True) if violin else px.box(data, **options, points="outliers")
    _show(figure, key=key, note=_join(note, group_note), height=height, series_count=1)


def heatmap_chart(
    rows: Rows,
    *,
    x: str,
    y: str,
    values: str,
    key: str,
    labels: bool = False,
    height: int = 420,
    empty_message: str = EMPTY,
) -> None:
    """Grid ``x`` × ``y`` coloured by the sum of ``values`` (e.g. week × mill). Darker = bigger."""
    frame = _frame(rows, [x, y, values])
    if frame.empty:
        empty_state(empty_message)
        return
    limit = get_settings().chart_max_categories
    data = frame.assign(**{values: pd.to_numeric(frame[values], errors="coerce").fillna(0)})
    data, x_note = keep_top(data, x, data[values].abs(), limit)
    data, y_note = keep_top(data, y, data[values].abs(), limit)
    grid = data.pivot_table(index=y, columns=x, values=values, aggfunc="sum", fill_value=0, sort=False)
    grid = grid.sort_index(axis=1) if sortable(data[x]) else grid
    grid = grid.sort_index() if sortable(data[y]) else grid
    show, label_note = show_labels(labels, grid.size, limit=LABEL_MAX_MARKS * 4)  # cells are smaller than bars
    figure = px.imshow(
        grid, aspect="auto", color_continuous_scale=["#EEF2FA", SERIES_COLORS[0]],
        text_auto=NUMBER if show else False, labels={"color": values},
    )  # fmt: skip
    figure.update_xaxes(type="category", side="bottom")
    figure.update_yaxes(type="category", title=None)
    _show(figure, key=key, note=_join(x_note, y_note, label_note), height=height, series_count=1)


def waterfall_chart(
    rows: Rows,
    *,
    x: str,
    y: str,
    key: str,
    total: str | None = "Tổng",
    height: int = 380,
    empty_message: str = EMPTY,
) -> None:
    """Steps that add up (rows in order: + increases, - decreases), ending with a ``total`` bar (None = no total)."""
    long = to_long(rows, x, y)
    if long.empty:
        empty_state(empty_message)
        return
    data, note = prepare_bars(long, x)
    steps = list(data[x].astype(str)) + ([total] if total else [])
    amounts = list(data[VALUE]) + ([data[VALUE].sum()] if total else [])  # y of a total bar is ignored
    figure = go.Figure(
        go.Waterfall(
            x=steps, y=amounts, measure=["relative"] * len(data) + (["total"] if total else []),
            text=amounts, texttemplate=f"%{{text:{NUMBER}}}", textposition="outside", cliponaxis=False,
            increasing={"marker": {"color": SERIES_COLORS[4]}}, decreasing={"marker": {"color": SERIES_COLORS[1]}},
            totals={"marker": {"color": SERIES_COLORS[0]}}, connector={"line": {"color": OTHER_COLOR, "width": 1}},
        )
    )  # fmt: skip
    _show(figure, key=key, note=note, height=height, series_count=1)


def funnel_chart(
    rows: Rows,
    *,
    stage: str,
    values: str,
    key: str,
    height: int = 360,
    empty_message: str = EMPTY,
) -> None:
    """Steps of a process in order (orders -> approved -> delivered), with the % kept from the first step."""
    long = to_long(rows, stage, values)
    if long.empty:
        empty_state(empty_message)
        return
    data, note = prepare_bars(long, stage)
    figure = go.Figure(
        go.Funnel(
            y=data[stage].astype(str), x=data[VALUE], marker={"color": SERIES_COLORS[0]},
            texttemplate=f"%{{x:{NUMBER}}} (%{{percentInitial}})", connector={"fillcolor": "#EEF2FA"},
        )
    )  # fmt: skip
    _show(figure, key=key, note=note, height=height, series_count=1)


def treemap_chart(
    rows: Rows,
    *,
    path: Sequence[str],
    values: str,
    key: str,
    sunburst: bool = False,
    height: int = 420,
    empty_message: str = EMPTY,
) -> None:
    """Parts of a whole by levels (``path=["Ngành", "Nhóm", "Mã"]``): rectangles, or rings with ``sunburst=True``."""
    frame = _frame(rows, [*path, values])
    if frame.empty:
        empty_state(empty_message)
        return
    data = frame.assign(**{values: pd.to_numeric(frame[values], errors="coerce").fillna(0).clip(lower=0)})
    data = data.groupby(list(path), as_index=False, sort=False)[values].sum()
    data = data[data[values] > 0].sort_values(values, ascending=False, kind="stable")
    if data.empty:
        empty_state(empty_message)
        return
    limit = get_settings().chart_max_points
    note = f"{format_number(limit)}/{format_number(len(data))} ô lớn nhất" if len(data) > limit else ""
    data = data.head(limit)
    draw = px.sunburst if sunburst else px.treemap
    figure = draw(
        data, path=list(path), values=values, color=path[0],
        color_discrete_map=color_map(list(data[path[0]].astype(str))),
    )  # fmt: skip
    figure.update_traces(texttemplate=f"%{{label}}<br>%{{value:{NUMBER}}}", sort=False)
    _show(figure, key=key, note=note, height=height, series_count=1)


def pyplot_chart(
    rows: Rows,
    draw: Callable[[pd.DataFrame, Any], Any],
    *,
    width: float = 8.0,
    height: float = 4.0,
    empty_message: str = EMPTY,
) -> None:
    """Any matplotlib / seaborn chart, drawn as a picture: ``draw(data, ax)`` gets the (sampled) rows and an axes.

        pyplot_chart(rows, lambda data, ax: sns.kdeplot(data=data, x="Giá", hue="Nhóm", fill=True, ax=ax))
        pyplot_chart(rows, lambda data, ax: sns.regplot(data=data, x="Giờ", y="Sản lượng", ax=ax))
        pyplot_chart(rows, lambda data, ax: sns.pairplot(data, hue="Nhóm"))   # figure-level: return the grid

    For what Plotly charts above do not cover (density, regression, pair / joint plots...): no hover, no zoom.
    """
    frame = _frame(rows, [])
    if frame.empty:
        empty_state(empty_message)
        return
    data, note = sample_rows(frame)
    # Lazy: matplotlib + seaborn cost ~1 s to import, only pages drawing one pay it.
    import matplotlib.pyplot as plt
    import seaborn as sns
    from matplotlib.figure import Figure

    figure = Figure(figsize=(width, height), layout="constrained")  # not pyplot: no global figure shared by sessions
    # ponytail: style + palette are process-wide rcParams while drawing; per-axes styling if two sessions ever clash
    with sns.axes_style("whitegrid"), sns.color_palette(SERIES_COLORS):
        result = draw(data, figure.subplots())
    grid = result if isinstance(result, sns.axisgrid.Grid) else None  # pairplot / jointplot / clustermap
    st.pyplot(grid.figure if grid else figure)
    if grid:
        plt.close(grid.figure)  # figure-level seaborn plots live in pyplot: free them
    _caption(note)
