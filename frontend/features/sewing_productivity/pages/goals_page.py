"""Screen 8 - Targets & Thresholds: the levels in force, the form for a new level and the history."""

from collections.abc import Sequence
from datetime import date
from typing import Any

import streamlit as st

from backend.core.base import EmptyRequest
from backend.core.exceptions import AppError
from backend.core.gateway import gateway
from backend.features.sewing_productivity import SewingProductivityController
from backend.features.sewing_productivity.dto.display_names import english_name
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
    ("%Efficiency target", "efficiency_target", 1, "%", None),
    ("MO 8h target", "mo8h_target", 2, "", None),
    ("%Efficiency threshold", "efficiency_threshold", 1, "%", None),
    ("MO 8h threshold", "mo8h_threshold", 2, "", None),
)
EMPTY_MESSAGE = "No levels yet."


def _goal_rows(goals: Sequence[GoalDTO], with_user: bool) -> list[dict[str, Any]]:
    columns: dict[str, Sequence[Any]] = {
        "Factory": [english_name(goal.factory) for goal in goals],
        "Effective from": [goal.effective_from for goal in goals],
        **spec_columns(goals, GOAL_COLUMNS),
    }
    if with_user:
        columns["Saved by"] = [english_name(goal.updated_by) for goal in goals]
    return column_rows(columns)


class GoalsPage(BasePage):
    title = "Targets & Thresholds"
    icon = "🎯"
    slug = "goals"
    description = "See and change the targets and thresholds by effective date."
    menu_group = "Data management"

    def render(self) -> None:
        feature = gateway.open(SewingProductivityController)
        try:
            goals = feature.list_goals(EmptyRequest())
        except AppError as exc:  # BR-09 is the only failure of this use case
            show_no_permission(exc)
            return
        show_flash(self.state)
        column_config = {
            "Effective from": st.column_config.DateColumn(format="DD/MM/YYYY"),
            **right_text_columns(spec_labels(GOAL_COLUMNS)),
        }

        with panel("Levels in force", icon="🎯"):
            data_table(
                _goal_rows(goals.current, with_user=False),
                column_config=column_config,
                key=self.key("current"),
                empty_message=EMPTY_MESSAGE,
            )
        with panel("Add a new level", icon="➕"):
            self._new_goal_form(feature)
        with panel("History", icon="🕘"):
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
                "Factory",
                FACTORIES,
                index=None,
                placeholder="Choose a factory",
                format_func=english_name,
                key=self.key(f"factory_{version}"),
            )
            effective_from = right.date_input(
                "Effective from", value=date.today(), format=DATE_FORMAT, key=self.key(f"effective_from_{version}")
            )
            first, second, third, fourth = st.columns(4)
            efficiency_target = first.number_input(
                "%Efficiency target",
                value=None,
                step=0.1,
                format="%.1f",
                key=self.key(f"efficiency_target_{version}"),
            )
            mo8h_target = second.number_input(
                "MO 8h target", value=None, step=0.01, format="%.2f", key=self.key(f"mo8h_target_{version}")
            )
            efficiency_threshold = third.number_input(
                "%Efficiency threshold",
                value=None,
                step=0.1,
                format="%.1f",
                key=self.key(f"efficiency_threshold_{version}"),
            )
            mo8h_threshold = fourth.number_input(
                "MO 8h threshold", value=None, step=0.01, format="%.2f", key=self.key(f"mo8h_threshold_{version}")
            )
            submitted = st.form_submit_button("Save new level", type="primary")
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
