"""Screen 4 - Sewing metrics (named Period Report until 2026-11-09; replaces the Monthly Report since 2026-11-06): the
factories week by week, month by month, quarter by quarter or year by year (UC-29, BR-68, BR-69). The figures one under
the other (no tabs since 2026-11-10): cards with the change against the period before (BR-70, BR-71; %Direct labor
cards under Direct worker, BR-77), the small charts folded under "Charts", the exact numbers folded. Display only.
Since 2026-11-13 also Matching strength and Changeover/line/day (BR-89)."""

import re

import streamlit as st

from backend.core.gateway import gateway
from backend.features.sewing_productivity import SewingProductivityController
from backend.features.sewing_productivity.dto.display_names import EFFICIENCY_SUM, english_name
from backend.features.sewing_productivity.dto.monthly_dto import (
    CHANGEOVER_PER_LINE_DAY,
    MonthlyReportRequest,
    PeriodKind,
    PeriodMetricDTO,
)
from frontend.core.base_page import BasePage
from frontend.core.components import empty_state, panel
from frontend.features.sewing_productivity.components.period_blocks import number_table, period_cards, small_charts
from frontend.features.sewing_productivity.components.report_filters import (
    NO_DATA_IN_RANGE,
    REPORT_SPINNER,
    load_filter_options,
    period_and_factories,
    show_data_times,
)

# BR-69 the short name, the full label (with its unit) and the icon of each figure, keyed by its backend name, in order
METRIC_LABELS = {
    "MO 8h": ("MO 8h", "MO 8h (USD)", "⏱️"),
    "Hiệu suất B": ("%Efficiency", EFFICIENCY_SUM, "⚡"),
    "Direct worker": ("Direct worker", "Direct worker (people per day)", "👷"),
    "Sản lượng": ("Output", "Output (pcs)", "👕"),
    "Tiền CM": ("Revenue", "Revenue (USD)", "💵"),
    "Giá CM trung bình": ("Avg CM price", "Avg CM price (USD/pc)", "🏷️"),
    "SMV bình quân": ("Avg SMV", "Avg SMV (min)", "🧵"),
    "Giờ làm trung bình": ("Avg working hours", "Avg working hours", "🕗"),
    "Tỷ lệ đúng sở trường": ("Matching strength", "Matching strength (%)", "🎯"),  # BR-89 (thêm 2026-11-13)
    CHANGEOVER_PER_LINE_DAY: ("Changeover/line/day", "Changeover / line / day", "🔁"),  # BR-89 (thêm 2026-11-13)
}
# UI concept 2026-11-13: the title colour of the two new figures
METRIC_COLORS = {"Tỷ lệ đúng sở trường": "green", CHANGEOVER_PER_LINE_DAY: "violet"}
# BR-77 figures shown only as an extra row of cards inside another tab: tab figure -> card figure
EXTRA_CARDS = {"Direct worker": "%Direct labor"}
JUMP_ANCHOR = "jump-to"  # AC-104 the "Jump to" bar, target of every "Back to top" link


def _anchor(metric: PeriodMetricDTO) -> str:
    """AC-104 the place a "Jump to" link scrolls to: "metric-mo-8h", "metric-efficiency"..."""
    return "metric-" + re.sub(r"[^a-z0-9]+", "-", _labels(metric)[0].lower()).strip("-")


def _labels(metric: PeriodMetricDTO) -> tuple[str, str, str]:
    name = english_name(metric.metric)
    return METRIC_LABELS.get(metric.metric, (name, name, "📈"))


class MonthlyReportPage(BasePage):
    title = "Sewing metrics"  # sửa 2026-11-09: trước đây "Period Report"
    icon = "🗓️"
    slug = "monthly"  # kept: links and permissions already given stay valid
    description = "Follow the factories week by week, month by month, quarter by quarter or year by year."
    menu_group = "Reports"

    def render(self) -> None:
        feature = gateway.open(SewingProductivityController)
        options = load_filter_options(feature)
        if options is None:
            return
        with panel("Filters", icon="🔎"):
            kind = st.segmented_control(
                "Period",
                [item.value for item in PeriodKind],
                default=PeriodKind.WEEK.value,
                required=True,
                key=self.key("period_kind"),
                persist_state="session",
            )
            from_date, to_date, factories = period_and_factories(
                self.key, options.default_year_from, options.latest_date
            )
        show_data_times(options)

        request = MonthlyReportRequest(
            from_date=from_date, to_date=to_date, factories=factories, period_kind=PeriodKind(kind)
        )
        with st.spinner(REPORT_SPINNER):
            data = feature.get_monthly_report(request)  # BR-30 stops the page here, the filters stay on screen
        if not data.has_data:
            empty_state(NO_DATA_IN_RANGE)
            return
        extras = {metric.metric: metric for metric in data.period_metrics if metric.metric in EXTRA_CARDS.values()}
        shown = [metric for metric in data.period_metrics if metric.metric not in extras]
        self._jump_bar(shown)
        for metric in shown:  # sửa 2026-11-10: one figure under the other, no tabs (AC-103)
            self._metric_block(metric, data.columns, extras.get(EXTRA_CARDS.get(metric.metric, "")))

    @staticmethod
    def _jump_bar(metrics: list[PeriodMetricDTO]) -> None:
        """AC-104 one link per figure; a click scrolls the page to that figure."""
        with panel():
            st.subheader("🧭 Jump to", anchor=JUMP_ANCHOR)
            with st.container(horizontal=True, gap="medium"):
                for metric in metrics:
                    st.markdown(f"[{_labels(metric)[0]}](#{_anchor(metric)})")

    def _metric_block(self, metric: PeriodMetricDTO, columns: list[str], extra: PeriodMetricDTO | None) -> None:
        _name, label, icon = _labels(metric)
        with panel():
            color = METRIC_COLORS.get(metric.metric)
            st.subheader(f"{icon} :{color}[{label}]" if color else f"{icon} {label}", anchor=_anchor(metric))
            period_cards(metric)
            if extra is not None:  # BR-77 %Direct labor under Direct worker
                period_cards(extra, title=f"{english_name(extra.metric)} (direct workers / total labor)")
            charts = st.expander(
                "Charts", icon=":material/add:", key=self.key(f"charts_{metric.metric}"), on_change="rerun"
            )
            with charts:
                if charts.open:  # closed by default; the charts are drawn only once opened
                    small_charts(metric, columns, label, self.key)
            number_table(metric, columns, self.key)
            st.caption(f"[Back to top](#{JUMP_ANCHOR})")
