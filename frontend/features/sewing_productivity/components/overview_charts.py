"""The 5 charts of Screen 1. Points with "-" never reach a chart: the shared chart component would draw them as 0."""

from collections.abc import Callable, Sequence

import streamlit as st

from backend.features.sewing_productivity.dto.overview_dto import (
    ChartPointDTO,
    ChartsResponse,
    RankedLineDTO,
    RankingMetric,
)
from frontend.core.components import bar_chart, line_chart, panel
from frontend.features.sewing_productivity.components.report_filters import NO_DATA_IN_RANGE

PERCENT_DECIMALS = 1
MONEY_DECIMALS = 2
RANKING_COLUMNS = {
    RankingMetric.EFFICIENCY_B.value: ("Hiệu suất B (%)", PERCENT_DECIMALS),
    RankingMetric.EFFICIENCY_A.value: ("Hiệu suất A (%)", PERCENT_DECIMALS),
    RankingMetric.MO8H.value: ("MO 8h", MONEY_DECIMALS),
}


def _daily_chart(
    title: str, points: Sequence[ChartPointDTO], label: str, decimals: int, key: str, message: str
) -> None:
    with panel(title):
        if message:
            st.info(message, icon=":material/info:")
            return
        rows = [{"Ngày": item.day, "Xưởng": item.factory, label: round(item.value, decimals)} for item in points]
        line_chart(rows, x="Ngày", y=label, color="Xưởng", key=key, empty_message=NO_DATA_IN_RANGE)


def _output_chart(charts: ChartsResponse, key: str) -> None:
    with panel("Sản lượng so với mục tiêu A giữa các xưởng"):
        if charts.not_applicable_message:
            st.info(charts.not_applicable_message, icon=":material/info:")
            return
        rows = []
        for item in charts.output_vs_target:
            rows.append({"Xưởng": item.factory, "Loại": "Sản lượng", "Số lượng": round(item.output)})
            if item.target_a is not None:
                rows.append({"Xưởng": item.factory, "Loại": "Mục tiêu A", "Số lượng": round(item.target_a)})
        bar_chart(rows, x="Xưởng", y="Số lượng", color="Loại", stacked=False, key=key, empty_message=NO_DATA_IN_RANGE)


def daily_charts(charts: ChartsResponse, key: Callable[[str], str]) -> None:
    """Two columns: efficiency A and B, then MO 8h and output against target A. Efficiency B stays under a filter."""
    message = charts.not_applicable_message
    left, right = st.columns(2)
    with left:
        _daily_chart("Hiệu suất A theo ngày", charts.efficiency_a, "Hiệu suất A (%)", 1, key("chart_eff_a"), message)
    with right:
        _daily_chart("Hiệu suất B theo ngày", charts.efficiency_b, "Hiệu suất B (%)", 1, key("chart_eff_b"), "")
    left, right = st.columns(2)
    with left:
        _daily_chart("MO 8h theo ngày", charts.mo8h, "MO 8h", MONEY_DECIMALS, key("chart_mo8h"), message)
    with right:
        _output_chart(charts, key("chart_output"))


def _ranking_chart(title: str, lines: Sequence[RankedLineDTO], metric: str, key: str, message: str) -> None:
    label, decimals = RANKING_COLUMNS[metric]
    with panel(title):
        if message and not lines:
            st.info(message, icon=":material/info:")
            return
        # the factory is part of the name: the chart sums per name, and LINE 1 exists in several factories
        rows = [{"Chuyền": f"{item.factory} · {item.line}", label: round(item.value, decimals)} for item in lines]
        bar_chart(rows, x="Chuyền", y=label, stacked=False, key=key, empty_message=NO_DATA_IN_RANGE)


def ranking_charts(charts: ChartsResponse, metric: str, key: Callable[[str], str]) -> None:
    left, right = st.columns(2)
    with left:
        _ranking_chart("10 chuyền cao nhất", charts.top_lines, metric, key("chart_top"), charts.not_applicable_message)
    with right:
        _ranking_chart(
            "10 chuyền thấp nhất", charts.bottom_lines, metric, key("chart_bottom"), charts.not_applicable_message
        )
