"""Fabric forms: "Thêm / Sửa mã vải" (Screen 4, UC-02) and "Sửa thông số vải" of a costsheet (Screen 2, UC-14)."""

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

import streamlit as st

from backend.core.current_user import get_current_user, set_current_user
from backend.features.woven_costing import WovenCostingController
from backend.features.woven_costing.dto.costsheet_dto import CostsheetResponse, UpdateFabricOverrideRequest
from backend.features.woven_costing.dto.fabric_dto import (
    FabricDetailDTO,
    FabricSpecsDTO,
    FabricYarnDTO,
    SaveFabricRequest,
)
from frontend.core.base_page import BasePage
from frontend.core.components import editable_table
from frontend.features.woven_costing.components.errors import attempt
from frontend.features.woven_costing.components.fabric_view import (
    DIRECTION_OPTIONS,
    SPEC_FIELDS,
    YARN_KIND_OPTIONS,
)
from frontend.features.woven_costing.components.flash import set_flash
from frontend.features.woven_costing.components.labels import dec, from_pct, num, text, text_or_empty, to_pct
from frontend.features.woven_costing.components.working import replace_working

YARN_COLUMNS = ["Hướng", "Tên sợi", "Tỷ lệ (%)", "Loại sợi", "Sợi gốc", "Tỷ lệ sợi gốc (%)", "T/M"]
HIDDEN_COLUMNS = ["full_yarn_name", "yarn_code", "raw_yarn_code"]
DEFAULT_WARPING_LOSS_PCT = 10.0


def spec_inputs(key: str, specs: FabricSpecsDTO | None) -> dict[str, Decimal | None]:
    """Number boxes Mộc / Thành phẩm -> {field: value} of FabricSpecsDTO."""
    values: dict[str, Decimal | None] = {}
    for column, prefix, title in zip(st.columns(2), ("greige", "finished"), ("Mộc", "Thành phẩm"), strict=True):
        with column:
            st.markdown(f"**{title}**")
            for label, field in SPEC_FIELDS:
                name = f"{prefix}_{field}"
                current = num(getattr(specs, name)) if specs is not None else None
                values[name] = dec(st.number_input(label, min_value=0.0, value=current, key=f"{key}.{name}"))
    return values


def yarn_editor(key: str, yarns: Sequence[FabricYarnDTO]) -> list[dict[str, Any]]:
    """Yarn rows edited like Excel -> kwargs of FabricYarnDTO (empty rows dropped, STT numbered per direction)."""
    rows = [
        {
            "Hướng": text(y.direction),
            "Tên sợi": y.yarn_name,
            "Tỷ lệ (%)": num(y.rate),
            "Loại sợi": text(y.yarn_kind) or None,
            "Sợi gốc": y.raw_yarn_name,
            "Tỷ lệ sợi gốc (%)": num(y.raw_rate),
            "T/M": y.twist_tpm,
            "full_yarn_name": y.full_yarn_name,
            "yarn_code": y.yarn_code,
            "raw_yarn_code": y.raw_yarn_code,
        }
        for y in yarns
    ]
    edited = editable_table(
        rows,
        key=key,
        columns=[*YARN_COLUMNS, *HIDDEN_COLUMNS],
        column_order=YARN_COLUMNS,
        column_config={
            "Hướng": st.column_config.SelectboxColumn("Hướng", options=DIRECTION_OPTIONS, required=True),
            "Tên sợi": st.column_config.TextColumn("Tên sợi", width="large"),
            "Tỷ lệ (%)": st.column_config.NumberColumn("Tỷ lệ (%)", min_value=0, max_value=100, format="%.2f"),
            "Loại sợi": st.column_config.SelectboxColumn("Loại sợi", options=YARN_KIND_OPTIONS),
            "Tỷ lệ sợi gốc (%)": st.column_config.NumberColumn(
                "Tỷ lệ sợi gốc (%)", min_value=0, max_value=100, format="%.2f"
            ),
        },
        allow_add_delete=True,
    )
    result: list[dict[str, Any]] = []
    counters: dict[Any, int] = {}
    for row in edited:
        if all(row.get(column) in (None, "") for column in YARN_COLUMNS):
            continue
        direction = row.get("Hướng")
        counters[direction] = counters.get(direction, 0) + 1
        result.append(
            {
                "direction": direction,
                "seq": counters[direction],
                "full_yarn_name": text_or_empty(row.get("full_yarn_name")),
                "yarn_code": text_or_empty(row.get("yarn_code")),
                "yarn_name": text_or_empty(row.get("Tên sợi")),
                "rate": dec(row.get("Tỷ lệ (%)")) or Decimal(0),
                "yarn_kind": row.get("Loại sợi") or None,
                "raw_yarn_code": text_or_empty(row.get("raw_yarn_code")),
                "raw_yarn_name": text_or_empty(row.get("Sợi gốc")),
                "raw_rate": dec(row.get("Tỷ lệ sợi gốc (%)")),
                "twist_tpm": text_or_empty(row.get("T/M")),
            }
        )
    return result


