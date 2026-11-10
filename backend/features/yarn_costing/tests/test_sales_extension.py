"""Mở rộng 2026-11-10 (yêu cầu của Sales): BR-76..BR-83, UC-49..UC-54 - AC-103..AC-116."""

from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest
from openpyxl import Workbook

from backend.core.base import UploadedFileDTO
from backend.core.exceptions import AppError
from backend.features.yarn_costing.business.blend_business import BlendBusiness
from backend.features.yarn_costing.dto.price_dto import ExportPriceLinesRequest, ListPriceLinesRequest
from backend.features.yarn_costing.dto.request_dto import CreateYarnRequestRequest
from backend.features.yarn_costing.dto.sales_dto import (
    ComparePriceLinesRequest,
    GetAccountingComparisonRequest,
    ImportAccountingFileRequest,
    SaveCustomerNameRequest,
    SuggestYarnsRequest,
    UseExistingYarnRequest,
)
from backend.features.yarn_costing.models.enums import FactoryCode, LineType, PriceEvent, YarnStatus
from backend.features.yarn_costing.models.price_history import PriceHistory
from backend.features.yarn_costing.models.yarn import CostBreakdown, PriceLine, Yarn
from backend.features.yarn_costing.repositories.accounting_cost_repository import (
    AccountingCostLineRepository,
    AccountingCostMonthRepository,
)
from backend.features.yarn_costing.repositories.customer_name_repository import CustomerYarnNameRepository
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository
from backend.features.yarn_costing.services.compare_price_lines_service import ComparePriceLinesService
from backend.features.yarn_costing.services.create_yarn_request_service import CreateYarnRequestService
from backend.features.yarn_costing.services.export_price_lines_service import ExportPriceLinesService
from backend.features.yarn_costing.services.get_accounting_comparison_service import GetAccountingComparisonService
from backend.features.yarn_costing.services.import_accounting_file_service import ImportAccountingFileService
from backend.features.yarn_costing.services.list_price_lines_service import ListPriceLinesService
from backend.features.yarn_costing.services.save_customer_name_service import SaveCustomerNameService
from backend.features.yarn_costing.services.suggest_similar_yarns_service import SuggestSimilarYarnsService
from backend.features.yarn_costing.services.use_existing_yarn_service import UseExistingYarnService
from backend.features.yarn_costing.tests.helpers import acting_as, setup_factory, user_with
from backend.shared.file_io.excel import ExcelReader

D = Decimal
S1, S4 = FactoryCode.S1, FactoryCode.S4
SALES = user_with("SALES", username="sales", full_name="Sales A")


def put_yarn(
    code: str,
    name: str,
    factory: FactoryCode = S4,
    status: YarnStatus = YarnStatus.DA_TINH_GIA,
    total: str = "20000",
    accounting_code: str | None = None,
    extra_lines: list[PriceLine] | None = None,
) -> Yarn:
    """A priced base yarn stored directly (only the fields the new use cases read)."""
    cost = CostBreakdown(labor=D(total))
    lines = [PriceLine(line_code=code, line_type=LineType.THUONG, cost=cost, accounting_code=accounting_code)]
    yarn = Yarn(
        factory_code=factory,
        yarn_code=code,
        base_code=code,
        yarn_name=name,
        status=status,
        lines=lines + (extra_lines or []) if status in (YarnStatus.DA_TINH_GIA, YarnStatus.CO_MA_KE_TOAN) else [],
    )
    YarnRepository().save_many([yarn])
    return yarn


def suggest(name: str, factory: FactoryCode | None = S4):
    return SuggestSimilarYarnsService().handle(SuggestYarnsRequest(yarn_name=name, factory_code=factory))


# ---- BR-76 ----
def test_ac103_read_blend_from_name() -> None:
    blends = BlendBusiness()
    same = {
        blends.parse(n).text
        for n in ("CVC 20/1 (50/50)", "TC 20/1 (50/50)", "Poly/cotton 20/1 (50/50)", "Cotton/poly 20/1 (50/50)")
    }
    assert same == {"20/1 · Cotton 50% + PE 50%"}
    assert blends.parse("TC 20/1 (65/35)").text == "20/1 · Cotton 35% + PE 65%"
    assert blends.parse("CVCD 16/1 (50/50)").text == "16/1 · Cotton 50% + PE 50% · từ khoá CHẢI THÔ"
    core = blends.parse("CORE 30/1 (CO/RE-PES) (72/28) MVS")
    assert core.text == "30/1 · Cotton 72% + PE 28% · từ khoá MVS, RECYCLE"
    assert not blends.parse("ABC 30/1 (60/40)").readable
    assert suggest("ABC 30/1 (60/40)").message.startswith("App chưa đọc được thành phần")


