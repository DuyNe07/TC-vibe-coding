"""Tables used on several screens: rows keyed by the Vietnamese column label + their column_config."""

from collections.abc import Iterable
from typing import Any

import streamlit as st

from backend.features.yarn_costing.dto.common_dto import RecalcBatchDTO, YarnComponentDTO
from backend.features.yarn_costing.dto.dashboard_dto import PriceAnomalyDTO
from backend.features.yarn_costing.dto.price_dto import PriceLineRowDTO
from backend.features.yarn_costing.dto.pricing_dto import PriceHistoryDTO, PriceLineDTO, StageCostDTO
from backend.features.yarn_costing.dto.request_dto import YarnSummaryDTO
from frontend.features.yarn_costing.components.display import minutes4, pct, plain, rate2, usd, vnd

COL = st.column_config

USD_FORMAT = "%.4f"
PCT_FORMAT = "%.2f%%"
COST_ITEMS = (
    ("labor", "Nhân công"),
    ("depreciation", "Khấu hao"),
    ("electricity", "Điện"),
    ("materials", "Vật tư"),
    ("overhead", "CPQL"),
)


def money(label: str) -> Any:
    return COL.NumberColumn(label, format="localized")


def percent(label: str) -> Any:
    return COL.NumberColumn(label, format=PCT_FORMAT)


def usd_col(label: str) -> Any:
    return COL.NumberColumn(label, format=USD_FORMAT)


def date_col(label: str) -> Any:
    return COL.DateColumn(label, format="DD/MM/YYYY")


def datetime_col(label: str) -> Any:
    return COL.DatetimeColumn(label, format="DD/MM/YYYY HH:mm")


def count_col(label: str) -> Any:
    return COL.NumberColumn(label, format="localized")


# ---- Bảng giá (sheet "Bang gia", 5.4) ----
PRICE_LINE_CONFIG = {
    "STT": count_col("STT"),
    "Mã dòng": COL.TextColumn("Mã dòng", pinned=True),
    "Chi số": count_col("Chi số"),
    "Thành phần": COL.TextColumn("Thành phần", width="large"),
    **{label: money(label) for _, label in COST_ITEMS},
    "Tổng (VND/kg)": money("Tổng (VND/kg)"),
    "USD/kg": usd_col("USD/kg"),
    "Tỷ giá": money("Tỷ giá"),
    "Ngày tính giá": date_col("Ngày tính giá"),
    "Ngày hiệu lực": date_col("Ngày hiệu lực"),
    "% CK/PP": percent("% CK/PP"),
}


def price_line_rows(items: Iterable[PriceLineRowDTO]) -> list[dict[str, Any]]:
    return [
        {
            "STT": row.stt,
            "Xưởng": str(row.factory_code),
            "Mã dòng": row.line_code,
            "Loại dòng": row.line_type.value,
            "Mã gốc": row.base_code,
            "Tên sợi": row.yarn_name,
            "Nhóm sợi": row.yarn_group,
            "Chi số": plain(row.count),
            "Công nghệ": row.technology.value,
            "Nhóm tiêu hao": row.loss_group_key,
            "Thành phần": row.components_text,
            **{label: vnd(getattr(row, field)) for field, label in COST_ITEMS},
            "Tổng (VND/kg)": vnd(row.total_vnd),
            "USD/kg": usd(row.usd_per_kg),
            "Tỷ giá": vnd(row.exchange_rate),
            "Loại đóng gói": row.packaging_code or "",
            "Tên loại đóng gói": row.packaging_name,
            "Ngày tính giá": row.first_priced_at,
            "Ngày hiệu lực": row.effective_date,
            "Trạng thái": row.status.value,
            "Mã kế toán": row.accounting_code or "",
            "% CK/PP": pct(row.adjustment_percent),
            "Lý do CK/PP": row.adjustment_reason,
            "Đơn hàng": row.order_ref,
        }
        for row in items
    ]


