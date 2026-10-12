"""Screen 4 (`tieu-hao`) - Tiêu hao (UC-10..UC-14)."""

from datetime import date
from typing import Any

import streamlit as st

from backend.core.gateway import gateway
from backend.features.yarn_costing import YarnCostingController
from backend.features.yarn_costing.dto.common_dto import ActorDTO, LossGroupLevel, Technology
from backend.features.yarn_costing.dto.loss_dto import (
    ComponentRowDTO,
    CreatePrimaryLossGroupRequest,
    CreateSecondaryLossGroupRequest,
    DeleteLossGroupRequest,
    ListLossGroupsRequest,
    LossGroupDTO,
    LossGroupListResponse,
    UpdateLossGroupRequest,
)
from backend.features.yarn_costing.dto.reference_dto import GetReferenceDataRequest
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, editable_table, panel, section_title
from frontend.core.formatting import format_number
from frontend.features.yarn_costing.components.actor_block import actor_factory, actor_is_so, render_actor_block
from frontend.features.yarn_costing.components.dialogs import confirm_dialog
from frontend.features.yarn_costing.components.display import from_percent, pct, pct_exact, yes_no
from frontend.features.yarn_costing.components.factory_picker import factory_segment
from frontend.features.yarn_costing.components.flash import set_flash, show_flash
from frontend.features.yarn_costing.components.group_menu import render_group_menu
from frontend.features.yarn_costing.components.labels import (
    ALL,
    LEVEL_LABELS,
    TECHNOLOGY_LABELS,
    all_or,
    label_of,
)
from frontend.features.yarn_costing.components.permissions import action_state, explain

LOSS_PREFILL_KEY = "loss_prefill"
FORM_KEY = "loss_form"
PREFILL_DATA_KEY = "loss_prefill_data"
STAGE_COL = "Công đoạn"
LOSS_COL = "Tiêu hao (%)"
COMPONENT_COL = "Nhóm thành phần"
RATIO_COL = "Tỷ lệ (%)"
# ô nhập %: tối đa 4 chữ số thập phân (ví dụ 0,395% hoặc 0,5%), hiện đúng số đang lưu (không làm tròn 2 chữ số)
PERCENT_EDIT = {"min_value": 0.0, "max_value": 100.0, "step": 0.0001, "format": "%.4f"}
LOSS_VIEW_FORMAT = "%.4f%%"  # bảng tiêu hao chỉ xem: 4 chữ số thập phân, để thấy đúng số đang lưu (0,3950%)


def loss_percent(label: str) -> Any:
    return st.column_config.NumberColumn(label, format=LOSS_VIEW_FORMAT)


def _losses_from_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {str(r[STAGE_COL]): from_percent(r.get(LOSS_COL)) for r in rows if r.get(STAGE_COL)}


def _components_from_rows(rows: list[dict[str, Any]]) -> list[ComponentRowDTO]:
    return [
        ComponentRowDTO(component_group_key=str(r[COMPONENT_COL]), ratio=from_percent(r.get(RATIO_COL)))
        for r in rows
        if r.get(COMPONENT_COL)
    ]


def _derived_losses_table(group: LossGroupDTO, stage_codes: list[str], key: str) -> None:
    section_title("Tiêu hao tính ra")
    data_table(
        [{STAGE_COL: s, LOSS_COL: pct_exact(group.losses.get(s))} for s in stage_codes if s in group.losses],
        column_config={LOSS_COL: loss_percent(LOSS_COL)},
        empty_message="Chưa có tiêu hao tính ra.",
        key=key,
    )