# ---- BR-77 ----
def test_ac104_same_and_near_suggestions() -> None:
    put_yarn("S4-3001", "TC 20/1 (50/50)")
    put_yarn("S4-3002", "CVC 20/1 (50/50)", status=YarnStatus.KHONG_SAN_XUAT)
    put_yarn("S4-3003", "CVC 20/1 (50/50)", status=YarnStatus.CHUA_TINH_DUOC)
    put_yarn("S4-3004", "CVC 20/1 (50/50)", status=YarnStatus.DA_HUY)
    res = suggest("Poly/cotton 20/1 (50/50)")
    assert [s.yarn_code for s in res.same] == ["S4-3001"] and res.near == []
    assert res.same_in_factory == ["S4-3001"] and res.blend_text == "20/1 · Cotton 50% + PE 50%"
    near = suggest("CVC 20/1 (50/50) MVS")
    assert near.same == [] and [(s.yarn_code, s.note) for s in near.near] == [("S4-3001", "không có MVS")]
    assert suggest("CVC 21/1 (50/50)").message == "Chưa có sợi trùng hoặc gần giống đã có giá."


def test_ac105_customer_name_counts_as_same() -> None:
    put_yarn("S1-2001", "VISCOSE 30/1 MVS", factory=S1)
    SaveCustomerNameService().handle(
        SaveCustomerNameRequest(base_code="S1-2001", customer_name="Salponpat", customer_yarn_name="VIS 30/1 MVS")
    )
    res = suggest("vis  30/1 mvs", S1)
    assert [(s.yarn_code, s.note) for s in res.same] == [("S1-2001", "trùng tên theo khách Salponpat")]


# ---- BR-78 / UC-15 ----
def test_ac106_duplicate_reason_required_in_same_factory() -> None:
    setup_factory(S4, with_loss_group=False)
    put_yarn("S4-3001", "TC 20/1 (50/50)")
    request = CreateYarnRequestRequest(
        factory_code=S4, yarn_name="Poly/cotton 20/1 (50/50)", packaging_code="Type 3", customer_name="ABC"
    )
    with pytest.raises(AppError, match="Đã có sợi trùng ở xưởng S4: S4-3001"):
        CreateYarnRequestService().handle(request)
    created = CreateYarnRequestService().handle(
        request.model_copy(update={"duplicate_reason": "Khách cần chạy compact"})
    )
    assert created.yarn.customer_name == "ABC" and created.yarn.duplicate_reason == "Khách cần chạy compact"
    # Trùng only at S1 while the request is for S4: no reason needed
    put_yarn("S1-2002", "CVC 30/1 (50/50)", factory=S1)
    other = CreateYarnRequestService().handle(
        CreateYarnRequestRequest(factory_code=S4, yarn_name="TC 30/1 (50/50)", packaging_code="Type 3")
    )
    assert other.yarn.duplicate_reason == "" and other.yarn.status == YarnStatus.CHO_XUONG_XEM


# ---- UC-50 / BR-79 ----
def test_ac107_use_existing_yarn_saves_customer_name() -> None:
    put_yarn("S4-3001", "TC 20/1 (50/50)")
    put_yarn("S4-3005", "CVC 20/1 (50/50) SIRO")
    with acting_as(SALES):
        res = UseExistingYarnService().handle(
            UseExistingYarnRequest(yarn_code="S4-3001", typed_name="Poly/cotton 20/1 (50/50)", customer_name="ABC")
        )
        assert res.saved and res.message == "Đã lưu tên 'Poly/cotton 20/1 (50/50)' của khách ABC cho sợi S4-3001."
        assert [line.line_code for line in res.lines] == ["S4-3001"]
        with pytest.raises(AppError, match="Tên 'Poly/cotton 20/1 \\(50/50\\)' của khách ABC đã gắn với sợi S4-3001."):
            UseExistingYarnService().handle(
                UseExistingYarnRequest(yarn_code="S4-3005", typed_name="poly/cotton 20/1 (50/50)", customer_name="abc")
            )
        plain = UseExistingYarnService().handle(
            UseExistingYarnRequest(yarn_code="S4-3005", typed_name="CVC 20/1 (50/50) SIRO", customer_name="")
        )
    assert not plain.saved and plain.message == "Sợi S4-3005 - CVC 20/1 (50/50) SIRO: 20.000 đ/kg."
    assert len(CustomerYarnNameRepository().list_all()) == 1


