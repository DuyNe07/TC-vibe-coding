"""Screen 6, Loại tải "Khai báo thành phần sợi pha" (UC-44, UC-45; 5.7)."""

from datetime import date
from typing import Any

import streamlit as st

from backend.features.yarn_costing.dto.common_dto import ActorDTO
from backend.features.yarn_costing.dto.import_dto import ComponentImportResponse, ImportComponentFileRequest
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, file_upload, panel, stat_row
from frontend.core.formatting import format_number
from frontend.features.yarn_costing.components.columns import count_col
from frontend.features.yarn_costing.components.dialogs import confirm_dialog
from frontend.features.yarn_costing.components.display import fmt_date, pct_exact
from frontend.features.yarn_costing.components.permissions import action_state, explain
from frontend.features.yarn_costing.components.recalc_diff import open_recalc_diff_dialog

PREVIEW_KEY = "component_import_preview"
DONE_KEY = "component_import_done"
LOSS_FORMAT = "%.4f"


def _stage_columns(result: ComponentImportResponse) -> list[str]:
    used = {code for g in result.groups for code in (*g.old_losses, *g.new_losses)}
    return [code for code in result.stage_codes if code in used]


def _group_rows(result: ComponentImportResponse) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    stages = _stage_columns(result)
    rows = []
    for g in result.groups:
        row: dict[str, Any] = {
            "Dòng": g.excel_row,
            "Nhóm": g.group_key,
            "Loại cũ": g.old_level or "(nhóm mới)",
            "Loại mới": g.new_level,
            "Thành phần": g.components_text,
            "Số mã bị ảnh hưởng": g.affected_count,
        }
        for code in stages:
            row[f"{code} cũ (%)"] = pct_exact(g.old_losses.get(code, 0))
            row[f"{code} mới (%)"] = pct_exact(g.new_losses.get(code, 0))
        rows.append(row)
    config: dict[str, Any] = {"Dòng": count_col("Dòng"), "Số mã bị ảnh hưởng": count_col("Số mã bị ảnh hưởng")}
    for code in stages:
        for suffix in ("cũ", "mới"):
            label = f"{code} {suffix} (%)"
            config[label] = st.column_config.NumberColumn(label, format=LOSS_FORMAT)
    return rows, config


def _result_tables(page: BasePage, result: ComponentImportResponse, key: str) -> None:
    stat_row(
        [
            ("Nhóm hợp lệ", format_number(result.valid_count)),
            ("Nhóm tạo mới", format_number(result.created_count)),
            ("Dòng bị loại", format_number(result.rejected_count)),
            ("Mã bị ảnh hưởng", format_number(result.affected_count)),
            ("Mã không ghép được thành phần", format_number(result.unmatched_count)),
        ]
    )
    rows, config = _group_rows(result)
    st.markdown("**Nhóm hợp lệ** (tiêu hao cũ → mới, %)")
    data_table(rows, column_config=config, empty_message="Không có nhóm hợp lệ.", key=page.key(f"{key}.groups"))
    st.markdown("**Dòng bị loại**")
    data_table(
        [{"Dòng": r.excel_row, "Nhóm": r.key, "Lý do": r.reason} for r in result.rejected_rows],
        column_config={"Dòng": count_col("Dòng")},
        empty_message="Không có dòng nào bị loại.",
        key=page.key(f"{key}.rejected"),
    )
    st.markdown("**Mã không ghép được thành phần**")
    data_table(
        [
            {
                "Mã": u.yarn_code,
                "Tên sợi": u.yarn_name,
                "Thành phần": u.material_label,
                "Dây chuyền": u.carding_stage,
                "Nhóm": u.group_key,
            }
            for u in result.unmatched
        ],
        empty_message="Không có mã nào.",
        key=page.key(f"{key}.unmatched"),
    )


