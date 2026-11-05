"""Screen 7, the data file: step 1 choose and check, step 2 read the result and save after a confirmation."""

import streamlit as st

from backend.core.base import UploadedFileDTO
from backend.core.exceptions import AppError
from backend.features.sewing_productivity import SewingProductivityController
from backend.features.sewing_productivity.dto.upload_dto import (
    CheckUploadRequest,
    SaveUploadRequest,
    UploadCheckResponse,
    UploadLogDTO,
    UploadLogListResponse,
    UploadWarningDTO,
)
from frontend.core.base_page import BasePage
from frontend.core.components import (
    data_table,
    file_upload,
    panel,
    section_title,
    show_error,
    show_success,
    stat_row,
)
from frontend.core.formatting import format_number
from frontend.core.session_state import SessionState
from frontend.features.sewing_productivity.components.report_cells import day_text

RESULT_KEYS = ("check_result", "check_error", "checked_fingerprint")


def _fingerprint(file: UploadedFileDTO) -> tuple[str, int, int]:
    return file.filename, len(file.content), hash(file.content)


def _forget_result_of_other_file(state: SessionState, file: UploadedFileDTO | None) -> None:
    """A result belongs to one file. The fingerprint is computed only while there is a result to protect."""
    checked = state.get("checked_fingerprint")
    if checked is not None and (file is None or _fingerprint(file) != checked):
        _forget_result(state)


def _forget_result(state: SessionState) -> None:
    for name in RESULT_KEYS:
        state.pop(name, None)


def _check_file(state: SessionState, feature: SewingProductivityController, file: UploadedFileDTO) -> None:
    _forget_result(state)
    state.pop("save_message", None)
    state.set("checked_fingerprint", _fingerprint(file))
    try:
        with st.spinner("Đang kiểm tra file, có thể mất khoảng một phút...", show_time=True):
            state.set("check_result", feature.check_upload(CheckUploadRequest(file=file)))
    except AppError as exc:  # the file was refused: step 2 shows why, and the rest of the page keeps working
        state.set("check_error", exc)


def _save_file(state: SessionState, feature: SewingProductivityController, file: UploadedFileDTO) -> None:
    """Runs in the full page run after the confirmation, so the backend sees who is logged in."""
    try:
        with st.spinner("Đang lưu dữ liệu, có thể mất khoảng một phút...", show_time=True):
            saved = feature.save_upload(SaveUploadRequest(file=file))
    except AppError as exc:
        state.set("check_error", exc)
        return
    _forget_result(state)
    state.set("save_message", saved.message)
    state.set("upload_version", state.get("upload_version", 0) + 1)  # a new widget key empties the file box
    st.rerun()


@st.dialog("Xác nhận lưu dữ liệu", icon=":material/save:")
def _confirm_save(page: BasePage, valid_rows: int, filename: str) -> None:
    """A dialog reruns on its own, without the logged-in user: it only leaves a flag, the page run does the saving."""
    st.write(
        f"Lưu {format_number(valid_rows)} dòng từ file {filename}? Dữ liệu đang lưu trong khoảng của file sẽ được "
        "thay bằng dữ liệu trong file. Dữ liệu ngoài khoảng giữ nguyên."
    )
    with st.container(horizontal=True):
        if st.button("Lưu", type="primary", key=page.key("save_yes")):
            page.state.set("do_save", True)
            st.rerun()
        if st.button("Huỷ", key=page.key("save_no")):
            st.rerun()


def _warning_rows(warnings: list[UploadWarningDTO]) -> list[dict[str, object]]:
    return [
        {
            "Loại": f"{item.kind}: {item.detail}" if item.detail else item.kind,
            "Ngày": day_text(item.warning_date),
            "Số lượng": item.count,
        }
        for item in warnings
    ]