# ---- Chi tiết công đoạn (4.14) ----
STAGE_COST_CONFIG = {
    "STT": count_col("STT"),
    "Lượt": count_col("Lượt"),
    "NSM (kg/giờ)": COL.NumberColumn("NSM (kg/giờ)", format="localized"),
    "Thời gian chạy máy (phút/kg)": COL.NumberColumn("Thời gian chạy máy (phút/kg)", format="%.4f"),
    "Tiêu hao": percent("Tiêu hao"),
    "Tiêu hao lũy kế": percent("Tiêu hao lũy kế"),
    "Định mức (VND/phút)": COL.NumberColumn("Định mức (VND/phút)", format="%.2f"),
    "Chi phí/kg": money("Chi phí/kg"),
    **{label: money(label) for _, label in COST_ITEMS},
}


def stage_cost_rows(details: Iterable[StageCostDTO]) -> list[dict[str, Any]]:
    return [
        {
            "STT": d.sequence,
            "Công đoạn": d.stage_code,
            "Tên công đoạn": d.stage_name,
            "Nguyên liệu": d.material_label,
            "Lượt": d.pass_no,
            "NSM (kg/giờ)": plain(d.nsm),
            "Thời gian chạy máy (phút/kg)": minutes4(d.run_minutes),
            "Tiêu hao": pct(d.loss),
            "Tiêu hao lũy kế": pct(d.cumulative_loss),
            "Định mức (VND/phút)": rate2(d.total_rate),
            "Chi phí/kg": vnd(d.cost_per_kg),
            **{label: vnd(getattr(d, field)) for field, label in COST_ITEMS},
            "Ghi chú tiêu hao": d.loss_note,  # BR-64
        }
        for d in details
    ]


# ---- Thành phần nguyên liệu của một sợi (4.12.1), chỉ xem ----
NO_CARDING = "Không chải thô"
COMPONENT_CONFIG = {
    "Tỷ lệ %": percent("Tỷ lệ %"),
    "Lượt": count_col("Lượt"),
    "NSM chải thô": COL.NumberColumn("NSM chải thô", format="localized"),
}


def component_rows(components: Iterable[YarnComponentDTO]) -> list[dict[str, Any]]:
    return [
        {
            "Nguyên liệu": c.material_label,
            "Tỷ lệ %": pct(c.ratio),
            "Dây chuyền": c.carding_stage or NO_CARDING,
            "Lượt": c.pass_no,
            "NSM chải thô": plain(c.nsm_carding),
        }
        for c in components
    ]


# ---- Danh sách mã / yêu cầu (UC-19) ----
YARN_SUMMARY_CONFIG = {
    "Ngày tạo": datetime_col("Ngày tạo"),
    "Ngày xử lý": datetime_col("Ngày xử lý"),
    "Tổng (VND/kg)": money("Tổng (VND/kg)"),
    "USD/kg": usd_col("USD/kg"),
}


def yarn_summary_rows(
    items: Iterable[YarnSummaryDTO], packaging_names: dict[str, str] | None = None
) -> list[dict[str, Any]]:
    names = packaging_names or {}
    rows = []
    for y in items:
        pack = y.packaging_code or ""
        rows.append(
            {
                "Mã": y.yarn_code,
                "Xưởng": str(y.factory_code),
                "Tên sợi": y.yarn_name,
                "Loại đóng gói": f"{pack} - {names[pack]}" if pack and names.get(pack) else pack,
                "Trạng thái": y.status.value,
                "Người tạo": y.requested_by,
                "Ngày tạo": y.requested_at,
                "Người xử lý": y.handled_by,
                "Ngày xử lý": y.handled_at,
                "Lý do từ chối / chưa tính được": y.reason,
                "Tổng (VND/kg)": vnd(y.total_vnd),
                "USD/kg": usd(y.usd_per_kg),
            }
        )
    return rows


# ---- Dòng giá của một mã ----
LINE_CONFIG = {
    **{label: money(label) for _, label in COST_ITEMS},
    "Tổng (VND/kg)": money("Tổng (VND/kg)"),
    "USD/kg": usd_col("USD/kg"),
    "% CK/PP": percent("% CK/PP"),
}


