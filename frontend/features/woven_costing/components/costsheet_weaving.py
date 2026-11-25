"""Screen 2 tab "Ngành Dệt" (block D): Se lines, sizing / warping / cone / outsourcing choices, stage costs."""

from typing import Any

import streamlit as st

from backend.features.woven_costing.dto.common_dto import FiberSystem, SaleForm
from backend.features.woven_costing.dto.costsheet_dto import CostsheetResponse
from backend.features.woven_costing.dto.list_dto import CostsheetOptionsResponse
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, editable_table, section_title, stat_row
from frontend.core.formatting import format_number
from frontend.features.woven_costing.components.labels import (
    FLAG,
    dec,
    enum_values,
    index_of,
    num,
    text,
    text_or_empty,
    with_value,
)

TWIST_DIRECTIONS = ["Dọc", "Ngang"]
TWIST_COLUMNS = ["Hướng", "Hệ sợi", "Chi số", "Độ săn", "SL yêu cầu (kg)"]
# hidden cells: the fiber system shown first and whether it was the app suggestion (BR-83)
AUTO, FIBER_SHOWN = "_auto", "_fiber"
# hidden cells (BR-86): the line is the app suggestion + the suggestion it came from (the app compares the cells)
SUGGESTED, SUGGESTION_KEY = "_suggested", "_suggestion"
CHECK = "✓"
YES_NO = ["Có", "Không"]
MONEY = st.column_config.NumberColumn(format="localized")


def _number(column: Any, label: str, value: Any, key: str, disabled: bool, help: str | None = None) -> Any:
    return dec(column.number_input(label, min_value=0.0, step=100.0, value=num(value), key=key, disabled=disabled,
                                   help=help))  # fmt: skip


def _twist_lines(page: BasePage, w: CostsheetResponse, sfx: str) -> Any:
    """Se lines like the Excel sheet: fiber system, count and twist prefilled by the app (BR-83, BR-86), typed freely
    (BR-81, BR-82); the converted count is not shown."""
    rows = [
        {
            "Hướng": t.direction,
            "Hệ sợi": text(t.fiber_system) or None,
            "Chi số": t.count or None,
            "Độ săn": t.twist,
            "SL yêu cầu (kg)": num(t.quantity_kg),
            AUTO: t.fiber_suggested,
            FIBER_SHOWN: text(t.fiber_system) or None,
            SUGGESTED: t.suggested,
            SUGGESTION_KEY: t.suggestion_key or None,
        }
        for t in w.input.twist_lines
    ]
    config = {
        "Hướng": st.column_config.SelectboxColumn("Hướng", options=TWIST_DIRECTIONS, required=True),
        "Hệ sợi": st.column_config.SelectboxColumn(
            "Hệ sợi", options=enum_values(FiberSystem), help="App gợi ý theo chi số; chọn lại nếu sai."
        ),
        "Chi số": st.column_config.TextColumn(
            "Chi số", help="Ví dụ: 75D/2 + CB, 30/2, 45 + 75D + SP 70", required=True
        ),
        "Độ săn": st.column_config.NumberColumn("Độ săn (T/M)", min_value=0, step=1, format="%d", required=True),
        "SL yêu cầu (kg)": st.column_config.NumberColumn("SL yêu cầu (kg)", min_value=0, format="%.2f", required=True),
    }
    if not w.editable:
        data_table(rows, column_config=config, column_order=TWIST_COLUMNS, empty_message="Không có dòng Se.")
        return None
    edited = editable_table(
        rows,
        key=page.key(f"twist.{sfx}"),
        columns=[*TWIST_COLUMNS, AUTO, FIBER_SHOWN, SUGGESTED, SUGGESTION_KEY],
        column_config=config,
        column_order=TWIST_COLUMNS,
        allow_add_delete=True,
    )
    return [
        {
            "direction": r.get("Hướng") or "",
            "fiber_system": r.get("Hệ sợi") or None,
            "count": text_or_empty(r.get("Chi số")),
            "twist": int(r["Độ săn"]) if r.get("Độ săn") is not None else None,
            "quantity_kg": dec(r.get("SL yêu cầu (kg)")),
            "fiber_suggested": bool(r.get(AUTO)) and r.get("Hệ sợi") == r.get(FIBER_SHOWN),
            "suggested": bool(r.get(SUGGESTED)),
            "suggestion_key": text_or_empty(r.get(SUGGESTION_KEY)),
        }
        for r in edited
        if any(r.get(c) not in (None, "") for c in TWIST_COLUMNS)
    ]