def _show_check_result(page: BasePage, result: UploadCheckResponse, file: UploadedFileDTO | None) -> None:
    stat_row(
        [
            ("Số dòng đọc được", format_number(result.read_rows)),
            ("Hợp lệ", format_number(result.valid_rows)),
            ("Bị bỏ qua", format_number(result.skipped_rows)),
        ]
    )
    stat_row([("Ngày đầu", day_text(result.from_date)), ("Ngày cuối", day_text(result.to_date))])
    st.caption(
        f"Trong khoảng {day_text(result.from_date)} đến {day_text(result.to_date)}: file có "
        f"{format_number(result.valid_rows)} dòng hợp lệ, dữ liệu đang lưu có "
        f"{format_number(result.stored_rows_in_range)} dòng."
    )
    if result.target_skipped_rows:
        st.caption(
            f"Các số trên tính theo sheet Production data. Sheet Target system có thêm "
            f"{format_number(result.target_skipped_rows)} dòng bị bỏ qua, xem trong bảng dưới."
        )
    section_title("Dòng bị bỏ qua")
    data_table(
        [{"Sheet": row.sheet, "Dòng": row.row_number, "Lý do": row.reason} for row in result.skipped],
        column_config={
            "Dòng": st.column_config.NumberColumn(format="plain"),
            "Lý do": st.column_config.TextColumn(width="large"),
        },
        key=page.key("skipped"),
        empty_message="Không có dòng bị bỏ qua.",
    )
    section_title("Cảnh báo")
    data_table(
        _warning_rows(result.warnings),
        column_config={"Số lượng": st.column_config.NumberColumn(format="localized")},
        key=page.key("warnings"),
        empty_message="Không có cảnh báo.",
    )
    if result.can_save and file is not None and st.button("Lưu dữ liệu", type="primary", key=page.key("save")):
        _confirm_save(page, result.valid_rows, file.filename)


def upload_blocks(page: BasePage, feature: SewingProductivityController) -> None:
    state = page.state
    with panel(
        "Bước 1 · Chọn file dữ liệu", icon="📤", description="File .xlsx, tối đa 50 MB, phải được lưu từ Excel."
    ):
        # no file type here: a .pdf must reach the backend, which answers with the BR-01 sentence (AC-01)
        file = file_upload("Chọn file", types=(), key=page.key(f"upload_{state.get('upload_version', 0)}"))
        _forget_result_of_other_file(state, file)
        if st.button("Kiểm tra file", type="primary", disabled=file is None, key=page.key("check")) and file:
            _check_file(state, feature, file)

    if state.pop("do_save", False) and file is not None:
        _save_file(state, feature, file)

    message = state.get("save_message")
    if message:
        show_success(message)

    result, error = state.get("check_result"), state.get("check_error")
    if result is None and error is None:
        return
    with panel("Bước 2 · Kết quả kiểm tra", icon="🔎"):
        if error is not None:
            show_error(error)
        if result is not None:
            _show_check_result(page, result, file)


def _local_time_rows(logs: list[UploadLogDTO]) -> list[dict[str, object]]:
    return [
        {
            "Thời điểm": log.uploaded_at.astimezone().replace(tzinfo=None)
            if log.uploaded_at.tzinfo
            else log.uploaded_at,
            "Người tải": log.uploaded_by,
            "Tên file": log.file_name,
            "Từ ngày": log.from_date,
            "Đến ngày": log.to_date,
            "Số dòng lưu": log.saved_rows,
            "Số dòng bỏ qua": log.skipped_rows,
        }
        for log in logs
    ]


def upload_history(page: BasePage, logs: UploadLogListResponse) -> None:
    with panel("Lịch sử tải file", icon="🕘"):
        data_table(
            _local_time_rows(logs.items),
            column_config={
                "Thời điểm": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
                "Từ ngày": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Đến ngày": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Số dòng lưu": st.column_config.NumberColumn(format="localized"),
                "Số dòng bỏ qua": st.column_config.NumberColumn(format="localized"),
            },
            key=page.key("logs"),
            empty_message="Chưa có lần tải file nào.",
        )
