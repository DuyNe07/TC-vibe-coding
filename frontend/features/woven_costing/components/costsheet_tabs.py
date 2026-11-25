"""Screen 2 tabs: Thông số vải (B), Sợi (C), Tham số (G), Cảnh báo and Lịch sử (H)."""

from typing import Any

import streamlit as st

from backend.features.woven_costing.dto.common_dto import Currency, ParamGroup, YarnDirection
from backend.features.woven_costing.dto.costsheet_dto import CostsheetResponse
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, editable_table, empty_state, section_title, stat_row
from frontend.core.formatting import format_number
from frontend.features.woven_costing.components.fabric_view import spec_table, yarn_table
from frontend.features.woven_costing.components.labels import (
    FLAG,
    dec,
    enum_values,
    from_pct,
    num,
    pct_text,
    status_column,
    text,
    to_pct,
)

WARP = YarnDirection.WARP.value
YARN_EDITABLE = ["Đơn vị giá", "Giá", "Sợi cặn (%)", "Se"]
YARN_COLUMNS = [
    "Hướng", "STT", "Tên sợi", "T/M", "Tỷ lệ (%)", "Đơn vị giá", "Giá", "Giá (đ/kg)", "Ngày nhập giá", "Giá hết hạn",
    "Sợi cặn (%)", "Se", "Hồ", "Lý do gợi ý Hồ", "Tiêu hao (%)", "Lượng sợi (kg)", "Thành tiền (đ)",
]  # fmt: skip
YARN_CONFIG = {
    "Hướng": st.column_config.TextColumn("Hướng", width="small", pinned=True),
    "STT": st.column_config.NumberColumn("STT", width="small"),
    "Tên sợi": st.column_config.TextColumn("Tên sợi", width="large"),
    "T/M": st.column_config.TextColumn("T/M", width="small"),
    "Tỷ lệ (%)": st.column_config.NumberColumn("Tỷ lệ (%)", format="%.2f"),
    "Đơn vị giá": st.column_config.SelectboxColumn("Đơn vị giá", options=enum_values(Currency), required=True),
    "Giá": st.column_config.NumberColumn("Giá", min_value=0, format="%.4f", help="USD/kg hoặc đ/kg"),
    "Giá (đ/kg)": st.column_config.NumberColumn("Giá (đ/kg)", format="localized"),
    "Ngày nhập giá": st.column_config.DateColumn("Ngày nhập giá", format="DD/MM/YYYY"),
    "Giá hết hạn": st.column_config.TextColumn("Giá hết hạn", width="small"),
    "Sợi cặn (%)": st.column_config.NumberColumn("Sợi cặn (%)", min_value=0, max_value=99.99, format="%.2f"),
    "Se": st.column_config.CheckboxColumn("Se"),
    "Hồ": st.column_config.CheckboxColumn("Hồ", disabled=True),
    "Tiêu hao (%)": st.column_config.NumberColumn("Tiêu hao (%)", format="%.2f"),
    "Lượng sợi (kg)": st.column_config.NumberColumn("Lượng sợi (kg)", format="%.2f"),
    "Thành tiền (đ)": st.column_config.NumberColumn("Thành tiền (đ)", format="localized"),
}
YARN_WASTE_PRICE_CODE = "yarn_waste_price"


def fabric_tab(w: CostsheetResponse) -> None:
    f = w.fabric
    if f is None:
        empty_state("Chưa có thông số vải.", "Nhập mã vải ở khối Thông tin đơn rồi bấm Tính lại.")
        return
    with st.container(horizontal=True, gap="small", vertical_alignment="center"):
        st.markdown(f"**{f.tcfno} - {f.fabric_name}**")
        source = text(f.source)
        st.badge(f"Nguồn: {source}", color="orange" if source == "Nhập tay" else "blue")
    spec_table(
        f,
        greige_m_per_kg=f.greige_m_per_kg,
        finished_m_per_kg=f.finished_m_per_kg,
        overridden=f.overridden_fields,
    )
    stat_row([("Độ co", pct_text(w.result.shrinkage)), ("Độ co mắc", pct_text(f.warping_loss_rate))])
    section_title("Sợi theo dữ liệu gốc")
    yarn_table(f.yarns)
    if source != "Nhập tay":
        st.caption("Thông số lấy từ dữ liệu gốc Peace / WFX, chỉ đọc.")
    if f.overridden_fields:
        st.caption(f"{FLAG} Thông số đã sửa trên costsheet (tô màu cho người duyệt).")