def fabric_dialog(page: BasePage, feature: WovenCostingController, detail: FabricDetailDTO | None) -> None:
    """UC-02 Thêm / Sửa mã vải nhập tay."""
    user = get_current_user()
    title = "Thêm mã vải" if detail is None else f"Sửa mã vải {detail.tcfno}"

    @st.dialog(title, width="large")
    def _dialog() -> None:
        set_current_user(user)
        key = page.key(f"fabric_dialog.{detail.tcfno if detail else 'new'}")
        c1, c2 = st.columns([1, 2])
        tcfno = c1.text_input(
            "Mã vải",
            value=detail.tcfno if detail else "",
            max_chars=30,
            disabled=detail is not None,
            key=f"{key}.tcfno",
        )
        name = c2.text_input("Tên vải", value=detail.fabric_name if detail else "", max_chars=300, key=f"{key}.name")
        c3, c4 = st.columns([1, 2])
        warping_default = (
            to_pct(detail.warping_loss_rate)
            if detail is not None and detail.warping_loss_rate is not None
            else DEFAULT_WARPING_LOSS_PCT
        )
        warping = c3.number_input(
            "Độ co mắc (%)", min_value=0.0, max_value=99.99, value=warping_default, format="%.2f", key=f"{key}.warp"
        )
        remark = c4.text_input(
            "Ghi chú (Remark)", value=detail.remark if detail else "", max_chars=300, key=f"{key}.rm"
        )
        specs = spec_inputs(key, detail)
        st.markdown("**Các dòng sợi**")
        yarns = yarn_editor(f"{key}.yarns", detail.yarns if detail else [])
        if st.button("Lưu mã vải", type="primary", icon=":material/save:", key=f"{key}.save"):
            saved = attempt(
                lambda: feature.save_fabric(
                    SaveFabricRequest(
                        is_new=detail is None,
                        tcfno=(tcfno or "").strip(),
                        fabric_name=(name or "").strip(),
                        remark=(remark or "").strip(),
                        warping_loss_rate=from_pct(warping),
                        yarns=[FabricYarnDTO(**y) for y in yarns],
                        **specs,
                    )
                )
            )
            if saved is not None:
                set_flash(page.state, saved.message)
                st.rerun()

    _dialog()


def override_dialog(page: BasePage, feature: WovenCostingController, working: CostsheetResponse) -> None:
    """UC-14 Sửa thông số vải của một costsheet (mã nhập tay, Nháp / Trả lại)."""
    user = get_current_user()
    fabric = working.fabric

    @st.dialog("Sửa thông số vải", width="large")
    def _dialog() -> None:
        set_current_user(user)
        key = page.key(f"override.{working.id}.{page.state.get('cs.rev', 0)}")
        warping = st.number_input(
            "Độ co mắc (%)",
            min_value=0.0,
            max_value=99.99,
            value=to_pct(fabric.warping_loss_rate) if fabric and fabric.warping_loss_rate is not None else None,
            format="%.2f",
            key=f"{key}.warp",
        )
        specs = spec_inputs(key, fabric)
        st.markdown("**Các dòng sợi**")
        yarns = yarn_editor(f"{key}.yarns", fabric.yarns if fabric else [])
        if st.button("Lưu và tính lại", type="primary", icon=":material/calculate:", key=f"{key}.save"):
            response = attempt(
                lambda: feature.update_fabric_override(
                    UpdateFabricOverrideRequest(
                        costsheet_id=working.id,
                        specs=FabricSpecsDTO(**specs, warping_loss_rate=from_pct(warping)),
                        yarns=[FabricYarnDTO(**y) for y in yarns],
                    )
                )
            )
            if response is not None:
                replace_working(page.state, response)
                set_flash(
                    page.state,
                    response.message or f"Đã cập nhật thông số vải cho costsheet {response.costsheet_no}.",
                    response.warning_texts,
                )
                st.rerun()

    _dialog()
