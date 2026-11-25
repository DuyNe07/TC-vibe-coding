"""Read-only tables of the fabric specs (Mộc / Thành phẩm) and of the yarn rows (Screen 2 tab and Screen 4 detail)."""

from collections.abc import Sequence
from typing import Any

import streamlit as st

from backend.features.woven_costing.dto.fabric_dto import FabricSpecsDTO, FabricYarnDTO
from frontend.core.components import data_table
from frontend.features.woven_costing.components.labels import FLAG, num, text

SPEC_FIELDS: tuple[tuple[str, str], ...] = (
    ("Khổ (cm)", "width_cm"),
    ("Khổ cắt (cm)", "cut_width_cm"),
    ("g/m2", "gsm"),
    ("g/m", "g_per_m"),
    ("Mật độ dọc (sợi/10 cm)", "warp_density"),
    ("Mật độ ngang (sợi/10 cm)", "weft_density"),
)
YARN_KIND_OPTIONS = ["Sợi đơn", "Sợi se"]
DIRECTION_OPTIONS = ["WARP", "WEFT"]


def spec_table(
    specs: FabricSpecsDTO,
    *,
    greige_m_per_kg: Any = None,
    finished_m_per_kg: Any = None,
    overridden: Sequence[str] = (),
) -> None:
    rows: list[dict[str, Any]] = []
    for label, field in SPEC_FIELDS:
        greige, finished = f"greige_{field}", f"finished_{field}"
        rows.append(
            {
                "Thông số": label,
                "Mộc": num(getattr(specs, greige)),
                "Thành phẩm": num(getattr(specs, finished)),
                "⚑": FLAG if greige in overridden or finished in overridden else "",
            }
        )
    if greige_m_per_kg is not None or finished_m_per_kg is not None:
        rows.append({"Thông số": "m/kg", "Mộc": num(greige_m_per_kg), "Thành phẩm": num(finished_m_per_kg), "⚑": ""})
    data_table(
        rows,
        column_config={
            "Mộc": st.column_config.NumberColumn("Mộc", format="localized"),
            "Thành phẩm": st.column_config.NumberColumn("Thành phẩm", format="localized"),
            "⚑": st.column_config.TextColumn("⚑", width="small"),
        },
    )


def yarn_rows(yarns: Sequence[FabricYarnDTO], full: bool = False) -> list[dict[str, Any]]:
    rows = []
    for y in yarns:
        row: dict[str, Any] = {"Hướng": text(y.direction), "STT": y.seq}
        if full:
            row["Tên sợi đầy đủ"] = y.full_yarn_name
            row["YCODE"] = y.yarn_code
        row |= {
            "Tên sợi": y.yarn_name,
            "Tỷ lệ (%)": num(y.rate),
            "Loại sợi": text(y.yarn_kind),
        }
        if full:
            row["YCODE gốc"] = y.raw_yarn_code
        row |= {"Sợi gốc": y.raw_yarn_name, "Tỷ lệ sợi gốc (%)": num(y.raw_rate), "T/M": y.twist_tpm}
        rows.append(row)
    return rows


def yarn_table(yarns: Sequence[FabricYarnDTO], *, full: bool = False, empty_message: str = "Chưa có dòng sợi.") -> None:
    data_table(
        yarn_rows(yarns, full),
        column_config={
            "STT": st.column_config.NumberColumn("STT", width="small"),
            "Tỷ lệ (%)": st.column_config.NumberColumn("Tỷ lệ (%)", format="%.2f"),
            "Tỷ lệ sợi gốc (%)": st.column_config.NumberColumn("Tỷ lệ sợi gốc (%)", format="%.2f"),
        },
        empty_message=empty_message,
    )
