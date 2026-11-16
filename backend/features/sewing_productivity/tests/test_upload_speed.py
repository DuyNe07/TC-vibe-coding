"""Fix log 2026-11-16: "Check & save" was slow - the file was read and checked twice, and a second save could run
alongside the first. The save now returns the check result of its own reading, and only one save runs at a time."""

from datetime import date

import pytest

from backend.core.current_user import CurrentUser, set_current_user
from backend.features.sewing_productivity.dto.upload_dto import CheckUploadRequest, SaveUploadRequest
from backend.features.sewing_productivity.exceptions import SaveInProgressError
from backend.features.sewing_productivity.repositories.source_repositories import ProductionRecordRepository
from backend.features.sewing_productivity.services import save_upload_service
from backend.features.sewing_productivity.services.check_upload_service import CheckUploadService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService
from backend.features.sewing_productivity.tests.workbook_factory import FAC2, data_file, production, worker

DAY = date(2026, 10, 24)


@pytest.fixture(autouse=True)
def _updater():
    set_current_user(CurrentUser(username="an", is_admin=True))
    yield
    set_current_user(None)


def _file():
    rows = [production(DAY, FAC2, po="PO-1.1"), production(DAY, FAC2, po="PO-2.1", smv=None), [None, "x"]]
    return data_file(rows, [], [worker(DAY)])  # no sewers for Fac 2 that day: a warning; one row skipped


def test_save_returns_the_check_of_its_own_reading():
    expected = CheckUploadService().handle(CheckUploadRequest(file=_file()))
    saved = SaveUploadService().handle(SaveUploadRequest(file=_file()))
    assert saved.check is not None
    assert (saved.check.valid_rows, saved.check.skipped_rows, saved.check.stored_rows_in_range) == (
        expected.valid_rows,
        expected.skipped_rows,
        expected.stored_rows_in_range,
    )
    assert [w.kind for w in saved.check.warnings] == [w.kind for w in expected.warnings]
    assert len(ProductionRecordRepository().list_all()) == 2


def test_save_reads_the_workbook_once(monkeypatch):
    calls = []
    original = save_upload_service.RawWorkbookBuilder.build

    def counted(self):
        calls.append(1)
        return original(self)

    monkeypatch.setattr(save_upload_service.RawWorkbookBuilder, "build", counted)
    SaveUploadService().handle(SaveUploadRequest(file=_file()))
    assert len(calls) == 1


def test_a_second_save_while_one_runs_is_refused_and_writes_nothing():
    assert save_upload_service._SAVING.acquire(blocking=False)
    try:
        with pytest.raises(SaveInProgressError):
            SaveUploadService().handle(SaveUploadRequest(file=_file()))
    finally:
        save_upload_service._SAVING.release()
    assert ProductionRecordRepository().list_all() == []
    assert SaveUploadService().handle(SaveUploadRequest(file=_file())).saved_rows == 2  # free again afterwards