def yarn_tab(page: BasePage, w: CostsheetResponse, sfx: str) -> list[dict[str, Any]] | None:
    """Block C. Returns the yarn input lines (None = unchanged / read only)."""
    lines = w.yarn_lines
    if not lines:
        empty_state("Mã vải chưa có dòng sợi.", "Liên hệ SO / PD bổ sung sợi cho mã này.")
        return None
    warp_sized = any(line.is_sized for line in lines if text(line.direction) == WARP)
    c1, c2 = st.columns([1, 2], vertical_alignment="center")
    sized_all = c1.toggle(
        "Tick Hồ cho tất cả sợi dọc", value=warp_sized, key=page.key(f"sized.{sfx}"), disabled=not w.editable
    )
    if w.size_suggest_reason:
        c2.caption(f"Gợi ý: {w.size_suggest_reason}")
    rows = [
        {
            "Hướng": text(y.direction),
            "STT": y.seq,
            "Tên sợi": y.yarn_name,
            "T/M": y.twist_tpm,
            "Tỷ lệ (%)": to_pct(y.ratio),
            "Đơn vị giá": text(y.price_currency) or Currency.USD.value,
            "Giá": num(y.price_input),
            "Giá (đ/kg)": num(y.price_vnd),
            "Ngày nhập giá": y.price_entered_on,
            "Giá hết hạn": FLAG if y.price_expired else "",
            "Sợi cặn (%)": to_pct(y.waste_rate),
            "Se": y.is_twisted,
            "Hồ": y.is_sized,
            "Lý do gợi ý Hồ": y.size_suggest_reason,
            "Tiêu hao (%)": to_pct(y.loss_rate),
            "Lượng sợi (kg)": num(y.yarn_kg),
            "Thành tiền (đ)": num(y.amount),
        }
        for y in lines
    ]
    result = None
    if w.editable:
        edited = editable_table(
            rows,
            key=page.key(f"yarns.{sfx}"),
            columns=YARN_COLUMNS,
            column_config=YARN_CONFIG,
            disabled=[c for c in YARN_COLUMNS if c not in YARN_EDITABLE],
        )
        result = [
            {
                "direction": r["Hướng"],
                "seq": int(r["STT"]),
                "price_currency": r.get("Đơn vị giá") or Currency.USD.value,
                "price_input": dec(r.get("Giá")),
                "waste_rate": from_pct(r.get("Sợi cặn (%)")),
                "is_twisted": bool(r.get("Se")),
                "is_sized": bool(sized_all) and r["Hướng"] == WARP,
            }
            for r in edited
        ]
    else:
        data_table(rows, column_config=YARN_CONFIG)
    waste_price = next((p.used_value for p in w.parameters if p.code == YARN_WASTE_PRICE_CODE), None)
    stat_row(
        [
            ("Tổng tỷ lệ", pct_text(w.result.yarn_ratio_total)),
            ("Tổng chi phí sợi (đ)", format_number(w.result.yarn_total)),
            ("Giá thanh lý sợi cặn (đ/kg)", format_number(waste_price)),
        ]
    )
    if any(y.price_expired for y in lines):
        st.caption(f'{FLAG} Giá sợi đã hết hiệu lực: nhập giá mới hoặc bấm "Xác nhận giá sợi hôm nay".')
    return result


def _param_row(p: Any) -> dict[str, Any]:
    convert = to_pct if p.is_percent else num
    return {
        "code": p.code,
        "Tham số": p.label,
        "Đơn vị": "%" if p.is_percent else p.unit,
        "Mặc định": convert(p.default_value),
        "Đang dùng": convert(p.used_value),
        "Đã sửa": FLAG if p.used_value != p.default_value else "",
        "Lý do": p.reason,
    }


PARAM_CONFIG = {
    "Mặc định": st.column_config.NumberColumn("Mặc định", format="%.4f"),
    "Đang dùng": st.column_config.NumberColumn("Đang dùng", min_value=0, format="%.4f"),
    "Đã sửa": st.column_config.TextColumn("Đã sửa", width="small"),
    "Lý do": st.column_config.TextColumn("Lý do", width="large"),
}
PARAM_ORDER = ["Tham số", "Đơn vị", "Mặc định", "Đang dùng", "Đã sửa", "Lý do"]


def _changed(edited: list[dict[str, Any]], params: list[Any]) -> list[dict[str, Any]]:
    """Rows whose "Đang dùng" differs from the default (BR-46 overrides)."""
    by_code = {p.code: p for p in params}
    changed = []
    for row in edited:
        p = by_code[row["code"]]
        used = from_pct(row.get("Đang dùng")) if p.is_percent else dec(row.get("Đang dùng"))
        if used is not None and abs(used - p.default_value) > dec("1e-9"):
            changed.append({"code": p.code, "used_value": used})
    return changed


