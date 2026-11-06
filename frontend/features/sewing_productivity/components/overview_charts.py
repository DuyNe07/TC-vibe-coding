"""The charts of Screen 1 and the summary above them (BR-54).

Points with "-" never reach a chart: the shared chart component would draw them as 0. That component does not write
numbers on the marks, so the numbers go where it does show text: the legend and the bar names."""

from collections.abc import Callable, Mapping, Sequence
from typing import NamedTuple

import streamlit as st

from backend.features.sewing_productivity.dto.display_names import (
    EFFICIENCY_NO_RATIO,
    EFFICIENCY_SUM,
    EFFICIENCY_SYSTEM,
    HCM_COLUMN,
    TARGET_SYSTEM,
    TOTAL_COLUMN,
    english_name,
)
from backend.features.sewing_productivity.dto.overview_dto import (
    ChartPointDTO,
    ChartsResponse,
    OverviewMetricDTO,
    RankedLineDTO,
    RankingMetric,
)
from frontend.core.components import bar_chart, line_chart, panel
from frontend.core.formatting import format_number
from frontend.features.sewing_productivity.components.report_cells import BELOW_MARK, NOT_AVAILABLE
from frontend.features.sewing_productivity.components.report_filters import DEFAULT_FACTORY, NO_DATA_IN_RANGE

PERCENT_DECIMALS = 1
MONEY_DECIMALS = 2
PERCENT = "%"
BAR_NAME = " "  # the axis title of a horizontal chart: blank, it would cover the long bar names
LEGEND_PADDING = "  "  # the chart legend cuts the last letter of a name: the cut falls on these spaces
RANKING_COLUMNS = {
    RankingMetric.EFFICIENCY_B.value: (EFFICIENCY_SUM, PERCENT_DECIMALS, PERCENT),
    RankingMetric.EFFICIENCY_A.value: (EFFICIENCY_SYSTEM, PERCENT_DECIMALS, PERCENT),
    RankingMetric.NO_RATIO.value: (EFFICIENCY_NO_RATIO, PERCENT_DECIMALS, PERCENT),
    RankingMetric.MO8H.value: ("MO 8h", MONEY_DECIMALS, ""),
}


class Card(NamedTuple):
    """BR-58 one card: backend name of its metric, then how it looks. A colour and a unit tell money from pieces."""

    metric: str
    label: str
    icon: str
    color: str
    prefix: str
    suffix: str
    decimals: int


CARDS = (
    Card("Tiền CM", "Revenue (USD)", ":material/payments:", "green", "$", "", 0),
    Card("Sản lượng", "Output (pcs)", ":material/checkroom:", "blue", "", "", 0),
    Card("Giá CM trung bình", "Avg CM price (USD/pc)", ":material/sell:", "violet", "$", "", MONEY_DECIMALS),
    Card("MO 8h", "MO 8h (USD)", ":material/schedule:", "orange", "$", "", MONEY_DECIMALS),
    Card("Hiệu suất B", EFFICIENCY_SUM, ":material/speed:", "red", "", "%", PERCENT_DECIMALS),
)
CARD_HEIGHT = 270  # every card the same height, room for a total that wraps on a narrow screen
CARD_SITE_NAMES = {DEFAULT_FACTORY: "Vinh Long", HCM_COLUMN: "HCM"}
CARD_SITE_COLORS = {DEFAULT_FACTORY: "blue", HCM_COLUMN: "orange"}
PeriodValues = Mapping[str, Mapping[str, float | None]]


def _value_text(value: float | None, decimals: int, suffix: str) -> str:
    return NOT_AVAILABLE if value is None else f"{format_number(value, decimals)}{suffix}"


def _legend(factory: str, value: float | None, decimals: int, suffix: str) -> str:
    """The name of a line in the legend, with the figure of the whole period."""
    name = english_name(factory)
    figure = "" if value is None else f": {_value_text(value, decimals, suffix)}"
    return f"{name}{figure}{LEGEND_PADDING}"


def _card_value(card: Card, metric: OverviewMetricDTO, column: str, mark: bool = True) -> str:
    value = metric.values.get(column)
    if value is None:
        return NOT_AVAILABLE
    text = f"{card.prefix}{format_number(value, card.decimals)}{card.suffix}"
    return f"{text} {BELOW_MARK}" if mark and metric.below.get(column, False) else text


def _markdown(text: str) -> str:
    """Two "$" in one Markdown text would start a formula."""
    return text.replace("$", "\\$")


def _card(card: Card, metric: OverviewMetricDTO, sites: Sequence[str]) -> None:
    """One card of the same height as the others: what it is (colour, icon, unit), the total, then each site.

    Each site has a bar: the bigger site fills it, the other one shows its size against it."""
    largest = max((metric.values.get(site) or 0 for site in sites), default=0)
    with st.container(border=True, height=CARD_HEIGHT):
        st.markdown(f":{card.color}[{card.icon} **{card.label}**]")  # wraps; a badge would cut a long label
        # a heading, not st.metric: st.metric cuts a long number with "...", a heading wraps it
        st.caption("Total")
        st.markdown(f"### :{card.color}[{_markdown(_card_value(card, metric, TOTAL_COLUMN, mark=False))}]")
        for site in sites:
            value = metric.values.get(site) or 0
            st.progress(
                min(max(value / largest, 0), 1) if largest > 0 else 0,
                text=f":{CARD_SITE_COLORS[site]}[{CARD_SITE_NAMES[site]}] "
                f"**{_markdown(_card_value(card, metric, site))}**",
            )


