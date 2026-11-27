"""Screen 2 tab "Nhuộm" (block E): HCM (4.15) or TCDN (4.16) inputs and the dyeing result."""

from collections.abc import Callable, Sequence
from types import SimpleNamespace
from typing import Any

import streamlit as st

from backend.features.woven_costing.dto.common_dto import DyePlant, ExtraCostType
from backend.features.woven_costing.dto.costsheet_dto import CostsheetResponse, ExtraCostDTO
from backend.features.woven_costing.dto.list_dto import CostsheetOptionsResponse
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, stat_row
from frontend.core.formatting import format_number
from frontend.features.woven_costing.components.labels import (
    dec,
    enum_values,
    from_pct,
    index_of,
    num,
    pct_text,
    text,
    text_or_empty,
    to_pct,
    with_value,
)
from frontend.features.woven_costing.components.marks import apply_table, heading

BLENDED = "Blended"
REPEAT = "Số lần xử lý thêm"
HCM_BLEND_LABELS = ["Trắng (%)", "Nhạt (%)", "Trung bình (%)", "Đậm (%)", "Đặc biệt (%)"]
TCDN_BLEND_LABELS = ["White (%)", "Light (%)", "Medium (%)", "Dark (%)", "Special (%)"]
WIDTH_LABELS = {1: "Khổ đơn", 2: "Khổ đôi", 3: "Khổ ba"}
EXTRA_FIELDS = ("chemical", "labor", "depreciation", "power", "fuel", "material", "overhead")
HCM_EXTRA_LABELS = ("HCTN", "Tiền lương", "Khấu hao", "Điện", "Nhiên liệu", "Vật tư", "Quản lý")
TCDN_EXTRA_LABELS = ("Hóa chất", "Nhân công", "Khấu hao", "Điện", "Nhiên liệu", "Vật tư", "CPQL")


def _key_maker(page: BasePage, prefix: str, sfx: str) -> Callable[[str], str]:
    def key(name: str) -> str:
        return page.key(f"{prefix}.{name}.{sfx}")

    return key


def _select(column: Any, label: str, options: Sequence[str], value: str, key: str, off: bool, placeholder: str) -> str:
    items = with_value(options, value)
    picked = column.selectbox(
        label, items, index=index_of(items, value), placeholder=placeholder, key=key, disabled=off
    )
    return picked or ""


def _blend(labels: Sequence[str], ratios: Sequence[Any], key: Callable[[str], str], off: bool) -> list[Any]:
    values = []
    for index, (column, label) in enumerate(zip(st.columns(5), labels, strict=True)):
        current = to_pct(ratios[index]) if index < len(ratios) else 0.0
        values.append(
            from_pct(
                column.number_input(
                    label, min_value=0.0, max_value=100.0, value=current or 0.0, key=key(f"blend{index}"), disabled=off
                )
            )
        )
    st.caption("Tổng tỷ trọng phải = 100%.")
    return values


def _list_table(
    title: str, key: str, values: Sequence[str], column: str, options: Sequence[str], off: bool
) -> list[str] | None:
    heading(title, editable=not off)
    rows = [{column: v} for v in values]
    items = list(dict.fromkeys([*options, *values]))
    config = {column: st.column_config.SelectboxColumn(column, options=items, required=True)}
    if off:
        data_table(rows, column_config=config, empty_message="Không có.")
        return None
    edited = apply_table(rows, key=key, columns=[column], column_config=config, allow_add_delete=True)
    return [str(r[column]) for r in edited if r.get(column)]


def _cost_table(
    title: str, key: str, lines: Sequence[Any], columns: dict[str, str], off: bool, unit_labels: Sequence[str] = ()
) -> list[dict[str, Any]] | None:
    """Rows of named costs: columns = {label: dto field}; percent columns (loss_rate) are x100 on screen."""
    heading(title, editable=not off)
    rows = []
    for line in lines:
        row = {}
        for label, field in columns.items():
            value = getattr(line, field)
            row[label] = to_pct(value) if field == "loss_rate" else (num(value) if field != "name" else value)
        rows.append(row)
    config = {
        label: st.column_config.NumberColumn(label, min_value=0, format="localized")
        for label, field in columns.items()
        if field not in ("name", "loss_rate")
    }
    config |= {
        label: st.column_config.NumberColumn(label, min_value=0, max_value=99.99, format="%.2f")
        for label, field in columns.items()
        if field == "loss_rate"
    }
    for label in unit_labels:
        config[label] = st.column_config.NumberColumn(label, min_value=0, format="localized")
    if off:
        data_table(rows, column_config=config, empty_message="Không có.")
        return None
    edited = apply_table(rows, key=key, columns=list(columns), column_config=config, allow_add_delete=True)
    result = []
    for row in edited:
        if all(row.get(label) in (None, "") for label in columns):
            continue
        item: dict[str, Any] = {}
        for label, field in columns.items():
            value = row.get(label)
            if field == "name":
                item[field] = text_or_empty(value)
            elif field == "loss_rate":
                item[field] = from_pct(value)
            else:
                item[field] = dec(value)
        result.append(item)
    return result


