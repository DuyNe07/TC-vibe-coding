"""Screen 2 - Line Detail (sửa 2026-11-12): one row per line over the chosen dates (BR-83); pick a line to see its
strength and the base orders it made (BR-84). Sửa 2026-11-13: Line performance is merged here - its table left the app,
its Excel file (UC-32, BR-85) is downloaded from this page; the weekly report button stays on Overview only."""

from datetime import date

import streamlit as st

from backend.core.gateway import gateway
from backend.features.sewing_productivity import SewingProductivityController
from backend.features.sewing_productivity.dto.changeover_dto import ChangeoverRequest
from backend.features.sewing_productivity.dto.display_names import english_name, english_terms
from backend.features.sewing_productivity.dto.line_detail_dto import (
    Factory,
    LineDetailRequest,
    LineTrendPointDTO,
    PeriodKind,
)
from frontend.core.base_page import BasePage
from frontend.core.components import download_button, empty_state, panel
from frontend.features.sewing_productivity.components.line_overview_blocks import line_details, line_table
from frontend.features.sewing_productivity.components.report_filters import (
    NO_DATA_IN_RANGE,
    REPORT_SPINNER,
    load_filter_options,
    multi_filter,
    period_and_factory,
    show_data_times,
)

FILTERS_ANCHOR = "filters"  # BR-91 (thêm 2026-11-13 lần 3)
LINE_PERFORMANCE_NOTE = "File gồm 4 xưởng, theo khoảng ngày đang chọn."


class LineDetailPage(BasePage):
    title = "Line Detail"
    icon = "🧵"
    slug = "line-detail"
    description = (
        "Each line over the chosen dates: output, %efficiency, MO 8h, matching, changeover and its orders; "
        "the Line performance Excel file."
    )
    menu_group = "Reports"

    def render(self) -> None:
        feature = gateway.open(SewingProductivityController)
        options = load_filter_options(feature)
        if options is None:
            return
        with panel():
            st.subheader("🔎 Filters", anchor=FILTERS_ANCHOR)  # BR-91: the target of "Back to filters"
            from_date, to_date, factory = period_and_factory(
                self.key, options.default_week_from, options.default_week_to
            )
            first, second, third = st.columns(3)
            with first:
                lines = multi_filter("Line", options.lines_by_factory.get(factory, []), self.key("lines"))
            with second:
                customer_groups = multi_filter("Customer group", options.customer_groups, self.key("customer_groups"))
            with third:
                product_groups = multi_filter("Product group", options.product_groups, self.key("product_groups"))
        show_data_times(options)

        request = LineDetailRequest(
            from_date=from_date,
            to_date=to_date,
            factory=factory,
            lines=lines,
            customer_groups=customer_groups,
            product_groups=product_groups,
        )
        with st.spinner(REPORT_SPINNER):
            data = feature.get_line_detail(request)
        self._line_performance_file(feature, from_date, to_date, Factory(factory))  # 4 factories, whatever is chosen
        if not data.has_data:
            empty_state(NO_DATA_IN_RANGE)
            return
        if data.note:
            st.info(english_terms(data.note), icon=":material/info:")

        picked = line_table(self, data.line_overview)  # BR-83 (sửa 2026-11-12: replaces the line-by-day tables)
        if picked is not None:
            line_details(
                self,
                data,
                picked.line,
                lambda kind: self._trend(feature, request, picked.line, kind),
                filter_note=self._filter_note(request),
            )

    @staticmethod
    def _filter_note(request: LineDetailRequest) -> str:
        """BR-91 the filters in use, in one line, with the link back up to them."""

        def chosen(values: list[str], everything: str) -> str:
            return ", ".join(values) if values else everything

        parts = [
            english_name(request.factory.value),
            f"{request.from_date:%d/%m/%Y} to {request.to_date:%d/%m/%Y}",
            chosen(request.lines, "all lines"),
            chosen(request.customer_groups, "all customer groups"),
            chosen(request.product_groups, "all product groups"),
        ]
        return f"Filters: {'; '.join(parts)}. [Back to filters](#{FILTERS_ANCHOR})"

    @staticmethod
    def _trend(
        feature: SewingProductivityController, request: LineDetailRequest, line: str, kind: PeriodKind
    ) -> list[LineTrendPointDTO]:
        """BR-90 (thêm 2026-11-13 lần 2) the "Line trend" of the line picked, same filters as the table."""
        with st.spinner(REPORT_SPINNER):
            return feature.get_line_detail(request.model_copy(update={"trend_line": line, "trend_kind": kind})).trend

    def _line_performance_file(
        self, feature: SewingProductivityController, from_date: date, to_date: date, factory: Factory
    ) -> None:
        """UC-32, BR-85 (sửa 2026-11-13): the Line performance file of the 4 factories for the chosen dates."""
        request = ChangeoverRequest(from_date=from_date, to_date=to_date, factories=[factory], line_performance=True)
        with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
            download_button(
                lambda: feature.export_changeover(request),
                label="Download Line performance",
                key=self.key("export_line_performance"),
                primary=True,
                file_name=f"Line performance - {from_date:%d.%m} to {to_date:%d.%m}.xlsx",
            )
            st.caption(LINE_PERFORMANCE_NOTE)