class LossGroupPage(BasePage):
    title = "[Xưởng] Tiêu hao"
    icon = "📉"
    slug = "tieu-hao"
    description = "Tra cứu, khai báo, sửa và xoá nhóm tiêu hao sơ cấp, sợi pha của từng xưởng."

    def render(self) -> None:
        feature = gateway.open(YarnCostingController)
        reference = feature.get_reference_data(GetReferenceDataRequest(factory_code=None))
        render_group_menu(self, reference)
        prefill = self.state.pop(LOSS_PREFILL_KEY)
        if prefill:
            st.session_state[self.key("factory")] = prefill["factory_code"]
            self.state.set(FORM_KEY, "new_secondary")
            self.state.set(PREFILL_DATA_KEY, prefill)
        actor = render_actor_block(feature, self.state, reference)
        show_flash(self.state)

        with panel("Bộ lọc", icon="🔎"):
            factory = factory_segment(reference.factories, self.key("factory"), actor_factory(self.state))
            if factory is None:
                return
            c1, c2, c3 = st.columns([2, 3, 2], vertical_alignment="bottom")
            level = c1.selectbox(
                "Loại",
                [ALL, *list(LEVEL_LABELS)],
                format_func=lambda v: v if v == ALL else label_of(LEVEL_LABELS, v),
                key=self.key("f_level"),
            )
            keyword = c2.text_input("Từ khoá", key=self.key("f_keyword"))
            locked_only = c3.toggle("Chỉ nhóm đang khoá", value=False, key=self.key("f_locked"))
        data = feature.list_loss_groups(
            ListLossGroupsRequest(factory_code=factory, level=all_or(level), keyword=keyword, locked_only=locked_only)
        )
        all_groups = feature.list_loss_groups(ListLossGroupsRequest(factory_code=factory))
        stage_codes = data.stage_codes or all_groups.stage_codes

        with panel("Nhóm tiêu hao", icon="📋"):
            picked = data_table(
                self._group_rows(data, stage_codes),
                column_config={f"{s} (%)": loss_percent(f"{s} (%)") for s in stage_codes},
                selection="single",
                key=self.key(f"groups.{factory}"),
                empty_message="Chưa có nhóm tiêu hao nào.",
            )
            p_disabled, p_why = action_state(self.state, "UC-11", factory)
            s_disabled, s_why = action_state(self.state, "UC-12", factory)
            left, right, _ = st.columns([1, 1, 3])
            if left.button("Thêm nhóm sơ cấp", icon="➕", key=self.key("add_primary"), disabled=p_disabled, help=p_why):
                self.state.set(FORM_KEY, "new_primary")
                st.rerun()
            if right.button(
                "Thêm nhóm sợi pha", icon="➕", key=self.key("add_secondary"), disabled=s_disabled, help=s_why
            ):
                self.state.set(FORM_KEY, "new_secondary")
                st.rerun()
            explain(p_why, s_why)

        form = self.state.get(FORM_KEY)
        if form == "new_primary":
            self._primary_form(feature, actor, factory, stage_codes)
        elif form == "new_secondary":
            self._secondary_form(feature, actor, factory, all_groups, stage_codes)
        elif picked:
            group = next((g for g in data.items if g.group_key == picked[0]["Nhóm"]), None)
            if group is not None:
                self._selected_group(feature, actor, factory, group, all_groups, stage_codes)

    @staticmethod
    def _group_rows(data: LossGroupListResponse, stage_codes: list[str]) -> list[dict[str, Any]]:
        return [
            {
                "Nhóm": g.group_key,
                "Nguyên liệu": g.material,
                "Công nghệ": g.technology.value,
                "Loại": g.level.value,
                "Thành phần": "; ".join(
                    f"{c.component_group_key} {format_number(pct(c.ratio), 2)}%" for c in g.components
                ),
                **{f"{s} (%)": pct_exact(g.losses.get(s)) for s in stage_codes},
                "Đang khoá": yes_no(g.is_locked),
                "Số mã đang dùng": g.used_count or len(g.used_by_codes),
            }
            for g in data.items
        ]

    def _close_button(self, name: str) -> None:
        if st.button("Đóng", type="tertiary", key=self.key(f"close.{name}")):
            self.state.pop(FORM_KEY)
            self.state.pop(PREFILL_DATA_KEY)
            st.rerun()

    def _header_inputs(self, prefix: str, defaults: dict[str, Any]) -> tuple[str, str, Technology]:
        c1, c2, c3 = st.columns([3, 3, 2], vertical_alignment="bottom")
        label = c1.text_input(
            "Nhóm sợi",
            value=defaults.get("group_label", ""),
            max_chars=200,
            placeholder="Ví dụ: PE NORMAL - RING",
            key=self.key(f"{prefix}.label"),
        )
        material = c2.text_input("Nguyên liệu", max_chars=200, key=self.key(f"{prefix}.material"))
        tech_default = defaults.get("technology") or Technology.RING
        technology = c3.segmented_control(
            "Công nghệ",
            list(TECHNOLOGY_LABELS),
            default=Technology(tech_default) if tech_default in list(Technology) else Technology.RING,
            required=True,
            format_func=lambda v: label_of(TECHNOLOGY_LABELS, v),
            key=self.key(f"{prefix}.tech"),
        )
        return label, material, technology or Technology.RING

    # ---- UC-11 ----
    def _primary_form(
        self, feature: YarnCostingController, actor: ActorDTO | None, factory: str, stage_codes: list[str]
    ) -> None:
        with panel("Thêm nhóm sơ cấp", icon="➕"):
            label, material, technology = self._header_inputs(f"new_primary.{factory}", {})
            rows = editable_table(
                [{STAGE_COL: s, LOSS_COL: 0.0} for s in stage_codes],
                key=self.key(f"new_primary_losses.{factory}"),
                columns=[STAGE_COL, LOSS_COL],
                disabled=[STAGE_COL],
                column_config={LOSS_COL: st.column_config.NumberColumn(LOSS_COL, **PERCENT_EDIT)},
            )
            disabled, why = action_state(self.state, "UC-11", factory)
            left, right, _ = st.columns([1, 1, 3])
            if left.button("Lưu nhóm", type="primary", key=self.key("primary_save"), disabled=disabled, help=why):
                result = feature.create_primary_loss_group(
                    CreatePrimaryLossGroupRequest(
                        actor=actor,
                        factory_code=factory,
                        yarn_group_label=label,
                        material=material,
                        technology=technology,
                        losses=_losses_from_rows(rows),
                    )
                )
                set_flash(self.state, result.message)
                self.state.pop(FORM_KEY)
                st.rerun()
            with right:
                self._close_button("primary")
            explain(why)

    # ---- UC-12 ----
    def _secondary_form(
        self,
        feature: YarnCostingController,
        actor: ActorDTO | None,
        factory: str,
        all_groups: LossGroupListResponse,
        stage_codes: list[str],
    ) -> None:
        prefill = self.state.get(PREFILL_DATA_KEY) or {}
        preview_key = f"secondary_preview.{factory}"
        with panel("Thêm nhóm sợi pha", icon="➕"):
            label, material, technology = self._header_inputs(f"new_secondary.{factory}", prefill)
            rows = editable_table(
                [],
                key=self.key(f"new_components.{factory}"),
                columns=[COMPONENT_COL, RATIO_COL],
                allow_add_delete=True,
                column_config={
                    COMPONENT_COL: st.column_config.SelectboxColumn(
                        COMPONENT_COL, options=[g.group_key for g in all_groups.items], required=True
                    ),
                    RATIO_COL: st.column_config.NumberColumn(RATIO_COL, **PERCENT_EDIT),
                },
            )
            st.caption("Từ 1 đến 5 thành phần, tổng tỷ lệ 100%.")
            disabled, why = action_state(self.state, "UC-12", factory)

            def build(save: bool) -> CreateSecondaryLossGroupRequest:
                return CreateSecondaryLossGroupRequest(
                    actor=actor,
                    factory_code=factory,
                    yarn_group_label=label,
                    material=material,
                    technology=technology,
                    components=_components_from_rows(rows),
                    save=save,
                )

            b1, b2, b3, _ = st.columns([1, 1, 1, 2])
            if b1.button(
                "Xem tiêu hao tính ra", icon="🔍", key=self.key("secondary_preview"), disabled=disabled, help=why
            ):
                self.state.set(preview_key, feature.create_secondary_loss_group(build(False)).group)
            if b2.button("Lưu nhóm", type="primary", key=self.key("secondary_save"), disabled=disabled, help=why):
                result = feature.create_secondary_loss_group(build(True))
                set_flash(self.state, result.message)
                self.state.pop(FORM_KEY)
                self.state.pop(PREFILL_DATA_KEY)
                self.state.pop(preview_key)
                st.rerun()
            with b3:
                self._close_button("secondary")
            explain(why)
            preview = self.state.get(preview_key)
            if preview is not None:
                _derived_losses_table(preview, stage_codes, self.key(f"preview_table.{factory}"))

    # ---- UC-13 / UC-14 ----
    def _selected_group(
        self,
        feature: YarnCostingController,
        actor: ActorDTO | None,
        factory: str,
        g: LossGroupDTO,
        all_groups: LossGroupListResponse,
        stage_codes: list[str],
    ) -> None:
        gk = g.group_key
        with panel(f"Nhóm: {gk}", icon="✏️"):
            locked_list = ", ".join(g.locked_codes[:5])
            if g.is_locked:
                st.warning(
                    f"Nhóm đang khoá: đang được dùng cho sợi đã có mã kế toán ({locked_list}). Chỉ Phòng SO được sửa.",
                    icon="🔒",
                )
            st.caption(f"Loại: {g.level.value}")
            c1, c2 = st.columns([3, 2], vertical_alignment="bottom")
            material = c1.text_input("Nguyên liệu", value=g.material, max_chars=200, key=self.key(f"g_material.{gk}"))
            technology = c2.segmented_control(
                "Công nghệ",
                list(TECHNOLOGY_LABELS),
                default=g.technology,
                required=True,
                format_func=lambda v: label_of(TECHNOLOGY_LABELS, v),
                key=self.key(f"g_tech.{gk}"),
            )
            use_components = g.level == LossGroupLevel.THU_CAP
            if g.level == LossGroupLevel.NHAP_TU_FILE:
                use_components = st.toggle(
                    "Khai báo thành phần (chuyển thành nhóm sợi pha)", value=False, key=self.key(f"g_to_sec.{gk}")
                )
            losses = None
            components = None
            if use_components:
                options = [x.group_key for x in all_groups.items if x.group_key != gk]
                rows = editable_table(
                    [{COMPONENT_COL: c.component_group_key, RATIO_COL: pct_exact(c.ratio)} for c in g.components],
                    key=self.key(f"g_components.{gk}"),
                    columns=[COMPONENT_COL, RATIO_COL],
                    allow_add_delete=True,
                    column_config={
                        COMPONENT_COL: st.column_config.SelectboxColumn(COMPONENT_COL, options=options, required=True),
                        RATIO_COL: st.column_config.NumberColumn(RATIO_COL, **PERCENT_EDIT),
                    },
                )
                st.caption("Từ 1 đến 5 thành phần, tổng tỷ lệ 100%.")
                components = _components_from_rows(rows)
                if g.level == LossGroupLevel.THU_CAP:
                    _derived_losses_table(g, stage_codes, self.key(f"g_derived.{gk}"))
            else:
                rows = editable_table(
                    [{STAGE_COL: s, LOSS_COL: pct_exact(g.losses.get(s, 0)) or 0.0} for s in stage_codes],
                    key=self.key(f"g_losses.{gk}"),
                    columns=[STAGE_COL, LOSS_COL],
                    disabled=[STAGE_COL],
                    column_config={LOSS_COL: st.column_config.NumberColumn(LOSS_COL, **PERCENT_EDIT)},
                )
                losses = _losses_from_rows(rows)

            d1, d2 = st.columns([1, 3])
            effective = d1.date_input(
                "Ngày hiệu lực", value=date.today(), format="DD/MM/YYYY", key=self.key(f"g_eff.{gk}")
            )
            reason = d2.text_area("Lý do", max_chars=500, key=self.key(f"g_reason.{gk}"))

            section_title("Mã đang dùng nhóm")
            data_table(
                [{"Mã sợi": c, "Đã có mã kế toán": yes_no(c in g.locked_codes)} for c in g.used_by_codes],
                empty_message="Chưa có mã sợi nào dùng nhóm này.",
                key=self.key(f"g_used.{gk}"),
            )

            upd_disabled, upd_why = action_state(self.state, "UC-13", factory)
            if not upd_disabled and g.is_locked and not actor_is_so(self.state):
                upd_disabled = True
                upd_why = (
                    f"Nhóm tiêu hao '{gk}' đang được dùng cho sợi đã có mã kế toán ({locked_list}). "
                    "Chỉ Phòng SO được sửa."
                )
            del_disabled, del_why = action_state(self.state, "UC-14", factory)
            request = UpdateLossGroupRequest(
                actor=actor or ActorDTO(),
                factory_code=factory,
                group_key=gk,
                material=material,
                technology=technology or g.technology,
                losses=losses,
                components=components,
                reason=reason,
                effective_date=effective,
            )
            left, right, _ = st.columns([1, 1, 3])
            if left.button("Lưu thay đổi", type="primary", key=self.key("g_save"), disabled=upd_disabled, help=upd_why):
                confirm_dialog(
                    self.state,
                    self.key(f"dlg.update.{gk}"),
                    "Xác nhận sửa nhóm tiêu hao",
                    f"Lưu thay đổi nhóm '{gk}'? App sẽ tính lại mọi mã đang dùng nhóm này và các nhóm sợi pha dùng nó "
                    f"({len(g.used_by_codes)} mã dùng trực tiếp).",
                    "Lưu và tính lại",
                    lambda: feature.update_loss_group(request).message,
                )
            if right.button("Xoá nhóm", icon="🗑️", key=self.key("g_delete"), disabled=del_disabled, help=del_why):
                confirm_dialog(
                    self.state,
                    self.key(f"dlg.delete.{gk}"),
                    "Xác nhận xoá nhóm tiêu hao",
                    f"Xoá nhóm '{gk}'? Chỉ xoá được nhóm không có mã sợi nào dùng và không là thành phần của nhóm khác.",
                    "Xoá nhóm",
                    lambda: (
                        feature.delete_loss_group(
                            DeleteLossGroupRequest(actor=actor or ActorDTO(), factory_code=factory, group_key=gk)
                        ).message
                    ),
                )
            explain(upd_why, del_why)