def _extra_cost(
    current: ExtraCostDTO | None, reason: str, labels: Sequence[str], unit: str, key: Callable[[str], str], off: bool
) -> tuple[dict[str, Any] | None, str]:
    name = st.text_input("Tên chi phí", value=current.name if current else "", max_chars=200, key=key("extra_name"),
                         disabled=off)  # fmt: skip
    values: dict[str, Any] = {"name": (name or "").strip()}
    for column, field, label in zip(st.columns(7), EXTRA_FIELDS, labels, strict=True):
        values[field] = dec(
            column.number_input(
                f"{label} ({unit})",
                min_value=0.0,
                value=num(getattr(current, field)) if current else None,
                key=key(f"extra_{field}"),
                disabled=off,
            )
        )
    new_reason = st.text_input(
        "Lý do sửa so với giá ngành báo", value=reason, max_chars=300, key=key("extra_reason"), disabled=off
    )
    has_data = values["name"] or any(values[f] is not None for f in EXTRA_FIELDS)
    return (values if has_data else None), (new_reason or "").strip()


def _hcm(page: BasePage, w: Any, options: CostsheetOptionsResponse, sfx: str) -> dict[str, Any] | None:
    data = w.input.hcm_dyeing
    off = not w.editable
    key = _key_maker(page, "hcm", sfx)
    c1, c2, c3, c4 = st.columns(4)
    material = _select(c1, "Nguyên liệu nhuộm", options.hcm_dye_materials, data.dye_material, key("material"), off,
                       "Chọn")  # fmt: skip
    color = _select(c2, "Cấp màu", options.hcm_color_levels, data.color_level, key("color"), off, "Chọn")
    with c3:
        width = st.segmented_control(
            "Khổ",
            list(WIDTH_LABELS),
            default=data.width_type if data.width_type in WIDTH_LABELS else 1,
            format_func=lambda v: WIDTH_LABELS[v],
            required=True,
            key=key("width"),
            disabled=off,
        )
    loss = c4.number_input(
        "Tiêu hao quy trình nhuộm (%)", min_value=0.0, max_value=99.99, value=to_pct(data.dye_loss_rate),
        format="%.2f", key=key("loss"), disabled=off,
    )  # fmt: skip
    blend = _blend(HCM_BLEND_LABELS, data.blend_ratios, key, off) if color == BLENDED else list(data.blend_ratios)
    stages = _list_table("Công đoạn đặc biệt (tối đa 7)", key("stages"), data.special_stages, "Công đoạn",
                         options.hcm_special_stages, off)  # fmt: skip
    features = _list_table("Tính năng đặc biệt (tối đa 6)", key("features"), data.special_features, "Tính năng",
                           options.hcm_special_features, off)  # fmt: skip
    special_costs = _cost_table("Chi phí đặc biệt (tối đa 2)", key("special_costs"), data.special_costs,
                                {"Tên": "name", "Đơn giá (đ/kg)": "amount"}, off)  # fmt: skip
    with st.expander("Chi phí phát sinh do ngành báo giá", expanded=data.extra_cost is not None, key=key("extra")):
        extra, reason = _extra_cost(data.extra_cost, data.extra_cost_reason, HCM_EXTRA_LABELS, "đ/kg", key, off)
    outsourcing = _cost_table("Gia công (tối đa 2)", key("outsourcing"), data.outsourcing_lines,
                              {"Tên": "name", "Đơn giá (đ/kg)": "amount"}, off)  # fmt: skip
    if off:
        return None
    return {
        "dye_material": material,
        "color_level": color,
        "blend_ratios": blend,
        "width_type": int(width or 1),
        "dye_loss_rate": from_pct(loss),
        "special_stages": stages or [],
        "special_features": features or [],
        "special_costs": special_costs or [],
        "extra_cost": extra,
        "extra_cost_reason": reason,
        "outsourcing_lines": outsourcing or [],
    }


