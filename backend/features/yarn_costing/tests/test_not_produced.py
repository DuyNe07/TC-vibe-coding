"""BR-72..BR-75, UC-47, UC-48 Trạng thái "Không sản xuất" (mở rộng 2026-11-05): AC-95..AC-102."""

from datetime import date
from decimal import Decimal

import pytest

from backend.core.base import UploadedFileDTO
from backend.core.exceptions import AppError
from backend.features.yarn_costing.dto.dashboard_dto import GetDashboardRequest
from backend.features.yarn_costing.dto.import_dto import ImportNotProducedFileRequest
from backend.features.yarn_costing.dto.master_dto import RecalculateNotPricedRequest
from backend.features.yarn_costing.dto.price_dto import (
    CreateAdjustmentLineRequest,
    ListPriceLinesRequest,
    SetAccountingCodeRequest,
)
from backend.features.yarn_costing.dto.pricing_dto import CreateNsmRevisionRequest, SaveYarnNsmRequest
from backend.features.yarn_costing.dto.request_dto import CreateYarnRequestRequest, SetNotProducedRequest
from backend.features.yarn_costing.models.enums import FactoryCode, ImportMode, LineType, PriceEvent, YarnStatus
from backend.features.yarn_costing.repositories.legacy_price_repository import ImportBatchRepository
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository
from backend.features.yarn_costing.services.create_adjustment_line_service import CreateAdjustmentLineService
from backend.features.yarn_costing.services.create_nsm_revision_service import CreateNsmRevisionService
from backend.features.yarn_costing.services.create_yarn_request_service import CreateYarnRequestService
from backend.features.yarn_costing.services.get_dashboard_service import GetDashboardService
from backend.features.yarn_costing.services.import_not_produced_file_service import ImportNotProducedFileService
from backend.features.yarn_costing.services.list_price_lines_service import ListPriceLinesService
from backend.features.yarn_costing.services.recalculate_not_priced_service import RecalculateNotPricedService
from backend.features.yarn_costing.services.save_yarn_nsm_service import SaveYarnNsmService
from backend.features.yarn_costing.services.set_accounting_code_service import SetAccountingCodeService
from backend.features.yarn_costing.services.set_not_produced_service import SetNotProducedService
from backend.features.yarn_costing.tests.helpers import (
    S4_COMPONENTS,
    S4_NAME,
    S4_NSM,
    acting_as,
    create_request,
    setup_factory,
    user_with,
)
from backend.shared.file_io.excel import ExcelWriter

S4 = FactoryCode.S4
D = Decimal
REASON = "Excel không có giá - ngành xác nhận không sản xuất"


def yarn(code: str):
    return next(y for y in YarnRepository().list_all() if y.yarn_code == code)


def priced_with_ck_and_revision() -> tuple[str, str]:
    """S4 yarn 'Đã tính giá' with Thường, Thí nghiệm, one CK line, and one NSM revision 'Chưa tính được'."""
    setup_factory(S4)
    code = create_request(S4_NAME)
    SaveYarnNsmService().handle(SaveYarnNsmRequest(yarn_code=code, components=S4_COMPONENTS, nsm=S4_NSM, save=True))
    CreateAdjustmentLineService().handle(
        CreateAdjustmentLineRequest(
            yarn_code=code, line_type=LineType.CHIET_KHAU, percent=D("0.05"), reason="Khách lớn", order_ref="PO-1"
        )
    )
    revision = CreateNsmRevisionService().handle(
        CreateNsmRevisionRequest(
            source_yarn_code=code, adjust_reason="Đơn 50 tấn", components=S4_COMPONENTS, nsm=S4_NSM, save=True
        )
    )
    rev_code = revision.yarn.yarn_code
    yarns = YarnRepository().list_all()
    rev = next(y for y in yarns if y.yarn_code == rev_code)
    YarnRepository().store(
        yarns, [rev.model_copy(update={"status": YarnStatus.CHUA_TINH_DUOC, "lines": [], "stage_details": []})]
    )
    return code, rev_code


def mark(code: str, reason: str = REASON, not_produced: bool = True):
    return SetNotProducedService().handle(
        SetNotProducedRequest(yarn_code=code, reason=reason, not_produced=not_produced)
    )


def test_ac95_mark_removes_lines_and_keeps_history() -> None:
    code, rev_code = priced_with_ck_and_revision()
    lines = {line.line_code: line.total_vnd for line in yarn(code).lines}
    assert len(lines) == 3
    with acting_as(user_with("XS4", username="an", full_name="An")):
        res = mark(rev_code)  # a revision → the whole family
    assert res.message == f"Đã đánh dấu Không sản xuất cho {code} (2 bản, gỡ 3 dòng giá)."
    for c in (code, rev_code):
        y = yarn(c)
        assert y.status == YarnStatus.KHONG_SAN_XUAT and y.lines == [] and y.stage_details == []
        assert y.not_produced_reason == REASON and y.not_produced_by and y.not_produced_at is not None
    assert yarn(code).nsm and yarn(code).components and yarn(code).yarn_name == S4_NAME
    entries = [h for h in PriceHistoryRepository().list_all() if h.event == PriceEvent.KHONG_SAN_XUAT]
    assert {h.line_code: h.old.total for h in entries} == lines  # type: ignore[union-attr]
    assert all(h.new.total == 0 and h.reason == REASON for h in entries)
    assert sum(1 for a in AuditLogRepository().list_all() if a.object_ref == code and "Không sản xuất" in a.detail) == 1


