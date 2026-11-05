"""Screen 6, Loại tải "Đánh dấu không sản xuất" (UC-48; 5.8, bổ sung 2026-11-05)."""

from typing import Any

import streamlit as st

from backend.features.yarn_costing.dto.import_dto import ImportNotProducedFileRequest, NotProducedImportResponse
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, file_upload, panel, stat_row
from frontend.core.formatting import format_number
from frontend.features.yarn_costing.components.columns import count_col
from frontend.features.yarn_costing.components.dialogs import confirm_dialog
from frontend.features.yarn_costing.components.permissions import action_state, explain

PREVIEW_KEY = "not_produced_preview"
DONE_KEY = "not_produced_done"
SKIP_PREFIX = "Bỏ qua: "


def _result_tables(page: BasePage, result: NotProducedImportResponse, key: str) -> None:
    stat_row(
        [
            ("Mã hợp lệ", format_number(result.valid_count)),
            ("Bản ĐCNSM kèm theo", format_number(result.revision_count)),
            ("Dòng giá sẽ gỡ" if not result.committed else "Dòng giá đã gỡ", format_number(result.line_count)),
            ("Dòng bị loại", format_number(result.rejected_count)),
            ("Dòng bỏ qua", format_number(result.skipped_count)),
        ]
    )
    only_errors = st.toggle("Chỉ hiện dòng lỗi", key=page.key(f"{key}.only_errors"))
    if not only_errors:
        st.markdown("**Mã hợp lệ**")
        data_table(
            [
                {
                    "Dòng": r.excel_row,
                    "Mã": r.yarn_code,
                    "Tên sợi": r.yarn_name,
                    "Trạng thái hiện tại": r.status,
                    "Số bản": r.version_count,
                    "Số dòng giá sẽ gỡ": r.line_count,
                    "Lý do": r.reason,
                }
                for r in result.valid_rows
            ],
            column_config={
                "Dòng": count_col("Dòng"),
                "Số bản": count_col("Số bản"),
                "Số dòng giá sẽ gỡ": count_col("Số dòng giá sẽ gỡ"),
            },
            empty_message="Không có mã hợp lệ.",
            key=page.key(f"{key}.valid"),
        )
    st.markdown("**Dòng bị loại / bỏ qua**")
    data_table(
        [{"Dòng": r.excel_row, "Mã": r.key, "Lý do": r.reason} for r in result.rejected_rows],
        column_config={"Dòng": count_col("Dòng")},
        empty_message="Không có dòng nào bị loại.",
        key=page.key(f"{key}.rejected"),
    )


def render_not_produced_import(page: BasePage, feature: Any, factory: str) -> None:
    """UC-48: tải file (Mã, Lý do), 'Kiểm tra file' (không lưu), 'Lưu N mã hợp lệ' (hỏi xác nhận)."""
    with panel("Đánh dấu không sản xuất", icon="🚫"):
        st.caption(
            "Mỗi dòng của sheet đầu tiên là một mã: cột 'Mã' và 'Lý do' bắt buộc, các cột khác được bỏ qua. Mã gốc được "
            "đánh dấu cùng mọi bản ĐCNSM; các dòng giá của mã bị gỡ khỏi bảng giá (số cũ còn trong Lịch sử giá)."
        )
        file = file_upload(
            "File danh sách mã",
            types=[".xlsx", ".xlsm", ".xls"],
            key=page.key(f"np.file.{factory}"),
            help="Tối đa 60 MB, 10.000 dòng. Dùng file mẫu hoặc file có 2 cột Mã, Lý do.",
        )
        disabled, why = action_state("UC-48", factory)
        signature = (file.filename, len(file.content), factory) if file is not None else None
        if st.button(
            "Kiểm tra file",
            type="primary",
            icon="🔍",
            key=page.key(f"np.check.{factory}"),
            disabled=disabled or file is None,
            help=why or ("Vui lòng chọn file Excel." if file is None else None),
        ):
            preview = feature.import_not_produced_file(
                ImportNotProducedFileRequest(factory_code=factory, file=file, commit=False)
            )
            page.state.set(PREVIEW_KEY, {"sig": signature, "result": preview})
            page.state.pop(DONE_KEY)
        explain(why)

    stored = page.state.get(PREVIEW_KEY)
    if stored and file is not None and stored["sig"] == signature:
        preview: NotProducedImportResponse = stored["result"]
        with panel("Kết quả kiểm tra file", icon="📊"):
            st.info(preview.message)
            _result_tables(page, preview, "np.preview")
            count = preview.valid_count
            if st.button(
                f"Lưu {count} mã hợp lệ",
                type="primary",
                icon="💾",
                key=page.key(f"np.commit.{factory}"),
                disabled=disabled or count == 0,
                help=why or ("Không có mã hợp lệ để lưu." if count == 0 else None),
            ):
                request = ImportNotProducedFileRequest(factory_code=factory, file=file, commit=True)

                def action() -> str:
                    result = feature.import_not_produced_file(request)
                    page.state.set(DONE_KEY, result)
                    page.state.pop(PREVIEW_KEY)
                    return result.message

                confirm_dialog(
                    page.state,
                    page.key(f"dlg.np_commit.{factory}"),
                    "Xác nhận đánh dấu Không sản xuất",
                    f"Đánh dấu {count} mã của xưởng {factory} (kèm {preview.revision_count} bản ĐCNSM) là Không sản "
                    f"xuất? {preview.line_count} dòng giá sẽ bị gỡ khỏi bảng giá.",
                    "Đánh dấu",
                    action,
                )

    done: NotProducedImportResponse | None = page.state.get(DONE_KEY)
    if done is not None:
        with panel("Kết quả lần lưu vừa rồi", icon="✅"):
            _result_tables(page, done, "np.done")
            if done.result_file is not None:
                download_button(done.result_file, label="Tải kết quả nhập file", key=page.key("np.result_dl"))
