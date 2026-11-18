"""BR-72, BR-73, BR-74, UC-01 / UC-02 / UC-03 (sửa 2026-11-09): every upload kept in the history (AC-94 to AC-98)."""

from datetime import UTC, date, datetime

import pytest

from backend.core.base import EmptyRequest, UploadedFileDTO
from backend.core.current_user import CurrentUser, set_current_user
from backend.core.exceptions import AppError, BusinessRuleViolation
from backend.features.sewing_productivity.dto.upload_dto import CheckUploadRequest, SaveUploadRequest, UploadLogDTO
from backend.features.sewing_productivity.models.enums import UploadStatus
from backend.features.sewing_productivity.models.settings_records import UploadLog
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source
from backend.features.sewing_productivity.repositories.source_repositories import (
    ProductionRecordRepository,
    UploadLogRepository,
)
from backend.features.sewing_productivity.services.check_upload_service import CheckUploadService
from backend.features.sewing_productivity.services.list_upload_logs_service import ListUploadLogsService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService
from backend.features.sewing_productivity.tests.workbook_factory import FAC2, FAC3, FAC5, data_file, production

BR01 = (
    "File phải có định dạng .xlsx, không quá 50 MB và mỗi sheet không quá 200.000 dòng. Hãy kiểm tra lại rồi tải lên."
)
BR02_WORKER = "File thiếu sheet: Worker. Hãy dùng đúng file Data sewing."


@pytest.fixture(autouse=True)
def _updater():
    set_current_user(CurrentUser(username="an", full_name="Nguyễn Văn A", is_admin=True))
    yield
    set_current_user(None)


def _check_and_save(file: UploadedFileDTO) -> None:
    """BR-57: the button checks, then saves a file the check accepts."""
    CheckUploadService().handle(CheckUploadRequest(file=file))
    SaveUploadService().handle(SaveUploadRequest(file=file))


def _logs() -> list[UploadLogDTO]:
    return ListUploadLogsService().handle(EmptyRequest()).items


def _changes(log: UploadLogDTO) -> dict[tuple[str, str], tuple[int, int, int]]:
    return {(c.sheet, c.factory): (c.added, c.updated, c.hidden) for c in log.changes}


def test_ac94_br73_added_updated_hidden_per_sheet_and_factory():
    first = [production(factory=FAC2), production(factory=FAC5, line="LINE 3")]
    _check_and_save(data_file(first))
    second = [production(factory=FAC2, qty=150), production(factory=FAC3, line="LINE 2")]
    _check_and_save(data_file(second))
    newest = _logs()[0]
    assert newest.status == UploadStatus.SAVED.value
    changes = _changes(newest)
    assert changes[("Production data", "Fac 2")] == (0, 1, 0)
    assert changes[("Production data", "Fac 3")] == (1, 0, 0)
    assert changes[("Production data", "Fac 5")] == (0, 0, 1)
    assert (newest.added, newest.hidden) == (sum(c.added for c in newest.changes), 1)
    assert len(ProductionRecordRepository().list_deleted()) == 1  # hidden = flagged, never removed


def test_br73_same_file_twice_changes_nothing():
    _check_and_save(data_file())
    _check_and_save(data_file())
    newest = _logs()[0]
    assert newest.changes == []
    assert (newest.added, newest.updated, newest.hidden) == (0, 0, 0)


def test_ac95_br72_sheet_counts_skipped_rows_and_warnings_are_kept():
    rows = [production(), production(day=date(2026, 10, 25), line="LINE 2"), production(po=None, color="X")]
    _check_and_save(data_file(rows, worker_rows=[]))
    log = _logs()[0]
    sheets = {count.sheet: (count.read_rows, count.valid_rows, count.skipped_rows) for count in log.sheet_counts}
    assert sheets["Production data"] == (3, 2, 1)
    assert [(row.sheet, row.row_number) for row in log.skipped] == [("Production data", 5)]
    assert "PO#" in log.skipped[0].reason
    assert log.skipped_rows == 1
    no_workers = [item for item in log.warnings if item.warning_date is not None]
    assert {item.warning_date for item in no_workers} >= {date(2026, 10, 24), date(2026, 10, 25)}


def test_ac96_br74_refused_files_are_kept_as_rejected_with_the_sentence_shown():
    _check_and_save(data_file())
    last_saved = load_report_source().last_upload_at
    for file, sentence in (
        (UploadedFileDTO(filename="report.pdf", content=b"%PDF"), BR01),
        (data_file(skip_sheet="Worker", filename="no worker.xlsx"), BR02_WORKER),
    ):
        with pytest.raises(AppError) as error:
            CheckUploadService().handle(CheckUploadRequest(file=file))
        assert error.value.message == sentence
        log = _logs()[0]
        assert (log.status, log.file_name, log.reject_reason) == ("Rejected", file.filename, sentence)
        assert (log.saved_rows, log.from_date) == (0, None)
    assert ProductionRecordRepository().count() == 1
    assert load_report_source().last_upload_at == last_saved


def test_br74_a_file_refused_by_the_save_itself_is_kept_too():
    with pytest.raises(AppError):
        SaveUploadService().handle(SaveUploadRequest(file=UploadedFileDTO(filename="x.pdf", content=b"%PDF")))
    assert [(log.status, log.reject_reason) for log in _logs()] == [("Rejected", BR01)]


def test_ac97_a_person_without_the_role_leaves_no_history_row():
    set_current_user(CurrentUser(username="viewer", permissions=frozenset({"sewing_productivity"})))
    for service, request in (
        (CheckUploadService(), CheckUploadRequest(file=data_file())),
        (SaveUploadService(), SaveUploadRequest(file=data_file())),
    ):
        with pytest.raises(BusinessRuleViolation):
            service.handle(request)
    assert UploadLogRepository().count() == 0


def test_ac98_rows_saved_before_have_no_details_and_still_read():
    UploadLogRepository().add(
        UploadLog(
            uploaded_at=datetime(2026, 11, 5, 8, 30, tzinfo=UTC),
            uploaded_by="Nguyễn Văn A",
            file_name="Data sewing 2026.xlsx",
            from_date=date(2026, 1, 2),
            to_date=date(2026, 11, 4),
            saved_rows=32050,
            skipped_rows=0,
        )
    )
    log = _logs()[0]
    assert (log.status, log.has_details) == ("Saved", False)
    assert (log.added, log.updated, log.hidden) == (None, None, None)
    assert log.sheet_counts == [] and log.skipped == []
