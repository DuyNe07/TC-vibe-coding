"""Screen 7, upload history (UC-03, sửa 2026-11-09): every upload, saved or rejected, with its totals; pick a row to
see what that upload did (BR-72 to BR-74)."""

import streamlit as st

from backend.features.sewing_productivity.dto.display_names import english_name
from backend.features.sewing_productivity.dto.upload_dto import UploadLogDTO, UploadLogListResponse
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, panel, section_title
from frontend.features.sewing_productivity.components.report_cells import day_text

NO_DETAILS = "Lần tải trước 09/11/2026 không có chi tiết."
ROW_KEY = "Upload"  # hidden position of the row, to find the picked upload again
LOCALIZED = st.column_config.NumberColumn(format="localized")


def _local(log: UploadLogDTO) -> object:
    return log.uploaded_at.astimezone().replace(tzinfo=None) if log.uploaded_at.tzinfo else log.uploaded_at


def _history_rows(logs: list[UploadLogDTO]) -> list[dict[str, object]]:
    return [
        {
            ROW_KEY: index,
            "Uploaded at": _local(log),
            "Uploaded by": log.uploaded_by,
            "File name": log.file_name,
            "Status": log.status,
            "From": log.from_date,
            "To": log.to_date,
            "Rows saved": log.saved_rows,
            "Rows skipped": log.skipped_rows,
            "Added": log.added,
            "Updated": log.updated,
            "Hidden": log.hidden,
        }
        for index, log in enumerate(logs)
    ]


def _details(page: BasePage, log: UploadLogDTO) -> None:
    """BR-72 to BR-74 the picked upload, block by block."""
    title = f"{log.file_name}, {_local(log):%d/%m/%Y %H:%M}, {log.uploaded_by}"
    with panel(f"Upload details: {title}", icon="🔍"):
        if not log.has_details:
            st.info(NO_DETAILS, icon=":material/info:")
            return
        if log.reject_reason:
            st.error(f"Rejected, nothing was saved. Reason shown to the user: {log.reject_reason}")
            return
        section_title("Rows per sheet")
        data_table(
            [
                {"Sheet": c.sheet, "Read": c.read_rows, "Valid": c.valid_rows, "Skipped": c.skipped_rows}
                for c in log.sheet_counts
            ],
            column_config={name: LOCALIZED for name in ("Read", "Valid", "Skipped")},
            key=page.key("log_sheets"),
        )
        section_title("Changes per factory")
        data_table(
            [
                {
                    "Sheet": c.sheet,
                    "Factory": english_name(c.factory),
                    "Added": c.added,
                    "Updated": c.updated,
                    "Hidden": c.hidden,
                }
                for c in log.changes
            ],
            column_config={name: LOCALIZED for name in ("Added", "Updated", "Hidden")},
            key=page.key("log_changes"),
            empty_message="Nothing changed: the stored data was already the same as the file.",
        )
        section_title("Skipped rows")
        if log.skipped_rows > len(log.skipped):
            st.caption(f"The first {len(log.skipped)} of {log.skipped_rows} skipped rows are kept.")
        data_table(
            [{"Sheet": row.sheet, "Row": row.row_number, "Reason": row.reason} for row in log.skipped],
            column_config={
                "Row": st.column_config.NumberColumn(format="plain"),
                "Reason": st.column_config.TextColumn(width="large"),
            },
            key=page.key("log_skipped"),
            empty_message="No skipped rows.",
        )
        section_title("Warnings")
        data_table(
            [
                {
                    "Type": f"{english_name(item.kind)}: {item.detail}" if item.detail else english_name(item.kind),
                    "Date": day_text(item.warning_date),
                    "Count": item.count,
                }
                for item in log.warnings
            ],
            column_config={"Count": LOCALIZED},
            key=page.key("log_warnings"),
            empty_message="No warnings.",
        )


def upload_history(page: BasePage, logs: UploadLogListResponse) -> None:
    with panel("Upload history", icon="🕘", description="Pick a row to see what that upload did."):
        picked = data_table(
            _history_rows(logs.items),
            column_config={
                "Uploaded at": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
                "From": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "To": st.column_config.DateColumn(format="DD/MM/YYYY"),
                **{name: LOCALIZED for name in ("Rows saved", "Rows skipped", "Added", "Updated", "Hidden")},
            },
            column_order=[
                "Uploaded at",
                "Uploaded by",
                "File name",
                "Status",
                "From",
                "To",
                "Rows saved",
                "Rows skipped",
                "Added",
                "Updated",
                "Hidden",
            ],  # fmt: skip
            selection="single",
            key=page.key("logs"),
            empty_message="No uploads yet.",
        )
    if picked:
        _details(page, logs.items[int(picked[0][ROW_KEY])])
