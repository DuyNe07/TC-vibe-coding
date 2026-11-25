"""Screen 5 - thẻ Tham số chung (2026-11-25): pick a set, 5 sub-tabs by department (single values + discount table /
% B/C table, edited like Excel), "Lưu bộ tham số mới" for Phòng SO."""

from datetime import date
from typing import Any

import streamlit as st

from backend.core.base import EmptyRequest
from backend.features.woven_costing import WovenCostingController
from backend.features.woven_costing.dto.common_dto import DiscountCondition, DiscountDepartment, ParamGroup, SaleForm
from backend.features.woven_costing.dto.master_dto import (
    BcRowDTO,
    DiscountRowDTO,
    OpRateRowDTO,
    ParameterSetDetailDTO,
    ParameterValueDTO,
    ParameterValueInputDTO,
    SaveParameterSetRequest,
)
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, editable_table, empty_state, panel, section_title
from frontend.features.woven_costing.components.errors import attempt
from frontend.features.woven_costing.components.flash import set_flash
from frontend.features.woven_costing.components.labels import dec, enum_values, from_pct, num, text, to_pct

# sub-tab -> department of its discount table (None = no discount table)
GROUP_DEPARTMENT = {
    ParamGroup.YARN.value: None,
    ParamGroup.WEAVING.value: DiscountDepartment.WEAVING.value,
    ParamGroup.HCM.value: DiscountDepartment.HCM.value,
    ParamGroup.TCDN.value: DiscountDepartment.TCDN.value,
    ParamGroup.PRICE.value: None,
}
VALUE_CONFIG = {
    "Giá trị": st.column_config.NumberColumn("Giá trị", format="%.4f"),
    "Chỉ SO": st.column_config.CheckboxColumn("Chỉ SO"),
}
VALUE_ORDER = ["Tham số", "Đơn vị", "Giá trị", "Chỉ SO"]
DISCOUNT_CONFIG = {
    "Điều kiện": st.column_config.SelectboxColumn("Điều kiện", options=enum_values(DiscountCondition), required=True),
    "Từ": st.column_config.NumberColumn("Từ", min_value=0, format="%.0f", help="Trống = không giới hạn dưới"),
    "Tính đúng mốc Từ (≥)": st.column_config.CheckboxColumn("Tính đúng mốc Từ (≥)", help="Bỏ tick = lớn hơn (>)"),
    "Đến": st.column_config.NumberColumn("Đến", min_value=0, format="%.0f", help="Trống = không giới hạn trên"),
    "Tính đúng mốc Đến (≤)": st.column_config.CheckboxColumn("Tính đúng mốc Đến (≤)", help="Bỏ tick = nhỏ hơn (<)"),
    "Hệ số": st.column_config.NumberColumn("Hệ số", min_value=0, format="%.4f"),
    "Đơn vị": st.column_config.TextColumn("Đơn vị", width="small"),
    "Chia đều": st.column_config.CheckboxColumn("Chia đều", help="Chỉ có ở bộ cũ (cách tính file Excel)"),
    "Áp dụng cho": st.column_config.TextColumn("Áp dụng cho", width="medium"),
}
DISCOUNT_ORDER = list(DISCOUNT_CONFIG)
DISCOUNT_LOCKED = ["Đơn vị", "Chia đều", "Áp dụng cho"]
BC_CONFIG = {
    "Hình thức bán": st.column_config.SelectboxColumn("Hình thức bán", options=enum_values(SaleForm), required=True),
    "% B/C mộc": st.column_config.NumberColumn("% B/C mộc", min_value=0, max_value=99.99, format="%.2f"),
    "% B/C thành phẩm": st.column_config.NumberColumn("% B/C thành phẩm", min_value=0, max_value=99.99, format="%.2f"),
}


def _value_row(p: ParameterValueDTO) -> dict[str, Any]:
    return {
        "code": p.code,
        "Tham số": p.label,
        "Đơn vị": "%" if p.is_percent else p.unit,
        "Giá trị": to_pct(p.default_value) if p.is_percent else num(p.default_value),
        "Chỉ SO": p.so_only,
    }


def _discount_row(r: DiscountRowDTO) -> dict[str, Any]:
    return {
        "Điều kiện": text(r.condition),
        "Từ": num(r.from_qty),
        "Tính đúng mốc Từ (≥)": r.from_inclusive,
        "Đến": num(r.to_qty),
        "Tính đúng mốc Đến (≤)": r.to_inclusive,
        "Hệ số": num(r.factor),
        "Đơn vị": text(r.quantity_unit),
        "Chia đều": r.interpolate,
        "Áp dụng cho": r.applies_to,
    }


