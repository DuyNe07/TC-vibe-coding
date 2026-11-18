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
    TOTAL_COLUMN,
    english_name,
)
from backend.features.sewing_productivity.dto.overview_dto import (
    ChartPointDTO,
    ChartsResponse,
    OverviewMetricDTO,
    RankingMetric,
)
from frontend.core.components import line_chart, panel
from frontend.core.session_state import SessionState
from frontend.features.sewing_productivity.components.number_format import format_number
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
    Card("SMV bình quân", "Avg SMV (min)", ":material/timer:", "#0F9D8F", "", "", MONEY_DECIMALS),  # BR-66 teal
    Card("MO 8h", "MO 8h (USD)", ":material/schedule:", "orange", "$", "", MONEY_DECIMALS),
    Card("Hiệu suất B", EFFICIENCY_SUM, ":material/speed:", "red", "", "%", PERCENT_DECIMALS),
    Card("%Direct labor", "%Direct labor (%)", ":material/groups:", "#5B7083", "", "%", PERCENT_DECIMALS),  # BR-65
)
CARD_HEIGHT = 310  # every card the same height
CARD_TITLE_HEIGHT = 58  # two lines of title in every card, so the totals and the bars line up across the row
CARD_TOTAL_HEIGHT = 80  # "Total" and the big number, the same height in every card
CARD_LINE_HEIGHT = 52  # one more site line (name and bar) in a card
CARD_SITE_NAMES = {DEFAULT_FACTORY: "Vinh Long", HCM_COLUMN: "HCM"}
HCM_MEMBERS = ("Fac 2", "Fac 3", "Fac 5")  # BR-60, the factories added together in HCM (BR-51)
HCM_DETAIL = "hcm_detail_open"
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


def _colored(color: str, text: str) -> str:
    """Markdown coloured text: a theme colour name, or a "#hex" colour the theme palette has no name for (teal)."""
    if color.startswith("#"):
        return f':color[{text}]{{foreground="{color}"}}'
    return f":{color}[{text}]"


def _card(card: Card, metric: OverviewMetricDTO, sites: Sequence[str], height: int) -> None:
    """One card of the same height as the others: what it is (colour, icon, unit), the total, then each site.

    Each site has a bar: the biggest line fills it, the others show their size against it. The title and the total
    sit in blocks of a fixed height, so a title on one line and a title on two lines leave every row level."""
    largest = max((metric.values.get(site) or 0 for site in sites), default=0)
    with st.container(border=True, height=height):
        with st.container(border=False, height=CARD_TITLE_HEIGHT):
            st.markdown(_colored(card.color, f"{card.icon} **{card.label}**"))  # wraps; a badge would cut it
        with st.container(border=False, height=CARD_TOTAL_HEIGHT, gap=None):
            st.caption("Total")
            # a heading, not st.metric: st.metric cuts a long number with "...", a heading wraps it
            st.subheader(
                _colored(card.color, _markdown(_card_value(card, metric, TOTAL_COLUMN, mark=False))), anchor=False
            )
        for site in sites:
            value = metric.values.get(site) or 0
            st.progress(
                min(max(value / largest, 0), 1) if largest > 0 else 0,
                text=f":{CARD_SITE_COLORS.get(site, 'gray')}[{CARD_SITE_NAMES.get(site, '· ' + site)}] "
                f"**{_markdown(_card_value(card, metric, site))}**",
            )


def _hcm_detail_button(state: SessionState, key: Callable[[str], str]) -> bool:
    """BR-60 the small "+" that opens Fac 2, Fac 3, Fac 5 under HCM in every card ("-" closes them)."""
    opened = bool(state.get(HCM_DETAIL, False))
    if st.button(
        "Hide HCM factories" if opened else "HCM factories",
        icon=":material/remove:" if opened else ":material/add:",
        type="tertiary",
        key=key("hcm_detail"),
    ):
        state.set(HCM_DETAIL, not opened)
        st.rerun()
    return opened


def group_summary(
    metrics: Sequence[OverviewMetricDTO], factories: Sequence[str], state: SessionState, key: Callable[[str], str]
) -> None:
    """BR-58 seven cards: the total of the chosen factories in big type, Vinh Long and HCM under it (BR-60: and the
    HCM factories when the "+" is open).

    Markdown cards, not metric tiles: a tile cuts a long number, a card wraps it."""
    by_name = {metric.metric: metric for metric in metrics}
    if not all(TOTAL_COLUMN in by_name[card.metric].values for card in CARDS):
        return
    sites = []
    if DEFAULT_FACTORY in factories:
        sites.append(DEFAULT_FACTORY)
    has_hcm = any(HCM_COLUMN in metric.values for metric in metrics)
    if has_hcm:
        sites.append(HCM_COLUMN)
    height = CARD_HEIGHT
    with panel("Vinh Long - HCM", icon="🏭", description="Total = every chosen factory together. Money in USD."):
        if has_hcm and _hcm_detail_button(state, key):
            members = [factory for factory in HCM_MEMBERS if factory in factories]
            sites.extend(members)
            height += CARD_LINE_HEIGHT * len(members)
        for column, card in zip(st.columns(len(CARDS)), CARDS, strict=True):
            with column:
                _card(card, by_name[card.metric], sites, height)


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


def daily_charts(charts: ChartsResponse, metrics: Sequence[OverviewMetricDTO], key: Callable[[str], str]) -> None:
    """Two columns: %Efficiency (with ratio) and MO 8h by day.

    BR-67: no daily chart of the system or no-ratio efficiency. MO 8h stops under a customer or product filter.
    BR-92 (sửa 2026-11-13 lần 4): the output vs system target chart and the line ranking left the page."""
    message = charts.not_applicable_message
    period: PeriodValues = {metric.metric: metric.values for metric in metrics}
    left, right = st.columns(2)
    with left:
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