# ---- UC-51 ----
def test_ac108_customer_names_add_edit_delete_and_roles() -> None:
    put_yarn("S4-3001", "TC 20/1 (50/50)")
    with acting_as(SALES):
        added = SaveCustomerNameService().handle(
            SaveCustomerNameRequest(base_code="S4-3001", customer_name="ABC", customer_yarn_name="PC 20/1 50/50")
        )
        assert added.item is not None
        SaveCustomerNameService().handle(
            SaveCustomerNameRequest(
                base_code="S4-3001", alias_id=added.item.id, customer_yarn_name="PC 20/1 (50/50)", note="Đơn PO-9"
            )
        )
        deleted = SaveCustomerNameService().handle(
            SaveCustomerNameRequest(base_code="S4-3001", alias_id=added.item.id, delete=True)
        )
    assert deleted.message == "Đã xoá tên 'PC 20/1 (50/50)' của khách ABC."
    assert CustomerYarnNameRepository().list_all() == []
    assert [a.customer_yarn_name for a in CustomerYarnNameRepository().list_deleted()] == ["PC 20/1 (50/50)"]
    assert sum(1 for a in AuditLogRepository().list_all() if a.object_ref == "S4-3001") == 3
    with acting_as(user_with("KT", username="kt")), pytest.raises(AppError, match="chưa có vai trò"):
        SaveCustomerNameService().handle(
            SaveCustomerNameRequest(base_code="S4-3001", customer_name="ABC", customer_yarn_name="X 20/1")
        )
    with pytest.raises(AppError, match="Tên khách gọi trùng tên chuẩn của sợi"):
        SaveCustomerNameService().handle(
            SaveCustomerNameRequest(base_code="S4-3001", customer_name="ABC", customer_yarn_name="tc 20/1 (50/50)")
        )


# ---- UC-27 / UC-29 ----
def test_ac109_price_list_customer_filter_column_and_export() -> None:
    setup_factory(S4, with_loss_group=False)
    put_yarn("S4-3001", "TC 20/1 (50/50)")
    put_yarn("S4-3006", "CVC 30/1 (60/40)")
    SaveCustomerNameService().handle(
        SaveCustomerNameRequest(base_code="S4-3001", customer_name="Salponpat", customer_yarn_name="PC 20/1")
    )
    every = ListPriceLinesService().handle(ListPriceLinesRequest())
    assert every.total_count == 2 and every.customers == ["Salponpat"]
    only = ListPriceLinesService().handle(ListPriceLinesRequest(customers=["salponpat"]))
    assert [(r.line_code, r.customer_names_text) for r in only.items] == [("S4-3001", "Salponpat: PC 20/1")]
    file = ExportPriceLinesService().handle(ExportPriceLinesRequest())
    rows = ExcelReader(sheet_name="Bang gia").read(UploadedFileDTO(filename=file.filename, content=file.content))
    assert list(rows[0].keys())[-1] == "Tên theo khách"
    assert {r["Mã dòng"]: r["Tên theo khách"] for r in rows} == {"S4-3001": "Salponpat: PC 20/1", "S4-3006": None}


# ---- UC-52 ----
def test_ac110_compare_two_lines() -> None:
    ck = PriceLine(
        line_code="S1-2001 (CK1)",
        line_type=LineType.CHIET_KHAU,
        adjustment_percent=D("0.368"),
        cost=CostBreakdown(labor=D("12640")),
    )
    put_yarn("S1-2001", "VISCOSE 30/1 MVS", factory=S1, total="20000", extra_lines=[ck])
    res = ComparePriceLinesService().handle(ComparePriceLinesRequest(line_a="S1-2001", line_b="S1-2001 (CK1)"))
    total = next(p for p in res.prices if p.label == "Tổng (VND/kg)")
    assert total.difference == D(-7360) and total.difference_percent == D("-36.8")
    assert {r.label: (r.a, r.b) for r in res.info}["Loại dòng"] == ("Thường", "Chiết khấu")
    with pytest.raises(AppError, match="Hãy chọn hai dòng giá khác nhau."):
        ComparePriceLinesService().handle(ComparePriceLinesRequest(line_a="S1-2001", line_b="S1-2001"))