def group_summary(metrics: Sequence[OverviewMetricDTO], factories: Sequence[str]) -> None:
    """BR-58 five cards: the total of the chosen factories in big type, Vinh Long and HCM under it.

    Markdown cards, not metric tiles: a tile cuts a long number, a card wraps it."""
    by_name = {metric.metric: metric for metric in metrics}
    if not all(TOTAL_COLUMN in by_name[card.metric].values for card in CARDS):
        return
    sites = []
    if DEFAULT_FACTORY in factories:
        sites.append(DEFAULT_FACTORY)
    if any(HCM_COLUMN in metric.values for metric in metrics):
        sites.append(HCM_COLUMN)
    with panel("Vinh Long - HCM", icon="🏭", description="Total = every chosen factory together. Money in USD."):
        for column, card in zip(st.columns(len(CARDS)), CARDS, strict=True):
            with column:
                _card(card, by_name[card.metric], sites)


def _daily_chart(
    title: str,
    points: Sequence[ChartPointDTO],
    label: str,
    period: Mapping[str, float | None],
    decimals: int,
    suffix: str,
    key: str,
    message: str,
) -> None:
    with panel(title):
        if message:
            st.info(message, icon=":material/info:")
            return
        rows = [
            {
                "Date": item.day,
                "Factory": _legend(item.factory, period.get(item.factory), decimals, suffix),
                label: round(item.value, decimals),
            }
            for item in points
        ]
        line_chart(rows, x="Date", y=label, color="Factory", key=key, empty_message=NO_DATA_IN_RANGE)
        st.caption("The figure beside each factory name is its result for the whole period.")


def _output_chart(charts: ChartsResponse, key: str) -> None:
    with panel(f"Output vs {TARGET_SYSTEM} by factory"):
        if charts.not_applicable_message:
            st.info(charts.not_applicable_message, icon=":material/info:")
            return
        rows = []
        items = [*charts.output_vs_target, *([charts.hcm_output] if charts.hcm_output else [])]
        for item in reversed(items):  # a horizontal chart draws its first row at the bottom
            name = f"{english_name(item.factory)}: {_value_text(item.output, 0, '')}"
            if item.target_a is not None:
                name = f"{name} / {_value_text(item.target_a, 0, '')}"
            rows.append({BAR_NAME: name, "Type": f"Output{LEGEND_PADDING}", "Quantity": round(item.output)})
            if item.target_a is not None:
                rows.append(
                    {BAR_NAME: name, "Type": f"Target (system){LEGEND_PADDING}", "Quantity": round(item.target_a)}
                )
        bar_chart(
            rows,
            x=BAR_NAME,
            y="Quantity",
            color="Type",
            horizontal=True,
            stacked=False,
            key=key,
            empty_message=NO_DATA_IN_RANGE,
        )
        st.caption(f"Beside each factory: output / {TARGET_SYSTEM}.")


def daily_charts(charts: ChartsResponse, metrics: Sequence[OverviewMetricDTO], key: Callable[[str], str]) -> None:
    """Two columns: the 3 efficiencies, MO 8h and output against the system target.

    Only the system efficiency, MO 8h and the output chart stop under a customer or product filter."""
    message = charts.not_applicable_message
    period: PeriodValues = {metric.metric: metric.values for metric in metrics}
    left, right = st.columns(2)
    with left:
        _daily_chart(
            f"{EFFICIENCY_SYSTEM} by day",
            [*charts.efficiency_a, *charts.hcm_efficiency_a],
            EFFICIENCY_SYSTEM,
            period["Hiệu suất A"],
            PERCENT_DECIMALS,
            PERCENT,
            key("chart_eff_a"),
            message,
        )
    with right:
        _daily_chart(
            f"{EFFICIENCY_SUM} by day",
            [*charts.efficiency_b, *charts.hcm_efficiency_b],
            EFFICIENCY_SUM,
            period["Hiệu suất B"],
            PERCENT_DECIMALS,
            PERCENT,
            key("chart_eff_b"),
            "",
        )
    left, right = st.columns(2)
    with left:
        _daily_chart(
            f"{EFFICIENCY_NO_RATIO} by day",
            [*charts.efficiency_no_ratio, *charts.hcm_efficiency_no_ratio],
            EFFICIENCY_NO_RATIO,
            period["Hiệu suất (không tỉ lệ)"],
            PERCENT_DECIMALS,
            PERCENT,
            key("chart_eff_no_ratio"),
            "",
        )
    with right:
        _daily_chart(
            "MO 8h by day",
            [*charts.mo8h, *charts.hcm_mo8h],
            "MO 8h",
            period["MO 8h"],
            MONEY_DECIMALS,
            "",
            key("chart_mo8h"),
            message,
        )
    _output_chart(charts, key("chart_output"))


def _ranking_chart(title: str, lines: Sequence[RankedLineDTO], metric: str, key: str, message: str) -> None:
    label, decimals, suffix = RANKING_COLUMNS[metric]
    with panel(title):
        if message and not lines:
            st.info(message, icon=":material/info:")
            return
        # the factory is part of the name: the chart sums per name, and LINE 1 exists in several factories.
        # A horizontal chart draws its first row at the bottom, so the list is turned around.
        rows = [
            {
                BAR_NAME: f"{english_name(item.factory)} · {item.line}: {_value_text(item.value, decimals, suffix)}",
                label: round(item.value, decimals),
            }
            for item in reversed(lines)
        ]
        bar_chart(rows, x=BAR_NAME, y=label, horizontal=True, stacked=False, key=key, empty_message=NO_DATA_IN_RANGE)


def ranking_charts(charts: ChartsResponse, metric: str, key: Callable[[str], str]) -> None:
    left, right = st.columns(2)
    with left:
        _ranking_chart("Top 10 lines", charts.top_lines, metric, key("chart_top"), charts.not_applicable_message)
    with right:
        _ranking_chart(
            "Bottom 10 lines", charts.bottom_lines, metric, key("chart_bottom"), charts.not_applicable_message
        )
