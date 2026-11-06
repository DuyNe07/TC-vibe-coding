"""UC-01, UC-02, UC-03: the data file, re-uploads and the upload history (AC-01 to AC-13)."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from backend.core.base import EmptyRequest, UploadedFileDTO
from backend.core.current_user import CurrentUser, set_current_user
from backend.core.exceptions import BusinessRuleViolation
from backend.features.sewing_productivity.dto.overview_dto import OverviewRequest
from backend.features.sewing_productivity.dto.upload_dto import CheckUploadRequest, SaveUploadRequest
from backend.features.sewing_productivity.exceptions import UploadFileError
from backend.features.sewing_productivity.models.enums import Factory
from backend.features.sewing_productivity.repositories.source_repositories import (
    ProductionRecordRepository,
    TargetRecordRepository,
    UploadLogRepository,
    WorkerRecordRepository,
)
from backend.features.sewing_productivity.services.check_upload_service import CheckUploadService
from backend.features.sewing_productivity.services.get_overview_service import GetOverviewService
from backend.features.sewing_productivity.services.list_upload_logs_service import ListUploadLogsService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService
from backend.features.sewing_productivity.tests.workbook_factory import (
    FAC2,
    PRODUCTION_HEADERS,
    data_file,
    production,
    target,
    worker,
)

BR01 = (
    "File phải có định dạng .xlsx, không quá 50 MB và mỗi sheet không quá 200.000 dòng. Hãy kiểm tra lại rồi tải lên."
)


@pytest.fixture(autouse=True)
def _no_user():
    set_current_user(None)
    yield
    set_current_user(None)


def check(file: UploadedFileDTO):
    return CheckUploadService().handle(CheckUploadRequest(file=file))


def save(file: UploadedFileDTO):
    return SaveUploadService().handle(SaveUploadRequest(file=file))


def test_ac01_pdf_is_refused_with_br01() -> None:
    with pytest.raises(BusinessRuleViolation) as error:
        check(UploadedFileDTO(filename="report.pdf", content=b"%PDF"))
    assert error.value.message == BR01


def test_br01_broken_workbook_is_refused() -> None:
    with pytest.raises(UploadFileError) as error:
        check(UploadedFileDTO(filename="broken.xlsx", content=b"not a workbook"))
    assert error.value.message == BR01


def test_ac02_missing_sheet_keeps_stored_data() -> None:
    save(data_file())
    with pytest.raises(BusinessRuleViolation) as error:
        check(data_file(skip_sheet="Worker"))
    assert error.value.message == "File thiếu sheet: Worker. Hãy dùng đúng file Data sewing."
    assert ProductionRecordRepository().count() == 1


def test_ac03_missing_column_names_sheet_and_column() -> None:
    headers = [header if header != "Price" else "Other" for header in PRODUCTION_HEADERS]
    with pytest.raises(BusinessRuleViolation) as error:
        check(data_file(production_headers=headers))
    assert error.value.message == "Sheet Production data thiếu cột: Price. Hãy kiểm tra dòng tiêu đề của sheet."


def test_quantity_header_accepts_the_correct_spelling() -> None:
    headers = ["Product Inline Quantity" if h == "Product Inline Quantiy" else h for h in PRODUCTION_HEADERS]
    assert check(data_file(production_headers=headers)).valid_rows == 1


def test_ac04_file_without_formula_results() -> None:
    with pytest.raises(BusinessRuleViolation) as error:
        check(data_file([production(standard=None)]))
    assert error.value.message == "File chưa có kết quả công thức. Hãy mở file bằng Excel, lưu lại rồi tải lên."


def test_ac05_row_without_order_is_listed_and_others_stay_valid() -> None:
    result = check(data_file([production(), production(po=None, color="RED")]))
    assert (result.read_rows, result.valid_rows, result.skipped_rows, result.can_save) == (2, 1, 1, True)
    assert result.skipped[0].row_number == 4
    assert result.skipped[0].reason == "Dòng 4: thiếu hoặc sai PO#."


def test_ac06_unknown_factory_is_listed() -> None:
    result = check(data_file([production(), production(factory="XYZ-Factory 9")]))
    assert result.skipped[0].reason == 'Dòng 4: chưa nhận diện được xưởng "XYZ-Factory 9".'


def test_br16_wrong_target_row_is_listed_and_blank_row_ignored() -> None:
    rows = [target(), target(line="Line 3"), [None, None, "only a name", None, None, None, None, None]]
    result = check(data_file(target_rows=rows))
    assert result.target_skipped_rows == 1
    assert result.skipped[0].sheet == "Target system"
    assert result.skipped[0].reason == "Sheet Target system, dòng 3: sai Line."


def test_ac07_check_saves_nothing_and_reports_the_period() -> None:
    result = check(data_file([production(day=date(2026, 10, 24)), production(day="2026/10/26", color="RED")]))
    assert ProductionRecordRepository().count() == 0
    assert (result.from_date, result.to_date, result.valid_rows) == (date(2026, 10, 24), date(2026, 10, 26), 2)
    assert result.stored_rows_in_range == 0


def test_style_number_is_kept_as_text_without_decimals() -> None:
    save(data_file([production(style=796470.0), production(style=796471, color="RED")]))
    assert sorted(record.style for record in ProductionRecordRepository().list_all()) == ["796470", "796471"]


def test_worker_reads_column_c_and_first_sf_columns() -> None:
    save(
        data_file(
            worker_rows=[worker(sf2=20, sfvl=700), worker(day="2026/10/25"), ["total", None, "n/a", 1, 1, 1, 1, 1]]
        )
    )
    stored = {
        (record.factory, record.work_date): record.direct_sewers for record in WorkerRecordRepository().list_all()
    }
    assert stored == {
        (Factory.FAC_2, date(2026, 10, 24)): Decimal(20),
        (Factory.FAC_1, date(2026, 10, 24)): Decimal(700),
    }


def test_target_line_gives_factory_and_line() -> None:
    save(data_file(target_rows=[target(line="SFVL - Sewing Line 07")]))
    stored = TargetRecordRepository().list_all()[0]
    assert (stored.factory, stored.line, stored.base_po) == (Factory.FAC_1, "LINE 7", "PO-1")


def test_ac08_new_price_updates_old_day_without_new_rows() -> None:
    save(data_file([production(price=1)]))
    save(data_file([production(price=2)]))
    assert ProductionRecordRepository().count() == 1
    overview = GetOverviewService().handle(OverviewRequest(from_date=date(2026, 10, 24), to_date=date(2026, 10, 24)))
    cm = next(row for row in overview.metrics if row.metric == "Tiền CM")
    assert cm.values["Fac 2"] == 200.0


def test_ac09_other_period_keeps_stored_data() -> None:
    save(data_file([production(day=date(2026, 10, 24))]))
    save(
        data_file(
            [production(day=date(2027, 1, 4))],
            target_rows=[target(day=date(2027, 1, 4))],
            worker_rows=[worker(day=date(2027, 1, 4), sf2=20)],
        )
    )
    assert {record.production_date.year for record in ProductionRecordRepository().list_all()} == {2026, 2027}
    assert TargetRecordRepository().count() == 2
    assert WorkerRecordRepository().count() == 2


def test_ac10_row_gone_from_the_file_is_flagged_and_kept() -> None:
    first = date(2026, 10, 24)
    last = date(2026, 10, 26)
    save(data_file([production(day=first), production(day=first, color="RED", qty=7), production(day=last)]))
    save(data_file([production(day=first), production(day=last)]))
    repository = ProductionRecordRepository()
    assert repository.count() == 2
    flagged = repository.list_deleted()
    assert len(flagged) == 1 and flagged[0].color == "RED"
    overview = GetOverviewService().handle(OverviewRequest(from_date=first, to_date=last))
    output = next(row for row in overview.metrics if row.metric == "Sản lượng")
    assert output.values["Fac 2"] == 200.0


def test_ac10_each_sheet_uses_its_own_period() -> None:
    save(data_file(target_rows=[target(day=date(2026, 10, 24)), target(day=date(2026, 10, 30), style="S2")]))
    # the new file has targets only on 24/10: the target of 30/10 is outside the sheet's period and stays
    save(data_file(target_rows=[target(day=date(2026, 10, 24))]))
    assert TargetRecordRepository().count() == 2


def test_flagged_row_comes_back_when_it_returns_in_the_file() -> None:
    save(data_file([production(), production(color="RED")]))
    save(data_file([production()]))
    save(data_file([production(), production(color="RED")]))
    assert ProductionRecordRepository().count() == 2
    assert ProductionRecordRepository().list_deleted() == []


def test_duplicate_rows_are_kept_and_counted_by_occurrence() -> None:
    result = check(data_file([production(), production(qty=5)]))
    assert any(item.kind == "Dòng trùng" and item.count == 1 for item in result.warnings)
    save(data_file([production(), production(qty=5)]))
    assert ProductionRecordRepository().count() == 2


def test_unchanged_reupload_writes_no_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    file = data_file([production(), production(color="RED")], worker_rows=[worker(sf2=20)])
    save(file)
    before = {record.id: record.updated_at for record in ProductionRecordRepository().list_all()}
    calls: list[str] = []
    for repository in (ProductionRecordRepository, TargetRecordRepository, WorkerRecordRepository):
        original = repository.save_many

        def spy(self, entities, original=original):
            calls.append(type(self).__name__)
            return original(self, entities)

        monkeypatch.setattr(repository, "save_many", spy)
    result = save(file)
    assert calls == []
    assert result.saved_rows == 2
    assert {record.id: record.updated_at for record in ProductionRecordRepository().list_all()} == before
    assert ProductionRecordRepository().count() == 2
    assert ProductionRecordRepository().list_deleted() == []


def test_vanished_rows_and_changes_are_written_in_one_call(monkeypatch: pytest.MonkeyPatch) -> None:
    save(data_file([production(), production(color="RED"), production(color="BLUE")]))
    sizes: list[int] = []
    original = ProductionRecordRepository.save_many

    def spy(self, entities):
        entities = list(entities)
        sizes.append(len(entities))
        return original(self, entities)

    monkeypatch.setattr(ProductionRecordRepository, "save_many", spy)
    save(data_file([production(qty=999)]))
    assert sizes == [3]  # one change + two flags


def test_ac11_newest_day_without_smv_workers_and_targets_warns_and_saves() -> None:
    newest = date(2026, 11, 4)
    rows = [
        production(day=newest, smv=None, standard=None, color="RED", qty=40),
        production(day=newest, color="BLUE", qty=50, standard=100),
    ]
    result = check(data_file(rows, target_rows=[target()], worker_rows=[worker()]))
    kinds = {(item.kind, item.warning_date, item.count) for item in result.warnings}
    assert ("Dòng thiếu SMV", newest, 1) in kinds
    assert ("Dòng thiếu mục tiêu B", newest, 1) in kinds
    assert ("Ngày có sản lượng nhưng chưa có số thợ", newest, 1) in kinds
    assert ("Ngày có sản lượng nhưng chưa có Target system", newest, 1) in kinds
    assert result.can_save is True
    save(data_file(rows, target_rows=[target()], worker_rows=[worker()]))
    overview = GetOverviewService().handle(OverviewRequest(from_date=newest, to_date=newest, factories=[Factory.FAC_2]))
    values = {row.metric: row.values["Fac 2"] for row in overview.metrics}
    assert values["Hiệu suất A"] is None
    assert values["MO 8h"] is None
    assert values["Hiệu suất B"] == pytest.approx(50.0)  # 50 / 100: the row without target B is left out


def test_warning_target_system_only_from_03_10_2026() -> None:
    result = check(
        data_file(
            [production(day=date(2026, 10, 2))], target_rows=[], worker_rows=[worker(day=date(2026, 10, 2), sf2=5)]
        )
    )
    assert not any(item.kind == "Ngày có sản lượng nhưng chưa có Target system" for item in result.warnings)


def test_warning_counts_unclassified_names_and_styles_without_name() -> None:
    result = check(
        data_file(
            [production(name="VITRIOL"), production(name=None, color="RED", style="S9", po="PO-9")], target_rows=[]
        )
    )
    counts = {item.kind: item.count for item in result.warnings if item.warning_date is None}
    assert counts == {"Tên sản phẩm chưa phân nhóm": 1, "Style chưa có tên sản phẩm": 1}


def test_ac12_user_without_role_cannot_save_and_data_stays() -> None:
    message = "Bạn chưa có quyền cập nhật dữ liệu. Hãy liên hệ quản trị viên."
    save(data_file())
    set_current_user(CurrentUser(username="viewer", permissions=frozenset({"sewing_productivity"})))
    for call in (save, check):
        with pytest.raises(BusinessRuleViolation) as error:
            call(data_file([production(qty=999)]))
        assert error.value.message == message
    with pytest.raises(BusinessRuleViolation):
        ListUploadLogsService().handle(EmptyRequest())
    set_current_user(None)
    assert ProductionRecordRepository().list_all()[0].quantity == Decimal(100)


def test_br09_updater_role_and_administrator_may_save() -> None:
    set_current_user(CurrentUser(username="an", permissions=frozenset({"sewing_productivity/@UPDATER"})))
    assert save(data_file()).saved_rows == 1
    set_current_user(CurrentUser(username="admin", is_admin=True))
    assert save(data_file()).saved_rows == 1


def test_ac13_history_records_who_when_and_what() -> None:
    set_current_user(CurrentUser(username="an", full_name="Nguyễn Văn A", is_admin=True))
    result = save(
        data_file([production(), production(day=date(2026, 10, 26), factory=FAC2), production(po=None, color="X")])
    )
    assert result.message == "Đã lưu 2 dòng, dữ liệu đến ngày 26/10/2026."
    logs = ListUploadLogsService().handle(EmptyRequest()).items
    assert len(logs) == 1
    log = logs[0]
    assert isinstance(log.uploaded_at, datetime)
    assert (log.uploaded_by, log.file_name, log.saved_rows, log.skipped_rows) == (
        "Nguyễn Văn A",
        "Data sewing 2026.xlsx",
        2,
        1,
    )
    assert (log.from_date, log.to_date) == (date(2026, 10, 24), date(2026, 10, 26))
    assert UploadLogRepository().count() == 1


def test_br07_deleted_by_records_the_user() -> None:
    set_current_user(CurrentUser(username="an", is_admin=True))
    save(data_file([production(), production(color="RED")]))
    save(data_file([production()]))
    assert ProductionRecordRepository().list_deleted()[0].deleted_by == "an"
