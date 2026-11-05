"""Screen 8 - Mục tiêu và ngưỡng: the levels in force, the form for a new level and the history."""

from collections.abc import Sequence
from datetime import date
from typing import Any

import streamlit as st

from backend.core.base import EmptyRequest
from backend.core.exceptions import AppError
from backend.core.gateway import gateway
from backend.features.sewing_productivity import SewingProductivityController
from backend.features.sewing_productivity.dto.goal_dto import GoalDTO, SaveGoalRequest
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, panel, show_error
from frontend.features.sewing_productivity.components.page_messages import (
    leave_flash,
    show_flash,
    show_no_permission,
)
from frontend.features.sewing_productivity.components.report_cells import (
    ColumnSpec,
    column_rows,
    right_text_columns,
    spec_columns,
    spec_labels,
)
from frontend.features.sewing_productivity.components.report_filters import DATE_FORMAT, FACTORIES

GOAL_COLUMNS: tuple[ColumnSpec, ...] = (
    ("Mục tiêu hiệu suất", "efficiency_target", 1, "%", None),
    ("Mục tiêu MO 8h", "mo8h_target", 2, "", None),
    ("Ngưỡng hiệu suất", "efficiency_threshold", 1, "%", None),
    ("Ngưỡng MO 8h", "mo8h_threshold", 2, "", None),
)
EMPTY_MESSAGE = "Chưa có mức nào."


def _goal_rows(goals: Sequence[GoalDTO], with_user: bool) -> list[dict[str, Any]]:
    columns: dict[str, Sequence[Any]] = {
        "Xưởng": [goal.factory for goal in goals],
        "Ngày hiệu lực": [goal.effective_from for goal in goals],
        **spec_columns(goals, GOAL_COLUMNS),
    }
    if with_user:
        columns["Người lưu"] = [goal.updated_by for goal in goals]
    return column_rows(columns)


class GoalsPage(BasePage):
    title = "Mục tiêu và ngưỡng"
    icon = "🎯"
    slug = "goals"
    description = "Xem và đổi mục tiêu, ngưỡng theo ngày hiệu lực."
    menu_group = "Quản lý dữ liệu"

    def render(self) -> None:
        feature = gateway.open(SewingProductivityController)
        try:
            goals = feature.list_goals(EmptyRequest())
        except AppError as exc:  # BR-09 is the only failure of this use case
            show_no_permission(exc)
            return
        show_flash(self.state)
        column_config = {
            "Ngày hiệu lực": st.column_config.DateColumn(format="DD/MM/YYYY"),
            **right_text_columns(spec_labels(GOAL_COLUMNS)),
        }

        with panel("Mức đang áp dụng", icon="🎯"):
            data_table(
                _goal_rows(goals.current, with_user=False),
                column_config=column_config,
                key=self.key("current"),
                empty_message=EMPTY_MESSAGE,
            )
        with panel("Thêm mức mới", icon="➕"):
            self._new_goal_form(feature)
        with panel("Lịch sử", icon="🕘"):
            data_table(
                _goal_rows(goals.history, with_user=True),
                column_config=column_config,
                key=self.key("history"),
                empty_message=EMPTY_MESSAGE,
            )

    def _new_goal_form(self, feature: SewingProductivityController) -> None:
        version = self.state.get("goal_version", 0)  # a new key empties the form after a successful save only
        with st.form(self.key("goal_form"), border=False):
            left, right = st.columns(2)
            factory = left.selectbox(
                "Xưởng", FACTORIES, index=None, placeholder="Chọn xưởng", key=self.key(f"factory_{version}")
            )
            effective_from = right.date_input(
                "Ngày hiệu lực", value=date.today(), format=DATE_FORMAT, key=self.key(f"effective_from_{version}")
            )
            first, second, third, fourth = st.columns(4)
            efficiency_target = first.number_input(
                "Mục tiêu hiệu suất (%)",
                value=None,
                step=0.1,
                format="%.1f",
                key=self.key(f"efficiency_target_{version}"),
            )
            mo8h_target = second.number_input(
                "Mục tiêu MO 8h", value=None, step=0.01, format="%.2f", key=self.key(f"mo8h_target_{version}")
            )
            efficiency_threshold = third.number_input(
                "Ngưỡng hiệu suất (%)",
                value=None,
                step=0.1,
                format="%.1f",
                key=self.key(f"efficiency_threshold_{version}"),
            )
            mo8h_threshold = fourth.number_input(
                "Ngưỡng MO 8h", value=None, step=0.01, format="%.2f", key=self.key(f"mo8h_threshold_{version}")
            )
            submitted = st.form_submit_button("Lưu mức mới", type="primary")
        if not submitted:
            return
        try:
            result = feature.save_goal(
                SaveGoalRequest(
                    factory=factory,
                    effective_from=effective_from,
                    efficiency_target=efficiency_target,
                    mo8h_target=mo8h_target,
                    efficiency_threshold=efficiency_threshold,
                    mo8h_threshold=mo8h_threshold,
                )
            )
        except AppError as exc:  # shown under the form, the typed values stay (AC-28)
            show_error(exc)
            return
        leave_flash(self.state, result.message)
        self.state.set("goal_version", version + 1)
        st.rerun()