def _choices(page: BasePage, w: CostsheetResponse, options: CostsheetOptionsResponse, sfx: str) -> dict[str, Any]:
    weave = w.input.weaving
    off = not w.editable

    def key(name: str) -> str:
        return page.key(f"weave.{name}.{sfx}")

    sizes = with_value(options.size_materials, weave.size_material)
    count_help = "Gõ chi số, ví dụ 150D, 75D/2 + CB, 30/2"
    c1, c2, c3, c4 = st.columns(4)
    size_material = c1.selectbox(
        "Nguyên liệu hồ", sizes, index=index_of(sizes, weave.size_material), placeholder="Không hồ",
        key=key("size"), disabled=off,
    )  # fmt: skip
    c1.caption(f"Nhóm tổng canh: {w.result.size_band or '-'}")
    with c2:
        band = st.segmented_control(
            "Mắc phân băng", YES_NO, default=weave.warping_band or None, key=key("band"), disabled=off
        )
    cone_1 = c3.text_input(
        "Chi số cone 1", value=weave.cone_count_1, max_chars=60, key=key("cone1"), disabled=off, help=count_help
    )
    cone_qty_1 = _number(
        c4, "SL cone 1 (kg)", weave.cone_qty_1, key("cone1_qty"), off,
        "App điền sẵn tổng SL Se ngang và tự cập nhật theo Se ngang tới khi bạn sửa ô này.",
    )  # fmt: skip
    if weave.cone_qty_1_suggested or weave.cone_count_1_suggested:
        c3.caption("Cone 1 được điền sẵn theo các dòng Se ngang.")
    c1, c2, c3, c4 = st.columns(4)
    cone_2 = c3.text_input(
        "Chi số cone 2", value=weave.cone_count_2, max_chars=60, key=key("cone2"), disabled=off, help=count_help
    )
    cone_qty_2 = _number(c4, "SL cone 2 (kg)", weave.cone_qty_2, key("cone2_qty"), off)
    twist_price = _number(c1, "Gia công Se (đ/kg)", weave.twist_outsourcing_price, key("twist_price"), off)
    twist_qty = _number(c2, "SL gia công Se (kg)", weave.twist_outsourcing_qty, key("twist_qty"), off)
    c1, c2, c3, _ = st.columns(4)
    size_price = _number(c1, "Gia công Hồ (đ/m)", weave.size_outsourcing_price, key("size_price"), off)
    weaving_price = _number(c2, "Gia công Dệt (đ/m)", weave.weaving_outsourcing_price, key("weave_price"), off)
    other_price = _number(c3, "Chi phí gia công khác (đ/m)", weave.other_outsourcing_price, key("other_price"), off)
    return {
        "size_material": size_material or "",
        "warping_band": band or "",
        "cone_count_1": (cone_1 or "").strip(),
        "cone_qty_1": cone_qty_1,
        # BR-87: the cell keeps following the Se lines while it still shows the suggestion
        "cone_count_1_suggested": weave.cone_count_1_suggested and (cone_1 or "").strip() == weave.cone_count_1,
        "cone_qty_1_suggested": weave.cone_qty_1_suggested and num(cone_qty_1) == num(weave.cone_qty_1),
        "cone_count_2": (cone_2 or "").strip(),
        "cone_qty_2": cone_qty_2,
        "twist_outsourcing_price": twist_price,
        "twist_outsourcing_qty": twist_qty,
        "size_outsourcing_price": size_price,
        "weaving_outsourcing_price": weaving_price,
        "other_outsourcing_price": other_price,
    }


