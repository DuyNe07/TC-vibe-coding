"""The filter widgets shared by the report screens. All of them keep their value for the session."""

import re
from collections.abc import Callable, Iterable, Sequence
from datetime import date

import streamlit as st

from backend.core.base import EmptyRequest
from backend.features.sewing_productivity import SewingProductivityController
from backend.features.sewing_productivity.dto.filter_dto import FilterOptionsResponse
from backend.features.sewing_productivity.dto.overview_dto import Factory
from frontend.core.components import empty_state
from frontend.core.formatting import format_datetime

FACTORIES = tuple(factory.value for factory in Factory)  # fixed list (section 3): a factory without data stays listed
DEFAULT_FACTORY = Factory.FAC_1.value
DATE_FORMAT = "DD/MM/YYYY"
ALL_LABEL = "Tất cả"
NO_DATA_MESSAGE = "Chưa có dữ liệu. Người cập nhật cần tải file ở màn hình Cập nhật dữ liệu."
NO_DATA_IN_RANGE = "Chưa có dữ liệu trong khoảng thời gian này."
NO_DATA_ON_DAY = "Chưa có dữ liệu của ngày này."
REPORT_SPINNER = "Đang tính báo cáo..."

KeyMaker = Callable[[str], str]


def load_filter_options(feature: SewingProductivityController) -> FilterOptionsResponse | None:
    """UC-26. Without stored data: the AC-45 message and None, so the page stops there."""
    options = feature.get_filter_options(EmptyRequest())
    if not options.has_data:
        empty_state(NO_DATA_MESSAGE)
        return None
    return options


def show_data_times(options: FilterOptionsResponse) -> None:
    latest = options.latest_date.strftime("%d/%m/%Y") if options.latest_date else "-"
    st.caption(f"Dữ liệu mới nhất: {latest} · Lần tải file gần nhất: {format_datetime(options.last_upload_at)}")


def date_filter(label: str, value: date | None, key: str) -> date:
    return st.date_input(label, value=value, format=DATE_FORMAT, key=key, persist_state="session")


def factories_filter(key: str) -> list[str]:
    """Several factories. Nothing selected counts as all of them; the result keeps the fixed factory order."""
    selected = st.pills(
        "Xưởng", FACTORIES, selection_mode="multi", default=list(FACTORIES), key=key, persist_state="session"
    )
    return [factory for factory in FACTORIES if factory in selected] or list(FACTORIES)


def factory_filter(key: str) -> str:
    """One factory, Fac 1 first."""
    return st.segmented_control(
        "Xưởng", FACTORIES, default=DEFAULT_FACTORY, required=True, key=key, persist_state="session"
    )


def multi_filter(label: str, options: Iterable[str], key: str) -> list[str]:
    """Nothing selected = no filter: the empty list goes to the backend as it is (BR-29 applies only when not empty)."""
    return st.multiselect(label, list(options), placeholder=ALL_LABEL, key=key, persist_state="session")


def period_and_factories(
    key: KeyMaker, default_from: date | None, default_to: date | None
) -> tuple[date, date, list[str]]:
    left, middle, right = st.columns([1, 1, 2])
    with left:
        from_date = date_filter("Từ ngày", default_from, key("from_date"))
    with middle:
        to_date = date_filter("Đến ngày", default_to, key("to_date"))
    with right:
        factories = factories_filter(key("factories"))
    return from_date, to_date, factories


def period_and_factory(key: KeyMaker, default_from: date | None, default_to: date | None) -> tuple[date, date, str]:
    left, middle, right = st.columns([1, 1, 2])
    with left:
        from_date = date_filter("Từ ngày", default_from, key("from_date"))
    with middle:
        to_date = date_filter("Đến ngày", default_to, key("to_date"))
    with right:
        factory = factory_filter(key("factory"))
    return from_date, to_date, factory


def _line_number(line: str) -> tuple[int, str]:
    found = re.search(r"\d+", line)
    return (int(found.group()) if found else 0, line)


def lines_of(options: FilterOptionsResponse, factories: Sequence[str]) -> list[str]:
    """The lines of the chosen factories: no repeats, sorted by line number."""
    lines = {line for factory in factories for line in options.lines_by_factory.get(factory, [])}
    return sorted(lines, key=_line_number)