# ---- UC-53 / UC-54 ----
HEADER = [
    "STT", "MÃ", "TÊN SẢN PHẨM", "SỐ LƯỢNG", "VLC", "NHÂN CÔNG + BẢO TRÌ", "KHẤU HAO", "ĐỘNG LỰC",
    "VẬT TƯ, NHIÊN LIỆU, CCDC, VẬT LIỆU PHỤ", "CHI PHÍ QUẢN LÝ", "CỘNG", "GIÁ THÀNH ĐƠN VỊ",
]  # fmt: skip
CM20 = ["S41602000010000000FCE", "CM 20/1", 35463.96, 2248692722, 252700655, 67691288, 207142195, 112308517, 58089665, 2946625042]  # fmt: skip
CORE40 = ["S1260400001AV00098D", "CORE 40/1 (NYLON/DTY 40D/24F/1) (70/30) MVS", 29.376, 5785230, 6658865, 17001914, 5541670, 1603031, 6326127, 42916837]  # fmt: skip


def z_file(sheets: dict[str, list[list]]) -> UploadedFileDTO:
    """File Z as accounting sends it: title, blank row, header, blank row, column numbers, data, total row."""
    book = Workbook()
    book.remove(book.active)
    for name, rows in sheets.items():
        sheet = book.create_sheet(name)
        sheet.append(["BẢNG TỔNG HỢP GIÁ THÀNH SỢI"])
        sheet.append([])
        sheet.append(HEADER)
        sheet.append([])
        sheet.append(["A", 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, "12=11/2"])
        for index, row in enumerate(rows, start=1):
            sheet.append([index, *row])
        sheet.append(["CỘNG SỢI 4", None, None, 1, 1, 1, 1, 1, 1, 1, 1])
    norm = book.create_sheet("Norm S4")
    norm.append(["MA_KE TOAN", "TEN"])
    stream = BytesIO()
    book.save(stream)
    return UploadedFileDTO(filename="3. Z SOI T09.2026.xlsx", content=stream.getvalue())


def import_z(sheets: dict[str, list[list]], commit: bool = True):
    return ImportAccountingFileService().handle(ImportAccountingFileRequest(file=z_file(sheets), commit=commit))


def test_ac111_read_file_z() -> None:
    bad = ["S42002000010000119E", "PE 20/1 MVS", "abc", 1, 1, 1, 1, 1, 1, 2]
    check = import_z({"Z SỢI T09.26": [CM20, CORE40, bad], "Z SOI T11.25": [CM20]}, commit=False)
    assert [(m.period, m.s1_count, m.s4_count, m.rejected_count) for m in check.months] == [
        ("2026-09", 1, 1, 1),
        ("2025-11", 0, 1, 0),
    ]
    assert check.rejected_rows[0].reason == "Cột SỐ LƯỢNG không phải số."
    assert AccountingCostMonthRepository().list_all() == []
    saved = import_z({"Z SỢI T09.26": [CM20, CORE40, bad], "Z SOI T11.25": [CM20]})
    assert saved.message == "Đã lưu giá thành kế toán tháng 09/2026, 11/2025: 3 mã, bị loại 1 dòng."
    line = next(x for x in AccountingCostLineRepository().list_all() if x.period == "2026-09" and x.factory_code == S4)
    assert round(line.conversion_unit_cost) == 19680 and round(line.unit_cost) == 83088


def test_ac112_reload_month_flags_old_version() -> None:
    import_z({"Z SỢI T09.26": [CM20, CORE40]})
    first = AccountingCostMonthRepository().current("2026-09")
    import_z({"Z SỢI T09.26": [CM20]})
    current = AccountingCostMonthRepository().current("2026-09")
    assert current is not None and first is not None and current.id != first.id and current.row_count == 1
    assert [m.id for m in AccountingCostMonthRepository().list_deleted()] == [first.id]
    assert len(AccountingCostLineRepository().list_deleted()) == 2
    assert any(a.detail.endswith("2 → 1 mã") for a in AuditLogRepository().list_all())


def history(line_code: str, total: str, effective: date) -> PriceHistory:
    return PriceHistory(
        factory_code=S4,
        yarn_code=line_code,
        line_code=line_code,
        line_type=LineType.THUONG,
        event=PriceEvent.DOI_DINH_MUC,
        effective_date=effective,
        new=CostBreakdown(labor=D(total)),
    )