def weaving_tab(
    page: BasePage, w: CostsheetResponse, options: CostsheetOptionsResponse, sfx: str, sale_form: str | None
) -> tuple[Any, Any]:
    """Returns (twist_lines, weaving) inputs; None = keep the stored values."""
    r = w.result
    twist_lines = weaving = None
    reason = f" ({r.quantity_factor_reason})" if r.quantity_factor_reason else ""
    stat_row(
        [
            ("Số mét mộc", format_number(r.greige_meters)),
            ("Hệ số số lượng", f"{format_number(r.quantity_factor, 3)}{reason}",
             "Nhân vào Mắc Hồ, Mắc phân băng, Cone, Dệt, Kiểm"),
        ]
    )  # fmt: skip
    if sale_form == SaleForm.DYED.value:
        st.info("Vải Nhuộm: chi phí ngành Dệt = 0, dùng giá mộc mua ngoài.", icon=":material/info:")
    else:
        section_title("Dòng Se")
        twist_lines = _twist_lines(page, w, sfx)
        st.caption(
            "Tối đa 9 dòng Se dọc và 9 dòng Se ngang. Hệ sợi, chi số, độ săn được gợi ý sẵn, sửa lại được. "
            "Ví dụ cách ghi: 75D/2 + CB, 30/2, 45 + 75D + SP 70."
        )
        stat_row(
            [
                ("Sản lượng Se ước tính (kg)", format_number(r.twist_estimated_kg, 2)),
                ("Tổng SL Se nhập (kg)", format_number(r.twist_entered_kg, 2)),
                ("Chênh lệch (kg)", format_number(r.twist_difference_kg, 2)),
            ]
        )
        for line in r.twist_lines:
            if line.error:
                st.warning(f"Se {line.direction} {line.count}: {line.error}", icon="⚠️")
        section_title("Hồ, mắc, cone, gia công")
        weaving = _choices(page, w, options, sfx)
    section_title("Chi phí công đoạn")
    data_table(
        [
            {
                "Công đoạn": s.stage,
                "SL": num(s.quantity),
                "Đơn vị": s.unit,
                "Định mức (đ/đơn vị)": num(s.norm),
                "Hệ số mã hàng": FLAG if s.factor_applied != 1 else "",
                "Thành tiền (đ)": num(s.amount),
                "Nhân hệ số SL": CHECK if s.applies_quantity_factor else "",
                "Thành tiền sau hệ số (đ)": num(s.amount_after_factor),
            }
            for s in r.weaving_stages
        ],
        column_config={
            "SL": st.column_config.NumberColumn("SL", format="localized"),
            "Định mức (đ/đơn vị)": st.column_config.NumberColumn("Định mức (đ/đơn vị)", format="localized"),
            "Thành tiền (đ)": st.column_config.NumberColumn("Thành tiền (đ)", format="localized"),
            "Thành tiền sau hệ số (đ)": st.column_config.NumberColumn("Thành tiền sau hệ số (đ)", format="localized"),
        },
        empty_message="Chưa có chi phí công đoạn.",
    )
    section_title("Chi phí theo khoản mục (đ/m)")
    item_labels = {
        "labor": "Nhân công", "depreciation": "Khấu hao", "power": "Điện", "material": "Vật tư", "fuel": "Nhiên liệu",
        "chemical": "Hóa chất", "overhead": "CPQL", "total": "Tổng (đ/m)",
    }  # fmt: skip
    data_table(
        [
            {"Công đoạn": c.stage} | {label: num(getattr(c, f)) for f, label in item_labels.items()}
            for c in r.cost_items
        ],
        column_config={
            label: st.column_config.NumberColumn(label, format="localized") for label in item_labels.values()
        },
        empty_message="Chưa có chi phí theo khoản mục.",
    )
    stat_row(
        [
            ("Tổng chi phí ngành Dệt (đ)", format_number(r.weaving_total)),
            ("Đơn giá CM (đ/m)", format_number(r.weaving_cm_price)),
            ("Kg mộc", format_number(r.greige_kg, 2)),
        ]
    )
    return twist_lines, weaving
