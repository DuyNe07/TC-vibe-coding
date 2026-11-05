"""Screen 7, the weekly changeover numbers: the form, the saved list and the delete confirmation."""

from datetime import date
from typing import Any

import streamlit as st

from backend.core.base import EmptyRequest
from backend.core.exceptions import AppError
from backend.features.sewing_productivity import SewingProductivityController
from backend.features.sewing_productivity.dto.filter_dto import FilterOptionsResponse
from backend.features.sewing_productivity.dto.weekly_changeover_dto import (
    DeleteWeeklyChangeoverRequest,
    SaveWeeklyChangeoversRequest,
)
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, panel, show_error
from frontend.features.sewing_productivity.components.page_messages import leave_flash
from frontend.features.sewing_productivity.components.report_cells import day_text
from frontend.features.sewing_productivity.components.report_filters import DATE_FORMAT, FACTORIES

COLUMNS = ["Xưởng", "Từ ngày", "Đến ngày", "Số lần", "Người lưu"]


def _new_version(page: BasePage) -> None:
    """New widget keys: the typed numbers and the row selection do not survive a successful save or delete."""
    page.state.set("weekly_version", page.state.get("weekly_version", 0) + 1)


def weekly_form(page: BasePage, feature: SewingProductivityController, options: FilterOptionsResponse) -> None:
    version = page.state.get("weekly_version", 0)
    # the default week is part of the key: a new file moves the default, a date typed for the current week stays
    default_from, default_to = options.default_week_from or date.today(), options.default_week_to or date.today()
    with (
        panel("Đổi mã hàng tuần", icon="🔄", description="Để trống ô của xưởng nào thì không lưu xưởng đó."),
        st.form(page.key("weekly_form"), border=False),
    ):
        left, right = st.columns(2)
        from_date = left.date_input(
            "Từ ngày", value=default_from, format=DATE_FORMAT, key=page.key(f"weekly_from_{default_from}")
        )
        to_date = right.date_input(
            "Đến ngày", value=default_to, format=DATE_FORMAT, key=page.key(f"weekly_to_{default_to}")
        )
        # float mode on purpose: in whole-number mode the browser would silently turn 1,5 into 1 instead of BR-39
        counts = {
            factory: column.number_input(
                factory,
                value=None,
                step=1.0,
                format="%g",
                placeholder="Để trống",
                key=page.key(f"weekly_{factory}_{version}"),
            )
            for factory, column in zip(FACTORIES, st.columns(len(FACTORIES)), strict=True)
        }
        submitted = st.form_submit_button("Lưu số đổi mã hàng", type="primary")
    if not submitted:
        return
    try:
        result = feature.save_weekly_changeovers(
            SaveWeeklyChangeoversRequest(from_date=from_date, to_date=to_date, counts=counts)
        )
    except AppError as exc:  # the typed numbers stay in the form (AC-32)
        show_error(exc)
        return
    leave_flash(page.state, result.message)
    _new_version(page)
    st.rerun()


@st.dialog("Xác nhận xoá", icon=":material/delete:")
def _confirm_delete(page: BasePage, row: dict[str, Any]) -> None:
    """Only leaves a flag: the page run does the deleting, with the logged-in user."""
    st.write(f"Xoá số đổi mã hàng của {row['Xưởng']} từ {day_text(row['Từ ngày'])} đến {day_text(row['Đến ngày'])}?")
    with st.container(horizontal=True):
        if st.button("Xoá", type="primary", key=page.key("delete_yes")):
            page.state.set("do_delete_id", row["id"])
            st.rerun()
        if st.button("Huỷ", key=page.key("delete_no")):
            st.rerun()


def _delete_when_confirmed(page: BasePage, feature: SewingProductivityController) -> None:
    delete_id = page.state.pop("do_delete_id", None)
    if delete_id is None:
        return
    try:
        result = feature.delete_weekly_changeover(DeleteWeeklyChangeoverRequest(id=delete_id))
    except AppError as exc:
        show_error(exc)
        return
    leave_flash(page.state, result.message)
    _new_version(page)
    st.rerun()


def weekly_list(page: BasePage, feature: SewingProductivityController) -> None:
    version = page.state.get("weekly_version", 0)
    with panel("Số đổi mã hàng đã nhập", icon="📋"):
        _delete_when_confirmed(page, feature)
        items = feature.list_weekly_changeovers(EmptyRequest()).items
        selected = data_table(
            [
                {
                    "id": item.id,
                    "Xưởng": item.factory,
                    "Từ ngày": item.from_date,
                    "Đến ngày": item.to_date,
                    "Số lần": item.changeover_count,
                    "Người lưu": item.updated_by,
                }
                for item in items
            ],
            selection="single",
            column_order=COLUMNS,
            column_config={
                "Từ ngày": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Đến ngày": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Số lần": st.column_config.NumberColumn(format="localized"),
            },
            key=page.key(f"weekly_table_{version}"),
            empty_message="Chưa nhập số đổi mã hàng tuần nào.",
        )
        if st.button("Xoá dòng đã chọn", disabled=not selected, key=page.key("weekly_delete")) and selected:
            _confirm_delete(page, selected[0])