def test_ac96_mark_refused() -> None:
    setup_factory(S4)
    waiting = create_request(S4_NAME)
    with pytest.raises(AppError, match=f"Mã {waiting} đang 'Chờ xưởng xem'. Hãy dùng Từ chối."):
        mark(waiting)
    SaveYarnNsmService().handle(SaveYarnNsmRequest(yarn_code=waiting, components=S4_COMPONENTS, nsm=S4_NSM, save=True))
    with pytest.raises(AppError, match="Vui lòng nhập lý do."):
        mark(waiting, reason="  ")
    with acting_as(user_with("XS1", username="b")), pytest.raises(AppError, match="xưởng S1"):
        mark(waiting)
    for role in ("SALES", "KT"):
        with acting_as(user_with(role, username="c")), pytest.raises(AppError, match="chưa có vai trò"):
            mark(waiting)
    with acting_as(user_with("KT", username="kt")):
        SetAccountingCodeService().handle(SetAccountingCodeRequest(line_code=waiting, accounting_code="S4KT01"))
    with pytest.raises(AppError, match=r"có mã kế toán \(S4KT01\)"):
        mark(waiting)
    assert yarn(waiting).status == YarnStatus.CO_MA_KE_TOAN and len(yarn(waiting).lines) == 2


def test_ac97_not_produced_yarn_is_left_out() -> None:
    code, _ = priced_with_ck_and_revision()
    mark(code)
    listing = ListPriceLinesService().handle(ListPriceLinesRequest(factory_code=S4))
    assert all(not r.line_code.startswith(code) for r in listing.items) and listing.not_produced_count == 1
    with pytest.raises(AppError, match="không có mã nào đang 'Chưa tính được'"):
        RecalculateNotPricedService().handle(
            RecalculateNotPricedRequest(factory_code=S4, effective_date=date.today(), reason="x")
        )
    assert yarn(code).status == YarnStatus.KHONG_SAN_XUAT
    dash = GetDashboardService().handle(
        GetDashboardRequest(factory_code=S4, date_from=date(2000, 1, 1), date_to=date.today())
    )
    assert dash.quoted_count == 0 and YarnStatus.KHONG_SAN_XUAT.value not in dash.status_counts
    blocked = f"Mã {code} đang 'Không sản xuất'. Vui lòng bỏ đánh dấu trước khi thao tác."
    with pytest.raises(AppError, match=blocked):
        SaveYarnNsmService().handle(SaveYarnNsmRequest(yarn_code=code, components=S4_COMPONENTS, nsm=S4_NSM, save=True))
    with pytest.raises(AppError, match=blocked):
        CreateNsmRevisionService().handle(
            CreateNsmRevisionRequest(source_yarn_code=code, adjust_reason="x", components=S4_COMPONENTS, nsm=S4_NSM)
        )
    with pytest.raises(AppError, match=blocked):
        CreateAdjustmentLineService().handle(
            CreateAdjustmentLineRequest(
                yarn_code=code, line_type=LineType.PHU_PHI, percent=D("0.1"), reason="x", order_ref="PO"
            )
        )
    new = CreateYarnRequestService().handle(  # BR-06 does not block, BR-05 counts the code
        CreateYarnRequestRequest(factory_code=S4, yarn_name=S4_NAME, packaging_code="Type 3")
    )
    assert int(new.yarn.yarn_code.split("-")[1]) > int(code.split("-")[1])


def test_ac98_unmark_recalculates() -> None:
    code, rev_code = priced_with_ck_and_revision()
    before = yarn(code)
    regular = next(line.total_vnd for line in before.lines if line.line_type == LineType.THUONG)
    mark(code)
    ruined = yarn(rev_code).model_copy(update={"nsm": {}, "components": []})
    YarnRepository().store(YarnRepository().list_all(), [ruined])  # the revision cannot be priced any more
    with pytest.raises(AppError, match="Vui lòng nhập lý do."):
        mark(code, reason="", not_produced=False)
    res = mark(code, reason="Ngành chạy lại", not_produced=False)
    assert res.priced_count == 1 and res.failed_count == 1
    base = yarn(code)
    assert base.status == YarnStatus.DA_TINH_GIA and not base.not_produced_reason and base.not_produced_at is None
    assert sorted(line.line_type for line in base.lines) == sorted([LineType.THUONG, LineType.THI_NGHIEM])
    assert next(line.total_vnd for line in base.lines if line.line_type == LineType.THUONG) == regular
    assert yarn(rev_code).status == YarnStatus.CHUA_TINH_DUOC and yarn(rev_code).status_reasons
    assert any(h.event == PriceEvent.BO_KHONG_SAN_XUAT for h in PriceHistoryRepository().list_all())
    with pytest.raises(AppError, match=f"Mã {code} không ở trạng thái 'Không sản xuất'."):
        mark(code, reason="x", not_produced=False)


