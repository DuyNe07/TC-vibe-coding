"""Screen 7, the data file: step 1 choose and check, step 2 read the result and save after a confirmation."""

import streamlit as st

from backend.core.base import UploadedFileDTO
from backend.core.exceptions import AppError
from backend.features.sewing_productivity import SewingProductivityController
from backend.features.sewing_productivity.dto.display_names import english_name
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
SAVED_RESULT = "saved_result"
UPLOAD_HELP = (
    "An .xlsx file saved from Excel, 50 MB at most. Press Check & save: the file is checked and saved in one go, "
    "then the skipped rows and warnings are listed below."
)


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
    state.pop(SAVED_RESULT, None)
    state.set("checked_fingerprint", _fingerprint(file))
    try:
        with st.spinner("Checking the file, this can take about a minute...", show_time=True):
            state.set("check_result", feature.check_upload(CheckUploadRequest(file=file)))
    except AppError as exc:  # the file was refused: step 2 shows why, and the rest of the page keeps working
        state.set("check_error", exc)


def _save_file(state: SessionState, feature: SewingProductivityController, file: UploadedFileDTO) -> None:
    """Runs in the full page run after the confirmation, so the backend sees who is logged in."""
    try:
        with st.spinner("Saving the data, this can take about a minute...", show_time=True):
            saved = feature.save_upload(SaveUploadRequest(file=file))
    except AppError as exc:
        state.set("check_error", exc)
        return
    state.set(SAVED_RESULT, state.get("check_result"))  # its warnings stay readable after the file box is emptied
    _forget_result(state)
    state.set("save_message", saved.message)
    state.set("upload_version", state.get("upload_version", 0) + 1)  # a new widget key empties the file box
    st.rerun()


def _check_and_save(state: SessionState, feature: SewingProductivityController, file: UploadedFileDTO) -> None:
    """BR-57 one button: a file the check accepts is saved at once, its skipped rows and warnings shown afterwards.

    Only a refused file stops at step 2. The daily file always ends with rows that have no date yet, so stopping on
    skipped rows would stop every day."""
    _check_file(state, feature, file)
    result: UploadCheckResponse | None = state.get("check_result")
    if result is not None and result.can_save:
        _save_file(state, feature, file)


@st.dialog("Confirm save", icon=":material/save:")
def _confirm_save(page: BasePage, valid_rows: int, filename: str) -> None:
    """A dialog reruns on its own, without the logged-in user: it only leaves a flag, the page run does the saving."""
    st.write(
        f"Save {format_number(valid_rows)} rows from {filename}? Data stored within the file's period is replaced by "
        "the file. Data outside that period stays."
    )
    with st.container(horizontal=True):
        if st.button("Save", type="primary", key=page.key("save_yes")):
            page.state.set("do_save", True)
            st.rerun()
        if st.button("Cancel", key=page.key("save_no")):
            st.rerun()


def _warning_rows(warnings: list[UploadWarningDTO]) -> list[dict[str, object]]:
    return [
        {
            "Type": f"{english_name(item.kind)}: {item.detail}" if item.detail else english_name(item.kind),
            "Date": day_text(item.warning_date),
            "Count": item.count,
        }
        for item in warnings
    ]


def _show_check_result(page: BasePage, result: UploadCheckResponse, file: UploadedFileDTO | None) -> None:
    stat_row(
        [
            ("Rows read", format_number(result.read_rows)),
            ("Valid", format_number(result.valid_rows)),
            ("Skipped", format_number(result.skipped_rows)),
        ]
    )
    stat_row([("First date", day_text(result.from_date)), ("Last date", day_text(result.to_date))])
    st.caption(
        f"From {day_text(result.from_date)} to {day_text(result.to_date)}: the file has "
        f"{format_number(result.valid_rows)} valid rows, the stored data has "
        f"{format_number(result.stored_rows_in_range)} rows."
    )
    if result.target_skipped_rows:
        st.caption(
            f"These numbers are for the Production data sheet. The Target system sheet has another "
            f"{format_number(result.target_skipped_rows)} skipped rows, listed in the table below."
        )
    section_title("Skipped rows")
    data_table(
        [{"Sheet": row.sheet, "Row": row.row_number, "Reason": row.reason} for row in result.skipped],
        column_config={
            "Row": st.column_config.NumberColumn(format="plain"),
            "Reason": st.column_config.TextColumn(width="large"),
        },
        key=page.key("skipped"),
        empty_message="No skipped rows.",
    )
    section_title("Warnings")
    data_table(
        _warning_rows(result.warnings),
        column_config={"Count": st.column_config.NumberColumn(format="localized")},
        key=page.key("warnings"),
        empty_message="No warnings.",
    )
    if result.can_save and file is not None and st.button("Save data", type="primary", key=page.key("save")):
        _confirm_save(page, result.valid_rows, file.filename)


def upload_blocks(page: BasePage, feature: SewingProductivityController) -> None:
    state = page.state
    with panel("Step 1 · Choose the data file", icon="📤", description=UPLOAD_HELP):
        # no file type here: a .pdf must reach the backend, which answers with the BR-01 sentence (AC-01)
        file = file_upload("Choose a file", types=(), key=page.key(f"upload_{state.get('upload_version', 0)}"))
        _forget_result_of_other_file(state, file)
        if st.button("Check & save", type="primary", disabled=file is None, key=page.key("check")) and file:
            _check_and_save(state, feature, file)

    if state.pop("do_save", False) and file is not None:
        _save_file(state, feature, file)

    message = state.get("save_message")
    if message:
        show_success(message)
    saved: UploadCheckResponse | None = state.get(SAVED_RESULT)
    if saved is not None and file is None:
        skipped = saved.skipped_rows + saved.target_skipped_rows
        label = f"Check result of the saved file · {format_number(skipped)} rows skipped, not saved"
        with st.expander(label, expanded=bool(skipped), icon=":material/fact_check:"):
            _show_check_result(page, saved, None)

    result, error = state.get("check_result"), state.get("check_error")
    if result is None and error is None:
        return
    with panel("Step 2 · The file was not saved", icon="🔎"):
        if error is not None:
            show_error(error)
        if result is not None:
            _show_check_result(page, result, file)


def _local_time_rows(logs: list[UploadLogDTO]) -> list[dict[str, object]]:
    return [
        {
            "Uploaded at": log.uploaded_at.astimezone().replace(tzinfo=None)
            if log.uploaded_at.tzinfo
            else log.uploaded_at,
            "Uploaded by": log.uploaded_by,
            "File name": log.file_name,
            "From": log.from_date,
            "To": log.to_date,
            "Rows saved": log.saved_rows,
            "Rows skipped": log.skipped_rows,
        }
        for log in logs
    ]


def upload_history(page: BasePage, logs: UploadLogListResponse) -> None:
    with panel("Upload history", icon="🕘"):
        data_table(
            _local_time_rows(logs.items),
            column_config={
                "Uploaded at": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
                "From": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "To": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Rows saved": st.column_config.NumberColumn(format="localized"),
                "Rows skipped": st.column_config.NumberColumn(format="localized"),
            },
            key=page.key("logs"),
            empty_message="No uploads yet.",
        )