def _discount_dto(department: str, row: dict[str, Any]) -> DiscountRowDTO | None:
    """Edited row -> DTO; an empty new row is skipped, a missing factor is sent as 0 (refused by BR-88)."""
    cells = ("Từ", "Đến", "Hệ số")
    if not row.get("Điều kiện") and all(row.get(c) is None for c in cells):
        return None
    return DiscountRowDTO(
        department=DiscountDepartment(department),
        condition=DiscountCondition(row.get("Điều kiện") or DiscountCondition.MASS.value),
        from_qty=dec(row.get("Từ")),
        from_inclusive=bool(row.get("Tính đúng mốc Từ (≥)")),
        to_qty=dec(row.get("Đến")),
        to_inclusive=bool(row.get("Tính đúng mốc Đến (≤)")),
        factor=dec(row.get("Hệ số")) or dec(0),
    )


def _bc_row(r: BcRowDTO) -> dict[str, Any]:
    return {
        "Hình thức bán": text(r.sale_form),
        "% B/C mộc": to_pct(r.greige_bc_rate),
        "% B/C thành phẩm": to_pct(r.finished_bc_rate),
    }


def _bc_dto(row: dict[str, Any]) -> BcRowDTO | None:
    if not row.get("Hình thức bán"):
        return None
    return BcRowDTO(
        sale_form=SaleForm(row["Hình thức bán"]),
        greige_bc_rate=from_pct(row.get("% B/C mộc")) or dec(0),
        finished_bc_rate=from_pct(row.get("% B/C thành phẩm")) or dec(0),
    )


class ParameterSetEditor:
    """Draws one set in 5 sub-tabs and collects what SO typed (edited cells come back at every rerun)."""

    def __init__(self, page: BasePage, detail: ParameterSetDetailDTO, editable: bool) -> None:
        self.page = page
        self.detail = detail
        self.editable = editable
        self.version = detail.effective_from.isoformat()
        self.values: list[ParameterValueInputDTO] = []
        self.discount_rows: list[DiscountRowDTO] = []
        self.bc_rows: list[BcRowDTO] = []
        self.op_rates: list[OpRateRowDTO] = []

    def key(self, name: str) -> str:
        return self.page.key(f"param.{self.version}.{name}")

    def draw(self) -> None:
        groups = enum_values(ParamGroup)
        for group, tab in zip(groups, st.tabs(groups, key=self.key("groups")), strict=True):
            with tab:
                self._values(group)
                department = GROUP_DEPARTMENT[group]
                if department is not None:
                    self._discounts(department)
                if group == ParamGroup.PRICE.value:
                    self._bc()
                if group == ParamGroup.TCDN.value:
                    self._op_rates()

    def _values(self, group: str) -> None:
        params = [p for p in self.detail.values if text(p.group) == group]
        if not params:
            return
        section_title("Tham số")
        rows = [_value_row(p) for p in params]
        if not self.editable:
            data_table(rows, column_config=VALUE_CONFIG, column_order=VALUE_ORDER)
            return
        edited = editable_table(rows, key=self.key(f"values.{group}"), column_config=VALUE_CONFIG,
                                column_order=VALUE_ORDER, disabled=["code", "Tham số", "Đơn vị", "Chỉ SO"])  # fmt: skip
        percent = {p.code: p.is_percent for p in params}
        for row in edited:
            value = from_pct(row.get("Giá trị")) if percent[row["code"]] else dec(row.get("Giá trị"))
            self.values.append(ParameterValueInputDTO(code=row["code"], value=value or dec(0)))

    def _discounts(self, department: str) -> None:
        section_title("Bảng discount theo sản lượng")
        rows = [_discount_row(r) for r in self.detail.discount_rows if text(r.department) == department]
        if not self.editable:
            data_table(rows, column_config=DISCOUNT_CONFIG, column_order=DISCOUNT_ORDER,
                       empty_message="Chưa có dòng discount.")  # fmt: skip
            return
        edited = editable_table(rows, key=self.key(f"discount.{department}"), columns=DISCOUNT_ORDER,
                                column_config=DISCOUNT_CONFIG, column_order=DISCOUNT_ORDER, disabled=DISCOUNT_LOCKED,
                                allow_add_delete=True)  # fmt: skip
        self.discount_rows += [dto for row in edited if (dto := _discount_dto(department, row)) is not None]
        st.caption("Thêm / xóa dòng ngay trong bảng. Bộ mới tính theo bậc (không chia đều giữa mốc).")

    def _bc(self) -> None:
        section_title("Bảng % B/C theo hình thức bán")
        rows = [_bc_row(r) for r in self.detail.bc_rows]
        if not self.editable:
            data_table(rows, column_config=BC_CONFIG)
            return
        edited = editable_table(rows, key=self.key("bc"), columns=list(BC_CONFIG), column_config=BC_CONFIG,
                                allow_add_delete=True)  # fmt: skip
        self.bc_rows += [dto for row in edited if (dto := _bc_dto(row)) is not None]

    def _op_rates(self) -> None:
        """4.24 (2026-11-25): operation rate of the TCDN stages, used by the dyeing job orders only (BR-93)."""
        section_title("Hệ số vận hành công đoạn (chỉ dùng cho phiếu gia công nhuộm)")
        rows = [{"Công đoạn": r.stage, "Hệ số vận hành": float(r.rate)} for r in self.detail.op_rates]
        config = {"Hệ số vận hành": st.column_config.NumberColumn("Hệ số vận hành", min_value=0.01, max_value=1.0,
                                                                   format="%.2f")}  # fmt: skip
        if not self.editable:
            data_table(rows, column_config=config, empty_message="Chưa có hệ số vận hành.")
            return
        edited = editable_table(rows, key=self.key("op_rates"), columns=["Công đoạn", "Hệ số vận hành"],
                                column_config=config, allow_add_delete=True)  # fmt: skip
        self.op_rates += [OpRateRowDTO(stage=str(r["Công đoạn"]).strip(), rate=dec(r["Hệ số vận hành"]) or dec(1))
                          for r in edited if r.get("Công đoạn")]  # fmt: skip
        st.caption("Công đoạn không có trong bảng: hệ số = 1. Chi phí (trừ hóa chất) chia cho hệ số này.")


