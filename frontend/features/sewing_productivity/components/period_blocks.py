"""Screen 4 (Sewing metrics) blocks of one figure (sửa 2026-11-08): a row of cards with the change against the period
before (BR-70, BR-71), one small chart per column with its own scale, the exact numbers in a folded table. Numbers are
written as BR-75 says, the below-threshold mark is BR-76."""

from collections.abc import Callable, Sequence

import streamlit as st

from backend.core.config import get_settings
from backend.features.sewing_productivity.dto.display_names import english_name
from backend.features.sewing_productivity.dto.monthly_dto import PeriodMetricDTO
from frontend.core.components import bar_chart, data_table, line_chart
from frontend.features.sewing_productivity.components.number_format import format_number
from frontend.features.sewing_productivity.components.report_cells import (
    BELOW_MARK,
    NOT_AVAILABLE,
    below_note,
    full_table_height,
    number_cells,
    right_text_columns,
)

FACTORY_COLUMN = "Factory"
FACTORY_COLUMN_WIDTH = 120  # "Fac Vinh Long" in full (the automatic width cut it)
CHART_X = "Period start"
CHARTS_PER_ROW = 2  # 3 per row squeezed the date labels into each other on a 1440 px screen (fix log 2026-11-08)
SMALL_CHART_HEIGHT = 230
SHORT_NUMBER_LENGTH = 6  # "55,102", "42.44", "91.4%": six cards still fit on one row
CARDS_PER_LONG_ROW = 3
# figures that add up over a period: drawn as columns (UI concept 2026-11-08); the others as lines
SUM_METRICS = frozenset({"Direct worker", "Sản lượng", "Tiền CM"})
TABLE_LABEL = "Exact numbers by period"

KeyFn = Callable[[str], str]


def _text(value: float | None, metric: PeriodMetricDTO) -> str:
    return NOT_AVAILABLE if value is None else f"{format_number(value, metric.decimals)}{metric.suffix}"


def _change_text(change: float | None, metric: PeriodMetricDTO) -> str | None:
    """BR-71 the signed change as the card shows it; None (no arrow) when missing or zero once rounded."""
    if change is None or round(change, metric.decimals) == 0:
        return None
    sign = "+" if change > 0 else "-"
    return f"{sign}{format_number(abs(change), metric.decimals)}{metric.suffix}"


def _series(metric: PeriodMetricDTO, column: str) -> list[float]:
    return [value for row in metric.rows if (value := row.values.get(column)) is not None]


def period_cards(metric: PeriodMetricDTO, title: str = "") -> None:
    """BR-70, BR-71 one card per column: the last period, its change, a mini chart of every period. `title` names an
    extra row of cards (BR-77 %Direct labor under Direct worker)."""
    last = metric.rows[-1].period
    if title:
        st.markdown(f"**{title}**")
    elif metric.compare_label:
        days = metric.compare_label.removeprefix("vs ")
        st.caption(f"Cards show the last period, {last}. The arrows compare it with {days}.")
    else:
        st.caption(f"Cards show the last period, {last}. There is no earlier period to compare with.")
    chart_type = "bar" if metric.metric in SUM_METRICS else "line"
    texts = [_text(card.value, metric) for card in metric.cards]
    # one row of cards while the numbers fit; longer numbers (Output, Revenue) were cut ("151.2…"): 3 cards per row
    per_row = len(metric.cards) if max(map(len, texts), default=0) <= SHORT_NUMBER_LENGTH else CARDS_PER_LONG_ROW
    slots = [slot for start in range(0, len(metric.cards), per_row) for slot in st.columns(per_row)]
    for slot, card in zip(slots, metric.cards, strict=False):
        delta = _change_text(card.change, metric)
        with slot:
            name = english_name(card.column)
            st.metric(
                f":red[{name} {BELOW_MARK}]" if card.below else name,  # BR-76 red name with ▼
                _text(card.value, metric),
                delta,
                delta_color="normal" if metric.rising_is_good else "off",
                help=f"{last}, change {metric.compare_label}" if delta else None,
                chart_data=_series(metric, card.column),
                chart_type=chart_type,
                border=True,
            )


def small_charts(metric: PeriodMetricDTO, columns: Sequence[str], label: str, key: KeyFn) -> None:
    """One chart per column, each with its own scale, two per row. Sum figures are columns while the periods fit
    the shared chart (more categories than that would be merged into "Khác"): then a filled line instead."""
    as_bars = metric.metric in SUM_METRICS and len(metric.rows) < get_settings().chart_max_categories
    for start in range(0, len(columns), CHARTS_PER_ROW):
        chunk = columns[start : start + CHARTS_PER_ROW]
        for slot, column in zip(st.columns(CHARTS_PER_ROW), chunk, strict=False):
            rows = [
                {CHART_X: row.start, label: round(value, metric.decimals)}
                for row in metric.rows
                if (value := row.values.get(column)) is not None
            ]
            options = {
                "x": CHART_X,
                "y": label,
                "height": SMALL_CHART_HEIGHT,
                "key": key(f"chart_{metric.metric}_{column}"),
            }
            with slot:
                st.markdown(f"**{english_name(column)}**")
                if as_bars:
                    bar_chart(rows, **options)
                else:
                    line_chart(rows, area=metric.metric in SUM_METRICS, **options)
    st.caption("Each point sits at the first day of its period. Each chart has its own scale.")


def number_table(metric: PeriodMetricDTO, columns: Sequence[str], key: KeyFn) -> None:
    """The BR-69 table, folded, full width (sửa 2026-11-08 lần 2): one row per factory, HCM, Total and one column per
    period; the first column stays on screen when scrolling sideways. Below-threshold numbers carry ▼ (BR-76)."""
    with st.expander(TABLE_LABEL, icon=":material/table:"):
        periods = [row.period for row in metric.rows]
        rows = [
            {
                FACTORY_COLUMN: english_name(column),
                **dict(
                    zip(
                        periods,
                        number_cells(
                            [row.values.get(column) for row in metric.rows],
                            metric.decimals,
                            metric.suffix,
                            [row.below.get(column, False) for row in metric.rows],
                        ),
                        strict=True,
                    )
                ),
            }
            for column in columns
        ]
        data_table(
            rows,
            column_config={
                FACTORY_COLUMN: st.column_config.TextColumn(pinned=True, width=FACTORY_COLUMN_WIDTH),
                **right_text_columns(periods),
            },
            height=full_table_height(len(rows)),
            key=key(f"table_{metric.metric}"),
        )
        if any(any(row.below.values()) for row in metric.rows):
            below_note()