def params_tab(page: BasePage, w: CostsheetResponse, sfx: str) -> list[dict[str, Any]] | None:
    """Block G grouped by department (2026-11-25): values sales may change (applied discount factor with its
    reason, % B/C of the sale form, liquidation prices...) and the values only SO sets. Returns the overrides
    (None = read only)."""
    result: list[dict[str, Any]] | None = [] if w.editable else None
    if not w.parameters:
        empty_state("Chưa có tham số.")
        return result
    for group in enum_values(ParamGroup):
        params = [p for p in w.parameters if text(p.group) == group]
        section_title(group)
        editable_params = [p for p in params if not p.so_only]
        so_params = [p for p in params if p.so_only]
        rows = [_param_row(p) for p in editable_params]
        if not params:
            st.caption("Không áp dụng cho phiếu này.")
        elif rows and result is not None:
            edited = editable_table(rows, key=page.key(f"params.{group}.{sfx}"), column_config=PARAM_CONFIG,
                                    column_order=PARAM_ORDER,
                                    disabled=["code", "Tham số", "Đơn vị", "Mặc định", "Đã sửa", "Lý do"])  # fmt: skip
            result += _changed(edited, editable_params)
        elif rows:
            data_table(rows, column_config=PARAM_CONFIG, column_order=PARAM_ORDER)
        if so_params:
            st.caption("Tham số chỉ SO đặt:")
            data_table([_param_row(p) for p in so_params], column_config=PARAM_CONFIG, column_order=PARAM_ORDER[:-2])
    st.caption("Ô đã sửa được tô màu cho người duyệt và lưu theo phiếu.")
    return result


def warnings_tab(w: CostsheetResponse) -> None:
    if not w.warnings:
        st.success("Không có cảnh báo.", icon=":material/check:")
        return
    for warning in w.warnings:
        if warning.blocking:
            st.error(warning.message, icon="⛔")
        else:
            st.warning(warning.message, icon="⚠️")


def history_tab(page: BasePage, w: CostsheetResponse) -> str | None:
    """Block H. Returns the id of the version the user asked to open (or None)."""
    section_title("Phiên bản")
    picked = data_table(
        [
            {
                "id": v.id,
                "Phiên bản": v.version,
                "Trạng thái": [text(v.status)],
                "Ngày tính giá": v.costing_date,
                "Giá bán (VND/m)": num(v.sell_price_vnd),
                "Giá vốn (VND/m)": num(v.cogs_vnd),
                "GP%": to_pct(v.gp_pct),
                "Người duyệt": v.approved_by_name,
                "Ngày duyệt": v.approved_at,
            }
            for v in w.versions
        ],
        column_config={
            "Phiên bản": st.column_config.NumberColumn("Phiên bản", format="v%d", width="small"),
            "Trạng thái": status_column(),
            "Ngày tính giá": st.column_config.DateColumn("Ngày tính giá", format="DD/MM/YYYY"),
            "Giá bán (VND/m)": st.column_config.NumberColumn("Giá bán (VND/m)", format="localized"),
            "Giá vốn (VND/m)": st.column_config.NumberColumn("Giá vốn (VND/m)", format="localized"),
            "GP%": st.column_config.NumberColumn("GP%", format="%.2f %%"),
            "Ngày duyệt": st.column_config.DatetimeColumn("Ngày duyệt", format="DD/MM/YYYY HH:mm"),
        },
        column_order=[
            "Phiên bản",
            "Trạng thái",
            "Ngày tính giá",
            "Giá bán (VND/m)",
            "Giá vốn (VND/m)",
            "GP%",
            "Người duyệt",
            "Ngày duyệt",
        ],  # fmt: skip
        selection="single",
        key=page.key(f"versions.{w.costsheet_no}.{w.id}"),
        empty_message="Chưa có phiên bản.",
    )
    chosen = picked[0]["id"] if picked else None
    open_version = st.button(
        "Mở phiên bản đã chọn",
        icon=":material/folder_open:",
        key=page.key(f"open_version.{w.id}"),
        disabled=not chosen or chosen == w.id,
    )
    section_title("Lịch sử thao tác")
    data_table(
        [
            {"Phiên bản": h.version, "Thao tác": text(h.action), "Người": h.by_name, "Lúc": h.at, "Ghi chú": h.comment}
            for h in w.history
        ],
        column_config={
            "Phiên bản": st.column_config.NumberColumn("Phiên bản", format="v%d", width="small"),
            "Lúc": st.column_config.DatetimeColumn("Lúc", format="DD/MM/YYYY HH:mm"),
        },
        empty_message="Chưa có thao tác.",
    )
    return chosen if open_version else None