def test_ac113_ac114_comparison_price_at_month_end_and_warnings() -> None:
    put_yarn("S4-3010", "CM 20/1", total="19500", accounting_code="S41602000010000000FCE")
    put_yarn("S1-2010", "CORE 40/1 MVS", factory=S1, total="1000000", accounting_code="S1260400001AV00098D")
    PriceHistoryRepository().add_many(
        [history("S4-3010", "19000", date(2026, 8, 1)), history("S4-3010", "19500", date(2026, 10, 5))]
    )
    other = ["S42002000010000119E", "PE 20/1 MVS", 8618, 233021351, 21208353, 13297353, 53170284, 26824615, 10287128, 357809084]  # fmt: skip
    import_z({"Z SỢI T09.26": [CM20, CORE40, other]})
    res = GetAccountingComparisonService().handle(GetAccountingComparisonRequest(period="2026-09"))
    rows = {r.accounting_code: r for r in res.rows}
    cm = rows["S41602000010000000FCE"]
    assert cm.app_total == D(19000) and cm.app_price_date == date(2026, 8, 1)
    assert round(cm.difference) == -680 and round(cm.difference_percent, 2) == D("-3.46")  # type: ignore[arg-type]
    core = rows["S1260400001AV00098D"]
    assert core.app_price_note == "giá hiện tại" and "⚠ Sản lượng nhỏ" in core.warnings
    assert res.matched_count == 2 and res.small_count == 1 and res.missing_count == 1
    assert [m.accounting_code for m in res.missing] == ["S42002000010000119E"]
    assert round(res.weighted_gap_percent, 2) == D("-3.46")  # type: ignore[arg-type]
    assert [r.accounting_code for r in res.top_gaps] == ["S41602000010000000FCE"]
    tight = GetAccountingComparisonService().handle(
        GetAccountingComparisonRequest(period="2026-09", gap_percent=D(3), only_gap=True, hide_small=True)
    )
    assert [r.accounting_code for r in tight.rows] == ["S41602000010000000FCE"] and tight.gap_count == 2
    with pytest.raises(AppError, match="Mức cảnh báo phải là số lớn hơn 0."):
        GetAccountingComparisonService().handle(GetAccountingComparisonRequest(period="2026-09", small_kg=D(0)))


def test_ac115_only_sales_and_so_upload_file_z() -> None:
    for roles in (("KT",), ("XS4",)):
        with acting_as(user_with(*roles, username="x")), pytest.raises(AppError, match="chưa có vai trò"):
            import_z({"Z SỢI T09.26": [CM20]})
    with acting_as(SALES):
        assert import_z({"Z SỢI T09.26": [CM20]}).committed


def test_ac116_old_request_flow_unchanged() -> None:
    setup_factory(S4, with_loss_group=False)
    created = CreateYarnRequestService().handle(
        CreateYarnRequestRequest(factory_code=S4, yarn_name="CVC 30/1 (60/40) MVS", packaging_code="Type 3")
    )
    assert created.yarn.customer_name == "" and created.yarn.duplicate_reason == ""
    with pytest.raises(AppError, match="đã có ở mã"):
        CreateYarnRequestService().handle(
            CreateYarnRequestRequest(factory_code=S4, yarn_name="cvc 30/1 (60/40) mvs", packaging_code="Type 3")
        )


def test_ac117_match_by_first_18_characters() -> None:
    """BR-82 (sửa 2026-11-10): app codes typed without the D / E / FCD / FCE suffix still match file Z."""
    put_yarn("S4-3010", "CM 20/1", total="19500", accounting_code="S41602000010000000")
    import_z({"Z SỢI T09.26": [CM20]})
    res = GetAccountingComparisonService().handle(GetAccountingComparisonRequest(period="2026-09"))
    assert res.matched_count == 1 and res.missing_count == 0
    row = res.rows[0]
    assert row.line_code == "S4-3010"
    assert row.app_price_note == "giá hiện tại; ghép theo 18 ký tự đầu (S41602000010000000)"
    put_yarn("S4-3011", "CM 20/1 COMPACT", total="21000", accounting_code="S41602000010000000FCE")
    exact = GetAccountingComparisonService().handle(GetAccountingComparisonRequest(period="2026-09"))
    assert exact.rows[0].line_code == "S4-3011" and "ghép theo" not in exact.rows[0].app_price_note
