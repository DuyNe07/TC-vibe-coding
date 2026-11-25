"""Screen 5 - Định mức và tham số: bộ định mức, tham số chung, hệ số theo mã hàng, ngày lễ
(UC-06..UC-11, UC-32..UC-34, UC-37)."""

from datetime import date

import streamlit as st

from backend.core.base import EmptyRequest
from backend.core.current_user import get_current_user, set_current_user
from backend.core.gateway import gateway
from backend.features.woven_costing import WovenCostingController
from backend.features.woven_costing.dto.common_dto import CostItem, FactorStage, HolidayAction, RoleCode
from backend.features.woven_costing.dto.master_dto import (
    FabricFactorDTO,
    NormTableDTO,
    SaveFabricFactorRequest,
    SaveHolidayRequest,
    SaveNormSetRequest,
    ViewNormSetRequest,
)
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, empty_state, file_upload, panel
from frontend.features.woven_costing.components.dialogs import confirm_dialog
from frontend.features.woven_costing.components.errors import attempt
from frontend.features.woven_costing.components.flash import set_flash, show_flash
from frontend.features.woven_costing.components.labels import dec, enum_values, index_of, num, text
from frontend.features.woven_costing.components.parameter_editor import parameter_sets_tab
from frontend.features.woven_costing.components.roles import has_any

NORM_CODE = "norm.code"
NORM_PREVIEW = "norm.preview"
# Screen 5 sub-tabs of the norm tables (2026-11-23), same names as the backend groups
NORM_GROUPS = ("Dệt", "Nhuộm HCM", "Nhuộm TCDN", "Danh mục chọn")


