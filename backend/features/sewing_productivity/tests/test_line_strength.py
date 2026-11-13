"""UC-33, BR-81, BR-82: the Line Strength file saved through the upload button (AC-110, AC-111)."""

from io import BytesIO

import pytest
from openpyxl import Workbook

from backend.core.base import EmptyRequest, UploadedFileDTO
from backend.core.current_user import CurrentUser, set_current_user
from backend.core.exceptions import AppError
from backend.features.sewing_productivity.dto.upload_dto import CheckUploadRequest, SaveUploadRequest
from backend.features.sewing_productivity.models.enums import Factory
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source
from backend.features.sewing_productivity.repositories.source_repositories import (
    LineStrengthRepository,
    ProductionRecordRepository,
)
from backend.features.sewing_productivity.services.check_upload_service import CheckUploadService
from backend.features.sewing_productivity.services.list_upload_logs_service import ListUploadLogsService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService

HEADERS = ["FAC ", "LINE ", "STRONG ITEM GROUP", None, None, None, "BUYER'S STRENGTH", "CHANGEOVER SPEED", "REMARK"]
ROWS = [
    ["XM1", 1, "T-Shirt", "Pants", None, None, "CHORI", "Slow", "Chuyền đào tạo"],
    ["XM2", 14, "Pants", "T-Shirt", None, None, "MCC, MARK'S WORK", "Medium", None],
    ["XM5", 15, "Hoodie", "T-Shirt", "Jacket", "Swimsuit", "Eland ", "Slow", None],
    ["XM1", 34, None, None, None, None, None, None, None],
    ["XM9", 1, "Polo", None, None, None, None, "Fast", None],
]


def strength_file(rows: list[list[object]] = ROWS, headers: list[object] = HEADERS) -> UploadedFileDTO:
    book = Workbook()
    sheet = book.active
    sheet.title = "Sewing Line Strength (14-Jul)"
    sheet.append(headers)
    sheet.append([None, None, 1, 2, 3, 4])
    for row in rows:
        sheet.append(row)
    stream = BytesIO()
    book.save(stream)
    return UploadedFileDTO(filename="Sewing Line Strength (14-Jul-2026).xlsx", content=stream.getvalue())


@pytest.fixture(autouse=True)
def _updater():
    set_current_user(CurrentUser(username="an", full_name="Nguyễn Văn A", is_admin=True))
    yield
    set_current_user(None)


def _save(file: UploadedFileDTO):
    CheckUploadService().handle(CheckUploadRequest(file=file))
    return SaveUploadService().handle(SaveUploadRequest(file=file))


def test_ac110_br81_the_file_is_recognised_and_saved():
    check = CheckUploadService().handle(CheckUploadRequest(file=strength_file()))
    assert (check.read_rows, check.valid_rows, check.skipped_rows) == (5, 4, 1)
    assert check.skipped[0].reason == 'Dòng 7: chưa nhận diện được xưởng "XM9".'
    saved = SaveUploadService().handle(SaveUploadRequest(file=strength_file()))
    assert saved.message == "Đã lưu sở trường của 4 chuyền."
    lines = {(line.factory, line.line): line for line in LineStrengthRepository().list_all()}
    fac2 = lines[(Factory.FAC_2, "LINE 14")]
    assert (fac2.strong_groups, fac2.buyers, fac2.changeover_speed) == (
        ["Pants", "T-Shirt"],
        "MCC, MARK'S WORK",
        "Medium",
    )
    assert lines[(Factory.FAC_5, "LINE 15")].strong_groups == ["Hoodie", "T-Shirt", "Jacket", "Swimsuit"]
    assert lines[(Factory.FAC_1, "LINE 34")].strong_groups == []
    log = ListUploadLogsService().handle(EmptyRequest()).items[0]
    assert (log.status, log.sheet_counts[0].sheet, log.saved_rows) == ("Saved", "Line Strength", 4)
    assert ProductionRecordRepository().count() == 0
    assert load_report_source().last_upload_at is None  # not a data upload


def test_ac111_br82_a_new_file_replaces_the_lines_and_flags_the_others():
    _save(strength_file())
    _save(strength_file(ROWS[:2]))
    lines = {(line.factory, line.line) for line in LineStrengthRepository().list_all()}
    assert lines == {(Factory.FAC_1, "LINE 1"), (Factory.FAC_2, "LINE 14")}
    assert len(LineStrengthRepository().list_deleted()) == 2
    changes = {(c.factory, c.hidden) for c in ListUploadLogsService().handle(EmptyRequest()).items[0].changes}
    assert ("Fac 5", 1) in changes


def test_br81_missing_column_refuses_the_file_and_changes_nothing():
    _save(strength_file())
    headers = [header if header != "CHANGEOVER SPEED" else "SPEED" for header in HEADERS]
    with pytest.raises(AppError) as error:
        CheckUploadService().handle(CheckUploadRequest(file=strength_file(headers=headers)))
    assert error.value.message == (
        "File Line Strength thiếu cột: CHANGEOVER SPEED. Hãy dùng đúng file Sewing Line Strength."
    )
    assert LineStrengthRepository().count() == 4
    assert ListUploadLogsService().handle(EmptyRequest()).items[0].status == "Rejected"