def test_ac99_waiting_accounting_code_kept_then_attached() -> None:
    setup_factory(S4)
    code = create_request(S4_NAME)
    SaveYarnNsmService().handle(SaveYarnNsmRequest(yarn_code=code, components=S4_COMPONENTS, nsm=S4_NSM, save=True))
    yarns = YarnRepository().list_all()
    y = next(x for x in yarns if x.yarn_code == code)
    YarnRepository().store(
        yarns,
        [y.model_copy(update={"lines": [], "status": YarnStatus.CHUA_TINH_DUOC, "pending_accounting_code": "S4WAIT"})],
    )
    mark(code)
    assert yarn(code).status == YarnStatus.KHONG_SAN_XUAT and yarn(code).pending_accounting_code == "S4WAIT"
    mark(code, reason="Sản xuất lại", not_produced=False)
    after = yarn(code)
    regular = next(line for line in after.lines if line.line_type == LineType.THUONG)
    assert after.status == YarnStatus.CO_MA_KE_TOAN and regular.accounting_code == "S4WAIT"
    assert after.pending_accounting_code is None


def upload(rows: list[dict]) -> UploadedFileDTO:
    return UploadedFileDTO(filename="ksx.xlsx", content=ExcelWriter().write({"Khong san xuat": rows}))


def test_ac100_file_preview_and_save() -> None:
    setup_factory(S4)
    ok = create_request(S4_NAME)
    names = [S4_NAME.replace("40/1", f"{n}/1") for n in (30, 20, 50)]  # same loss group, other counts
    dup, coded, done = (create_request(n) for n in names)
    for c in (ok, dup, coded, done):
        SaveYarnNsmService().handle(SaveYarnNsmRequest(yarn_code=c, components=S4_COMPONENTS, nsm=S4_NSM, save=True))
    with acting_as(user_with("KT", username="kt")):
        SetAccountingCodeService().handle(SetAccountingCodeRequest(line_code=coded, accounting_code="S4KT9"))
    mark(done)
    display_ok = ok.replace("-", " - ")
    rows = [
        {"Mã": display_ok, "Lý do": REASON, "Tên sợi": "bỏ qua cột này"},
        {"Mã": dup, "Lý do": REASON},
        {"Mã": dup, "Lý do": REASON},
        {"Mã": "S4-99999", "Lý do": REASON},
        {"Mã": coded, "Lý do": REASON},
        {"Mã": "S4-1", "Lý do": None},
        {"Mã": done, "Lý do": REASON},
        {"Mã": None, "Lý do": "dòng trống mã"},
    ]
    preview = ImportNotProducedFileService().handle(ImportNotProducedFileRequest(factory_code=S4, file=upload(rows)))
    assert preview.valid_count == 1 and preview.valid_rows[0].yarn_code == ok and preview.line_count == 2
    reasons = {(r.excel_row, r.reason) for r in preview.rejected_rows}
    assert (3, f"Mã '{dup}' bị trùng trong file.") in reasons and (4, f"Mã '{dup}' bị trùng trong file.") in reasons
    assert (5, "Không có mã 'S4-99999' ở xưởng S4.") in reasons
    assert any(r.excel_row == 6 and "có mã kế toán" in r.reason for r in preview.rejected_rows)
    assert preview.rejected_count == 5 and preview.skipped_count == 1
    assert any(r.excel_row == 8 and "đã là Không sản xuất" in r.reason for r in preview.rejected_rows)
    assert yarn(ok).status == YarnStatus.DA_TINH_GIA  # preview saves nothing
    saved = ImportNotProducedFileService().handle(
        ImportNotProducedFileRequest(factory_code=S4, file=upload(rows), commit=True)
    )
    assert saved.message == "Đã đánh dấu Không sản xuất cho 1 mã (gỡ 2 dòng giá), bị loại 5 dòng."
    assert yarn(ok).status == YarnStatus.KHONG_SAN_XUAT and yarn(dup).status == YarnStatus.DA_TINH_GIA
    assert any(b.mode == ImportMode.KHONG_SAN_XUAT for b in ImportBatchRepository().list_all())
    assert saved.result_file is not None


def test_ac101_file_factory_scope() -> None:
    setup_factory(S4)
    code = create_request(S4_NAME)
    rows = [{"Mã": code, "Lý do": REASON}]
    with acting_as(user_with("XS4", username="x4")), pytest.raises(AppError, match="xưởng S4"):
        ImportNotProducedFileService().handle(
            ImportNotProducedFileRequest(factory_code=FactoryCode.S1, file=upload(rows))
        )
    with pytest.raises(AppError, match="thiếu cột bắt buộc: Lý do"):
        ImportNotProducedFileService().handle(
            ImportNotProducedFileRequest(factory_code=S4, file=upload([{"Mã": code}]))
        )