def line_rows(lines: Iterable[PriceLineDTO]) -> list[dict[str, Any]]:
    return [
        {
            "Mã dòng": line.line_code,
            "Loại dòng": line.line_type.value,
            **{label: vnd(getattr(line, field)) for field, label in COST_ITEMS},
            "Tổng (VND/kg)": vnd(line.total_vnd),
            "USD/kg": usd(line.usd_per_kg),
            "% CK/PP": pct(line.adjustment_percent),
            "Lý do CK/PP": line.adjustment_reason,
            "Đơn hàng": line.order_ref,
            "Mã kế toán": line.accounting_code or "",
        }
        for line in lines
    ]


# ---- Lịch sử giá (4.15) ----
HISTORY_CONFIG = {
    "Lúc thay đổi": datetime_col("Lúc thay đổi"),
    "Ngày hiệu lực": date_col("Ngày hiệu lực"),
    "Tổng cũ": money("Tổng cũ"),
    "Tổng mới": money("Tổng mới"),
    **{f"{label} cũ": money(f"{label} cũ") for _, label in COST_ITEMS},
    **{f"{label} mới": money(f"{label} mới") for _, label in COST_ITEMS},
}


def history_rows(history: Iterable[PriceHistoryDTO]) -> list[dict[str, Any]]:
    ordered = sorted(history, key=lambda h: h.changed_at, reverse=True)
    return [
        {
            "Mã dòng": h.line_code,
            "Lúc thay đổi": h.changed_at,
            "Người thao tác": h.changed_by,
            "Nguyên nhân": h.event.value,
            "Lần tính lại": h.batch_id or "",
            "Ngày hiệu lực": h.effective_date,
            "Tổng cũ": vnd(h.old_total),
            "Tổng mới": vnd(h.new_total),
            **{f"{label} cũ": vnd(getattr(h, f"old_{field}")) for field, label in COST_ITEMS},
            **{f"{label} mới": vnd(getattr(h, f"new_{field}")) for field, label in COST_ITEMS},
            "Lý do": h.reason,
        }
        for h in ordered
    ]


# ---- Các lần tính lại (UC-36) ----
BATCH_CONFIG = {
    "Ngày hiệu lực": date_col("Ngày hiệu lực"),
    "Lúc chạy": datetime_col("Lúc chạy"),
    "Số mã đã tính": count_col("Số mã đã tính"),
    "Số dòng thay đổi": count_col("Số dòng thay đổi"),
    "Số mã chưa tính được": count_col("Số mã chưa tính được"),
}


def batch_rows(batches: Iterable[RecalcBatchDTO]) -> list[dict[str, Any]]:
    return [
        {
            "Mã lần tính lại": b.batch_id,
            "Xưởng": str(b.factory_code),
            "Nguyên nhân": b.trigger.value,
            "Ngày hiệu lực": b.effective_date,
            "Lý do": b.reason,
            "Người chạy": b.run_by,
            "Lúc chạy": b.run_at,
            "Số mã đã tính": b.yarn_count,
            "Số dòng thay đổi": b.changed_line_count,
            "Số mã chưa tính được": b.failed_yarn_count,
        }
        for b in batches
    ]


# ---- Giá bất thường (UC-30) ----
ANOMALY_CONFIG = {
    "Chi số trước": count_col("Chi số trước"),
    "Giá trước": money("Giá trước"),
    "Chi số sau": count_col("Chi số sau"),
    "Giá sau": money("Giá sau"),
}


def price_anomaly_rows(items: Iterable[PriceAnomalyDTO]) -> list[dict[str, Any]]:
    return [
        {
            "Xưởng": a.factory_code,
            "Công nghệ": a.technology,
            "Nhóm sợi": a.yarn_group,
            "Nhóm tiêu hao": a.loss_group_key,
            "Mã trước": a.prev_code,
            "Chi số trước": plain(a.prev_count),
            "Giá trước": vnd(a.prev_total),
            "Mã sau": a.next_code,
            "Chi số sau": plain(a.next_count),
            "Giá sau": vnd(a.next_total),
            "Lý do sai": a.reason,
        }
        for a in items
    ]