def render_component_import(
    page: BasePage, feature: Any, actor: ActorDTO | None, factory: str, effective: date
) -> None:
    """UC-45: tải file, 'Kiểm tra file' (không lưu), 'Lưu N nhóm hợp lệ' (hỏi xác nhận), kết quả + chênh lệch."""
    with panel("Khai báo thành phần sợi pha", icon="🧩"):
        st.caption(
            "Mỗi dòng của sheet 'Khai bao thanh phan' là một nhóm tiêu hao: Thành phần 1-5 và Tỷ lệ (%). Nhóm được khai "
            "báo chuyển thành nhóm sợi pha, tiêu hao tính theo thành phần; các mã dùng nhóm được tính lại."
        )
        reason = st.text_input("Lý do", max_chars=500, key=page.key(f"comp.reason.{factory}"))
        file = file_upload(
            "File khai báo thành phần",
            types=[".xlsx", ".xlsm", ".xls"],
            key=page.key(f"comp.file.{factory}"),
            help="Tối đa 60 MB, 10.000 dòng. Dùng file mẫu hoặc bản nháp đã có các cột Nhóm sợi pha, Thành phần, Tỷ lệ.",
        )
        disabled, why = action_state(page.state, "UC-45", factory)
        signature = (file.filename, len(file.content), factory) if file is not None else None
        if st.button(
            "Kiểm tra file",
            type="primary",
            icon="🔍",
            key=page.key(f"comp.check.{factory}"),
            disabled=disabled or file is None,
            help=why or ("Vui lòng chọn file Excel." if file is None else None),
        ):
            preview = feature.import_component_file(
                ImportComponentFileRequest(
                    actor=actor or ActorDTO(),
                    factory_code=factory,
                    file=file,
                    effective_date=effective,
                    reason=reason,
                    commit=False,
                )
            )
            page.state.set(PREVIEW_KEY, {"sig": signature, "result": preview})
            page.state.pop(DONE_KEY)
        explain(why)

    stored = page.state.get(PREVIEW_KEY)
    if stored and file is not None and stored["sig"] == signature:
        preview: ComponentImportResponse = stored["result"]
        with panel("Kết quả kiểm tra file", icon="📊"):
            st.info(preview.message)
            _result_tables(page, preview, "comp.preview")
            count = preview.valid_count
            if st.button(
                f"Lưu {count} nhóm hợp lệ",
                type="primary",
                icon="💾",
                key=page.key(f"comp.commit.{factory}"),
                disabled=disabled or count == 0,
                help=why or ("Không có nhóm hợp lệ để lưu." if count == 0 else None),
            ):
                request = ImportComponentFileRequest(
                    actor=actor or ActorDTO(),
                    factory_code=factory,
                    file=file,
                    effective_date=effective,
                    reason=reason,
                    commit=True,
                )

                def action() -> str:
                    result = feature.import_component_file(request)
                    page.state.set(DONE_KEY, result)
                    page.state.pop(PREVIEW_KEY)
                    return result.message

                confirm_dialog(
                    page.state,
                    page.key(f"dlg.comp_commit.{factory}"),
                    "Xác nhận khai báo thành phần sợi pha",
                    f"Lưu thành phần cho {count} nhóm của xưởng {factory} từ file {file.filename}? Tiêu hao các nhóm này "
                    f"sẽ tính theo thành phần và {preview.affected_count} mã bị ảnh hưởng được tính lại với ngày hiệu "
                    f"lực {fmt_date(effective)}.",
                    "Lưu và tính lại",
                    action,
                )

    done: ComponentImportResponse | None = page.state.get(DONE_KEY)
    if done is not None:
        with panel("Kết quả lần lưu vừa rồi", icon="✅"):
            _result_tables(page, done, "comp.done")
            left, right = st.columns(2)
            if done.batch_id and left.button("Xem chênh lệch", icon="🔁", key=page.key("comp.diff")):
                open_recalc_diff_dialog(feature, done.batch_id, page.key(f"comp.diff_dlg.{done.batch_id}"))
            if done.result_file is not None:
                with right:
                    download_button(done.result_file, label="Tải kết quả nhập file", key=page.key("comp.result_dl"))