def _tcdn(
    page: BasePage, w: Any, options: CostsheetOptionsResponse, sfx: str, job: bool = False
) -> dict[str, Any] | None:
    """``job`` (2026-11-25, dyeing job order): + "Số lần xử lý thêm", no extra cost / outside processing."""
    data = w.input.tcdn_dyeing
    off = not w.editable
    key = _key_maker(page, "tcdn", sfx)
    c1, c2, c3, c4 = st.columns(4)
    material = _select(c1, "Nguyên liệu nhuộm", options.tcdn_dye_materials, data.dye_material, key("material"), off,
                       "Chọn")  # fmt: skip
    color = _select(c2, "Cấp màu", options.tcdn_color_levels, data.color_level, key("color"), off, "Chọn")
    special_dye = _select(c3, "Phẩm nhuộm đặc biệt", options.special_dyes, data.special_dye, key("special_dye"), off,
                          "Không")  # fmt: skip
    wr = _select(c4, "Hóa chất WR", options.wr_chemicals, data.wr_chemical, key("wr"), off, "Không")
    if wr:
        c4.caption("Đã tự tính Kiểm trước WR, không cần chọn Kiểm Trung Gian nữa.")
    special_price = data.special_dye_chemical_price
    if special_dye:
        special_price = dec(
            c3.number_input(
                "Giá hóa chất thuốc nhuộm (đ/m, vải 250 g/m)", min_value=0.0, value=num(special_price),
                key=key("special_price"), disabled=off,
            )
        )  # fmt: skip
    blend = _blend(TCDN_BLEND_LABELS, data.blend_ratios, key, off) if color == BLENDED else list(data.blend_ratios)
    heading("Công đoạn ngoài quy trình (tối đa 13)", editable=not off)
    stage_rows = [{"Công đoạn": s.name, "Giá hóa chất (đ/m)": num(s.chemical_price), REPEAT: s.repeat_count}
                  for s in data.extra_stages]  # fmt: skip
    stage_names = list(dict.fromkeys([*options.tcdn_stages, *(s.name for s in data.extra_stages if s.name)]))
    stage_config = {
        "Công đoạn": st.column_config.SelectboxColumn("Công đoạn", options=stage_names, required=True),
        "Giá hóa chất (đ/m)": st.column_config.NumberColumn(
            "Giá hóa chất (đ/m)", min_value=0, format="localized", help="Bắt buộc với Coating, Santa, Bonding, Soaping"
        ),
    }
    if job:
        stage_config[REPEAT] = st.column_config.NumberColumn(REPEAT, min_value=0, max_value=9, step=1, format="%d",
                                                             help="Xử lý thêm 1 lần: nhập 1; thêm 2 lần: nhập 2")  # fmt: skip
    else:
        for row in stage_rows:
            row.pop(REPEAT)
    stages = None
    if off:
        data_table(stage_rows, column_config=stage_config, empty_message="Không có.")
    else:
        edited = apply_table(stage_rows, key=key("stages"), columns=list(stage_config), column_config=stage_config,
                                allow_add_delete=True)  # fmt: skip
        stages = [
            {
                "name": text_or_empty(r.get("Công đoạn")),
                "chemical_price": dec(r.get("Giá hóa chất (đ/m)")),
                "repeat_count": int(r.get(REPEAT) or 0),
            }
            for r in edited
            if r.get("Công đoạn") or r.get("Giá hóa chất (đ/m)") is not None
        ]
    st.caption("Công đoạn lặp lại: ghi số lần xử lý thêm." if job else "Công đoạn lặp lại = thêm dòng.")
    features = _cost_table("Tính năng đặc biệt (tối đa 6)", key("features"), data.special_features,
                           {"Tính năng": "name", "Giá hóa chất (đ/m)": "amount"}, off)  # fmt: skip
    if job:
        if off:
            return None
        return {"dye_material": material, "color_level": color, "blend_ratios": blend, "special_dye": special_dye,
                "special_dye_chemical_price": special_price, "wr_chemical": wr, "extra_stages": stages or [],
                "special_features": features or []}  # fmt: skip
    with st.expander("Chi phí phát sinh do ngành báo giá", expanded=data.extra_cost is not None, key=key("extra")):
        types = enum_values(ExtraCostType)
        extra_type = st.segmented_control(
            "Loại quy trình", types, default=text(data.extra_cost_type) or None, key=key("extra_type"), disabled=off
        )
        extra_loss = st.number_input(
            "Tiêu hao quy trình nhuộm (%)", min_value=0.0, max_value=99.99, value=to_pct(data.extra_cost_loss_rate),
            format="%.2f", key=key("extra_loss"), disabled=off,
        )  # fmt: skip
        extra, reason = _extra_cost(data.extra_cost, data.extra_cost_reason, TCDN_EXTRA_LABELS, "đ/m", key, off)
    outsourcing = _cost_table("Gia công ngoài (tối đa 2)", key("outsourcing"), data.outsourcing_lines,
                              {"Tên": "name", "Đơn giá (đ/m)": "amount", "Tiêu hao (%)": "loss_rate"}, off)  # fmt: skip
    if off:
        return None
    return {
        "dye_material": material,
        "color_level": color,
        "blend_ratios": blend,
        "special_dye": special_dye,
        "special_dye_chemical_price": special_price,
        "wr_chemical": wr,
        "extra_stages": stages or [],
        "special_features": features or [],
        "extra_cost_type": extra_type or None,
        "extra_cost_loss_rate": from_pct(extra_loss),
        "extra_cost": extra,
        "extra_cost_reason": reason,
        "outsourcing_lines": outsourcing or [],
    }