class NormParameterPage(BasePage):
    title = "Định mức và tham số"
    icon = "📐"
    slug = "dinh-muc"
    menu_group = "Phòng SO"
    description = "Bộ định mức, bộ tham số chung, hệ số theo mã hàng và ngày lễ."

    def render(self) -> None:
        show_flash(self.state)
        feature = gateway.open(WovenCostingController)
        is_so = has_any(RoleCode.SO.value)
        tabs = st.tabs(
            ["Bộ định mức", "Tham số chung", "Hệ số theo mã hàng", "Ngày lễ"], key=self.key("tabs"), on_change="rerun"
        )
        for tab, draw in zip(tabs, (self._norms, self._parameters, self._factors, self._holidays), strict=True):
            with tab:
                if tab.open:
                    draw(feature, is_so)

    # ---- Bộ định mức --------------------------------------------------------------------------------------------
    def _norms(self, feature: WovenCostingController, is_so: bool) -> None:
        data = feature.view_norm_set(ViewNormSetRequest(norm_set_code=self.state.get(NORM_CODE)))
        with panel("Danh sách bộ định mức", icon="📚"):
            picked = data_table(
                [
                    {
                        "Mã bộ": s.norm_set_code,
                        "Hiệu lực từ": s.effective_from,
                        "Ghi chú": s.note,
                        "Người tải": s.uploaded_by,
                        "Lúc tải": s.uploaded_at,
                        "Đang hiệu lực": s.is_current,
                    }
                    for s in data.sets
                ],
                column_config={
                    "Hiệu lực từ": st.column_config.DateColumn("Hiệu lực từ", format="DD/MM/YYYY"),
                    "Lúc tải": st.column_config.DatetimeColumn("Lúc tải", format="DD/MM/YYYY HH:mm"),
                    "Đang hiệu lực": st.column_config.CheckboxColumn("Đang hiệu lực"),
                },
                selection="single",
                key=self.key("norm.sets"),
                empty_message="Chưa có bộ định mức.",
            )
            st.caption("Chọn 1 bộ để xem các bảng (không chọn = bộ đang hiệu lực).")
        code = str(picked[0]["Mã bộ"]) if picked else None
        if code != self.state.get(NORM_CODE):
            self.state.set(NORM_CODE, code)
            st.rerun()
        if data.selected is not None and data.selected.tables:
            with panel(f"Các bảng của bộ {data.selected.norm_set_code}", icon="📊"):
                self._norm_tables(data.selected.norm_set_code, [*data.selected.tables, *data.selected.optional_tables])
        if is_so:
            self._norm_upload(feature)

    def _norm_tables(self, code: str, tables: list[NormTableDTO]) -> None:
        """4 sub-tabs (Dệt / Nhuộm HCM / Nhuộm TCDN / Danh mục chọn), every table drawn with its title (AC-58)."""
        groups = list(dict.fromkeys([*NORM_GROUPS, *(t.group for t in tables if t.group)]))
        tabs = st.tabs(groups, key=self.key(f"norm.groups.{code}"))
        for group, tab in zip(groups, tabs, strict=True):
            with tab:
                shown = [t for t in tables if (t.group or NORM_GROUPS[-1]) == group]
                if not shown:
                    empty_state("Bộ này chưa có bảng ở nhóm này.")
                for table in shown:
                    st.markdown(f"**{table.title}**")
                    data_table(table.rows, column_order=table.columns, empty_message="Bảng chưa có dòng.")

    def _norm_upload(self, feature: WovenCostingController) -> None:
        with panel("Cập nhật bộ định mức", icon="⬆️"):
            download_button(
                lambda: feature.download_norm_template(EmptyRequest()),
                label="Tải file mẫu",
                key=self.key("norm.template"),
                file_name=f"bo-dinh-muc-{date.today():%Y%m%d}.xlsx",
            )
            file = file_upload("Tải lên bộ định mức", types=[".xlsx"], key=self.key("norm.file"))
            c1, c2 = st.columns([1, 2])
            effective = c1.date_input("Ngày hiệu lực", format="DD/MM/YYYY", key=self.key("norm.effective"))
            note = c2.text_input("Ghi chú", max_chars=300, key=self.key("norm.note"))
            preview = self.state.get(NORM_PREVIEW)
            if preview is not None and (file is None or preview[0] != file.filename):
                self.state.pop(NORM_PREVIEW)
                preview = None
            if st.button("Kiểm tra", icon=":material/fact_check:", disabled=file is None, key=self.key("norm.check")):
                result = attempt(
                    lambda: feature.preview_norm_set(
                        SaveNormSetRequest(file=file, effective_from=effective, note=(note or "").strip())
                    )
                )
                if result is not None:
                    preview = (file.filename, result)
                    self.state.set(NORM_PREVIEW, preview)
            if preview is None or file is None:
                return
            p = preview[1]
            counts = [{"Sheet": c.sheet, "Số dòng": c.rows} for c in [*p.sheet_counts, *p.optional_sheet_counts]]
            data_table(counts)
            if not p.optional_sheet_counts:
                st.caption("File không có sheet Spandex: bảng Spandex cộng thêm giữ như bộ đang dùng.")
            data_table(
                [
                    {"Sheet": c.sheet, "Khóa": c.key, "Cột": c.column, "Giá trị cũ": c.old_value,
                     "Giá trị mới": c.new_value}
                    for c in p.changes
                ],
                empty_message="Không có ô thay đổi.",
            )  # fmt: skip
            for error in p.errors:
                st.error(error, icon="⚠️")
            if st.button(
                "Lưu bộ định mức",
                type="primary",
                icon=":material/save:",
                disabled=bool(p.errors),
                key=self.key("norm.save"),
            ):
                confirm_dialog(
                    self.state,
                    self.key("norm.save_dialog"),
                    "Lưu bộ định mức",
                    f"Lưu bộ định mức mới hiệu lực từ {effective:%d/%m/%Y}? "
                    "Costsheet đã gửi duyệt / đã duyệt không đổi số.",
                    "Lưu",
                    lambda _: (
                        feature.save_norm_set(
                            SaveNormSetRequest(file=file, effective_from=effective, note=(note or "").strip())
                        ).message,
                        [],
                    ),
                    on_done=lambda: self.state.pop(NORM_PREVIEW),
                )

    # ---- Tham số chung ------------------------------------------------------------------------------------------
    def _parameters(self, feature: WovenCostingController, is_so: bool) -> None:
        """Pick a set, 5 sub-tabs by department, "Lưu bộ tham số mới" (2026-11-25)."""
        parameter_sets_tab(self, feature, is_so)

    # ---- Hệ số theo mã hàng -------------------------------------------------------------------------------------
    def _factors(self, feature: WovenCostingController, is_so: bool) -> None:
        rows = feature.list_fabric_factors(EmptyRequest()).rows
        picked = data_table(
            [
                {
                    "id": f.id,
                    "Mã vải": f.tcfno,
                    "Công đoạn": text(f.stage),
                    "Khoản mục": text(f.cost_item),
                    "Hệ số nhân": num(f.multiplier),
                    "Cộng thêm": num(f.addition),
                    "Hiệu lực từ": f.effective_from,
                    "Đang dùng": f.active,
                    "Ghi chú": f.note,
                }
                for f in rows
            ],
            column_config={
                "Hệ số nhân": st.column_config.NumberColumn("Hệ số nhân", format="%.4f"),
                "Cộng thêm": st.column_config.NumberColumn("Cộng thêm", format="localized"),
                "Hiệu lực từ": st.column_config.DateColumn("Hiệu lực từ", format="DD/MM/YYYY"),
                "Đang dùng": st.column_config.CheckboxColumn("Đang dùng"),
            },
            column_order=[
                "Mã vải",
                "Công đoạn",
                "Khoản mục",
                "Hệ số nhân",
                "Cộng thêm",
                "Hiệu lực từ",
                "Đang dùng",
                "Ghi chú",
            ],  # fmt: skip
            selection="single",
            key=self.key("factor.grid"),
            empty_message="Chưa có hệ số theo mã hàng.",
        )
        if not is_so:
            return
        chosen = next((f for f in rows if picked and f.id == picked[0]["id"]), None)
        with st.container(horizontal=True, gap="small"):
            add = st.button("Thêm", icon=":material/add:", key=self.key("factor.add"))
            edit = st.button("Sửa", icon=":material/edit:", disabled=chosen is None, key=self.key("factor.edit"))
            stop = st.button(
                "Ngừng dùng",
                icon=":material/block:",
                disabled=chosen is None or not chosen.active,
                key=self.key("factor.stop"),
            )
        if add:
            self._factor_dialog(feature, None)
        if edit and chosen is not None:
            self._factor_dialog(feature, chosen)
        if stop and chosen is not None:
            saved = attempt(
                lambda: feature.save_fabric_factor(
                    SaveFabricFactorRequest(**chosen.model_dump(exclude={"active"}), active=False)
                )
            )
            if saved is not None:
                set_flash(self.state, saved.message)
                st.rerun()

    def _factor_dialog(self, feature: WovenCostingController, factor: FabricFactorDTO | None) -> None:
        user = get_current_user()
        stages, items = enum_values(FactorStage), enum_values(CostItem)

        @st.dialog("Hệ số theo mã hàng", width="medium")
        def _dialog() -> None:
            set_current_user(user)
            key = self.key(f"factor.dialog.{factor.id if factor else 'new'}")
            tcfno = st.text_input("Mã vải", value=factor.tcfno if factor else "", max_chars=30, key=f"{key}.tcfno")
            c1, c2 = st.columns(2)
            stage = c1.selectbox(
                "Công đoạn", stages, index=index_of(stages, text(factor.stage)) if factor else 0, key=f"{key}.stage"
            )
            item = c2.selectbox(
                "Khoản mục", items, index=index_of(items, text(factor.cost_item)) if factor else 0, key=f"{key}.item"
            )
            multiplier = c1.number_input(
                "Hệ số nhân", min_value=0.0001, value=num(factor.multiplier) if factor else 1.0, format="%.4f",
                key=f"{key}.mult",
            )  # fmt: skip
            addition = c2.number_input("Cộng thêm", value=num(factor.addition) if factor else 0.0, key=f"{key}.add")
            effective = c1.date_input(
                "Hiệu lực từ", value=factor.effective_from if factor else date.today(), format="DD/MM/YYYY",
                key=f"{key}.eff",
            )  # fmt: skip
            with c2:
                active = st.toggle("Đang dùng", value=factor.active if factor else True, key=f"{key}.active")
            note = st.text_input("Ghi chú", value=factor.note if factor else "", max_chars=300, key=f"{key}.note")
            if st.button("Lưu", type="primary", icon=":material/save:", key=f"{key}.save"):
                saved = attempt(
                    lambda: feature.save_fabric_factor(
                        SaveFabricFactorRequest(
                            id=factor.id if factor else None,
                            tcfno=(tcfno or "").strip(),
                            stage=stage,
                            cost_item=item,
                            multiplier=dec(multiplier),
                            addition=dec(addition) or dec(0),
                            effective_from=effective,
                            active=active,
                            note=(note or "").strip(),
                        )
                    )
                )
                if saved is not None:
                    set_flash(self.state, saved.message)
                    st.rerun()

        _dialog()

    # ---- Ngày lễ ------------------------------------------------------------------------------------------------
    def _holidays(self, feature: WovenCostingController, is_so: bool) -> None:
        rows = feature.list_holidays(EmptyRequest()).rows
        picked = data_table(
            [{"Ngày": h.date, "Tên ngày lễ": h.name} for h in rows],
            column_config={"Ngày": st.column_config.DateColumn("Ngày", format="DD/MM/YYYY")},
            selection="single",
            key=self.key("holiday.grid"),
            empty_message="Chưa có ngày lễ.",
        )
        if not is_so:
            return
        with st.form(self.key("holiday.form"), clear_on_submit=True):
            c1, c2 = st.columns([1, 2])
            day = c1.date_input("Ngày", format="DD/MM/YYYY", key=self.key("holiday.date"))
            name = c2.text_input("Tên ngày lễ", max_chars=100, key=self.key("holiday.name"))
            add = st.form_submit_button("Thêm", type="primary", icon=":material/add:")
        if add:
            saved = attempt(
                lambda: feature.save_holiday(
                    SaveHolidayRequest(action=HolidayAction.ADD, date=day, name=(name or "").strip())
                )
            )
            if saved is not None:
                set_flash(self.state, saved.message or "Đã thêm ngày lễ.")
                st.rerun()
        if st.button("Xóa", icon=":material/delete:", disabled=not picked, key=self.key("holiday.delete")) and picked:
            day_picked = picked[0]["Ngày"]
            day_picked = day_picked.date() if hasattr(day_picked, "date") else day_picked
            chosen = next((h for h in rows if h.date == day_picked and h.name == picked[0]["Tên ngày lễ"]), None)
            if chosen is not None:
                saved = attempt(
                    lambda: feature.save_holiday(
                        SaveHolidayRequest(action=HolidayAction.DELETE, date=chosen.date, name=chosen.name)
                    )
                )
                if saved is not None:
                    set_flash(self.state, saved.message or "Đã xóa ngày lễ.")
                    st.rerun()