def parameter_sets_tab(page: BasePage, feature: WovenCostingController, is_so: bool) -> None:
    data = feature.list_parameter_sets(EmptyRequest())
    with panel("Các bộ tham số", icon="🗂️"):
        data_table(
            [{"Hiệu lực từ": s.effective_from, "Người lưu": s.created_by, "Lúc lưu": s.created_at} for s in data.sets],
            column_config={
                "Hiệu lực từ": st.column_config.DateColumn("Hiệu lực từ", format="DD/MM/YYYY"),
                "Lúc lưu": st.column_config.DatetimeColumn("Lúc lưu", format="DD/MM/YYYY HH:mm"),
            },
            empty_message="Chưa có bộ tham số.",
        )
    if not data.details:
        empty_state("Chưa có bộ tham số.")
        return
    dates = [d.effective_from for d in data.details]
    picked: date = st.selectbox(
        "Xem bộ tham số hiệu lực từ", dates, index=0, format_func=lambda d: f"{d:%d/%m/%Y}", key=page.key("param.view")
    )
    detail = next(d for d in data.details if d.effective_from == picked)
    if detail.from_old_values:
        st.caption("Bộ này lưu trước 25/11/2026: bảng discount Dệt chia đều giữa mốc như file Excel cũ.")
    if is_so:
        st.caption('Sửa ngay trong các bảng dưới đây rồi chọn ngày hiệu lực và bấm "Lưu bộ tham số mới".')
    editor = ParameterSetEditor(page, detail, is_so)
    editor.draw()
    if not is_so:
        return
    with panel("Lưu bộ tham số mới", icon="✏️"):
        effective = st.date_input("Ngày hiệu lực", format="DD/MM/YYYY", key=page.key("param.effective"))
        if st.button("Lưu bộ tham số mới", type="primary", icon=":material/save:", key=page.key("param.save")):
            request = SaveParameterSetRequest(
                effective_from=effective,
                values=editor.values,
                discount_rows=editor.discount_rows,
                bc_rows=editor.bc_rows,
                op_rates=editor.op_rates,
            )
            saved = attempt(lambda: feature.save_parameter_set(request))
            if saved is not None:
                set_flash(page.state, saved.message)
                st.rerun()