def _result(w: CostsheetResponse, plant: str) -> None:
    r = w.result
    heading("Kết quả nhuộm", editable=False)
    tcdn = plant == DyePlant.TCDN.value
    labels = TCDN_EXTRA_LABELS if tcdn else HCM_EXTRA_LABELS
    rows = []
    for line in r.dyeing_lines:
        row: dict[str, Any] = {"Dòng": line.name}
        row |= {label: num(getattr(line, field)) for field, label in zip(EXTRA_FIELDS, labels, strict=True)}
        if tcdn:
            row["Hệ số TCDN"] = num(line.factor)
        row["Tiêu hao (%)"] = to_pct(line.loss_rate)
        row["Chi phí/m (đ)" if tcdn else "Tổng (đ/kg)"] = num(line.per_m if tcdn else line.per_kg)
        row["Ghi chú"] = line.note
        rows.append(row)
    money = {label: st.column_config.NumberColumn(label, format="localized") for label in labels}
    money |= {
        "Chi phí/m (đ)": st.column_config.NumberColumn("Chi phí/m (đ)", format="localized"),
        "Tổng (đ/kg)": st.column_config.NumberColumn("Tổng (đ/kg)", format="localized"),
        "Hệ số TCDN": st.column_config.NumberColumn("Hệ số TCDN", format="%.4f"),
        "Tiêu hao (%)": st.column_config.NumberColumn("Tiêu hao (%)", format="%.2f"),
    }
    data_table(rows, column_config=money, empty_message="Chưa có kết quả nhuộm.")
    tiles = [("Hệ số TCDN", format_number(r.tcdn_factor, 4))] if tcdn else []
    tiles += [("Tiêu hao nhuộm", pct_text(r.dye_loss_rate))]
    if not tcdn:
        tiles.append(("Chi phí/kg (đ)", format_number(r.dyeing_per_kg)))
    tiles += [
        ("Chi phí/m (đ)", format_number(r.dyeing_per_m)),
        ("Tổng chi phí nhuộm (đ)", format_number(r.dyeing_total)),
    ]
    stat_row(tiles)


def dyeing_tab(
    page: BasePage, w: CostsheetResponse, options: CostsheetOptionsResponse, sfx: str, plant: str | None
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Draws the plant chosen in block A. Returns (hcm, tcdn) inputs; None = keep the stored values."""
    if plant == DyePlant.TCDN.value:
        st.caption("Nhà máy nhuộm TCDN (theo khối Thông tin đơn).")
        tcdn = _tcdn(page, w, options, sfx)
        _result(w, DyePlant.TCDN.value)
        return None, tcdn
    st.caption("Nhà máy nhuộm HCM (theo khối Thông tin đơn).")
    hcm = _hcm(page, w, options, sfx)
    _result(w, DyePlant.HCM.value)
    return hcm, None


def job_line_dyeing(
    page: BasePage, line: Any, editable: bool, options: CostsheetOptionsResponse, sfx: str, plant: str
) -> dict[str, Any] | None:
    """Screen 8 "Chi tiết dòng" (2026-11-25): the TCDN (4.16) or HCM (4.15) inputs of one job line; None = read only."""
    holder = SimpleNamespace(input=SimpleNamespace(tcdn_dyeing=line.tcdn_dyeing, hcm_dyeing=line.hcm_dyeing),
                             editable=editable)  # fmt: skip
    if plant == DyePlant.TCDN.value:
        return _tcdn(page, holder, options, sfx, job=True)
    return _hcm(page, holder, options, sfx)
