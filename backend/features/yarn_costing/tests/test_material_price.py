"""Đợt 2 (bổ sung 2026-11-10): giá nguyên liệu bình quân, hàng sắp về, giá báo khách - BR-84..BR-99, AC-118..AC-132.

Numbers come from the real files of Sales: GIÁ SỢI 4 THÁNG 10.xlsx, Giá nguyên liệu.xlsx, Ke hoach xo ve NM - 06.11.xlsx."""

from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

import pytest
from openpyxl import Workbook

from backend.core.base import UploadedFileDTO
from backend.core.exceptions import AppError
from backend.features.yarn_costing.dto.material_dto import (
    ArrivalLotRowDTO,
    ArrivalMappingRowDTO,
    CalculateQuoteRequest,
    CottonShareDTO,
    DeleteQuoteRequest,
    ExportQuotesRequest,
    GetMaterialAveragesRequest,
    GetMaterialSetupRequest,
    GetMonthlySettingRequest,
    GetQuoteFormRequest,
    GetStockOutComparisonRequest,
    ImportArrivalFileRequest,
    ImportStockFileRequest,
    ListArrivalsRequest,
    ListQuotesRequest,
    RecoveryDTO,
    SaveArrivalLotsRequest,
    SaveArrivalMappingsRequest,
    SaveMonthlySettingRequest,
    SavePriceGroupRequest,
    SaveStockItemSettingsRequest,
    StockItemRowDTO,
)
from backend.features.yarn_costing.models.enums import (
    CottonOrigin,
    FactoryCode,
    Incoterm,
    LineType,
    MaterialDecision,
    MaterialMarket,
    PriceGroupKind,
    PriceKind,
    YarnStatus,
)
from backend.features.yarn_costing.models.exchange_rate import ExchangeRate
from backend.features.yarn_costing.models.material_price import COTTON_PLAN_ID
from backend.features.yarn_costing.models.yarn import CostBreakdown, PriceLine, StageCostDetail, Yarn, YarnComponent
from backend.features.yarn_costing.repositories.exchange_rate_repository import ExchangeRateRepository
from backend.features.yarn_costing.repositories.material_price_repository import (
    ArrivalLotRepository,
    StockItemSettingRepository,
    StockLineRepository,
    StockMonthRepository,
)
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository
from backend.features.yarn_costing.services.calculate_quote_service import CalculateQuoteService
from backend.features.yarn_costing.services.delete_quote_service import DeleteQuoteService
from backend.features.yarn_costing.services.export_quotes_service import ExportQuotesService
from backend.features.yarn_costing.services.get_material_averages_service import GetMaterialAveragesService
from backend.features.yarn_costing.services.get_material_setup_service import GetMaterialSetupService
from backend.features.yarn_costing.services.get_monthly_setting_service import GetMonthlySettingService
from backend.features.yarn_costing.services.get_quote_form_service import GetQuoteFormService
from backend.features.yarn_costing.services.get_stock_out_comparison_service import GetStockOutComparisonService
from backend.features.yarn_costing.services.import_arrival_file_service import ImportArrivalFileService
from backend.features.yarn_costing.services.import_stock_file_service import ImportStockFileService
from backend.features.yarn_costing.services.list_arrivals_service import ListArrivalsService
from backend.features.yarn_costing.services.list_quotes_service import ListQuotesService
from backend.features.yarn_costing.services.save_arrival_lots_service import SaveArrivalLotsService
from backend.features.yarn_costing.services.save_arrival_mappings_service import SaveArrivalMappingsService
from backend.features.yarn_costing.services.save_monthly_setting_service import SaveMonthlySettingService
from backend.features.yarn_costing.services.save_price_group_service import SavePriceGroupService
from backend.features.yarn_costing.services.save_stock_item_settings_service import SaveStockItemSettingsService
from backend.features.yarn_costing.tests.helpers import acting_as, user_with
from backend.shared.file_io.excel import ExcelReader

D = Decimal
SALES = user_with("SALES", username="sales", full_name="Sales A")
SALES_B = user_with("SALES", username="sales2", full_name="Sales B")
USA = "MN1100153210200005IDR"
BRAZIL = "MN1100153211801002IDR"
INDO_D = "MN1001203812233001IDR"
INDO_X = "MN1001203812233001IR"
YARN_CODE = "S41602000010000000FCE"

STOCK_HEADER = [
    "ICA_NAME", "NGAY_NHAP_CUOI", "SO_LUONG_NHAP_CUOI", "SO_TIEN_NHAP_CUOI", "ITT_CODE", "VAT_TU", "DVT", "DG_CUOI",
    "CRITICAL", "SL_TON", "GT_TON", "SL_NHAP", "GT_NHAP", "SL_XUAT", "GT_XUAT", "SL_CUOI", "Column1", "GT_CUOI1",
    "CF_APE_DATE",
]  # fmt: skip
PERIOD_TEXT = "Từ ngày 01-10-2026 đến ngày 31-10-2026"
# (ICA, code, name, SL_TON, GT_TON, SL_XUAT, GT_XUAT, SL_CUOI, GT_CUOI1) - real rows of GIÁ SỢI 4 THÁNG 10
STOCK_ROWS = [
    ("Bông", USA, 'COTTON Usa 1-5/32" 3.5~4.9 Green Card', "553312.08", "27660201661", "197056.56", "9850904728", "356255.52", "17809296933"),
    ("Bông", BRAZIL, 'COTTON Brazil 1-5/32" 3.5~4.9 Middling', "1198515.26", "60825840980", "433231.17", "21986910773", "765284.09", "38838930207"),
    ("Bông", "MN1100000010400032", "BONG B4 XU LY", "208.9", "3955251", "0", "0", "208.9", "3955251"),
    ("Xơ ", INDO_D, "PSF Indonesia 1.2D x 38mm Semidull Indorama Brand", "72879.2", "1851172530", "57543", "1574888613", "40280.2", "1102424762"),
    ("Xơ ", INDO_X, "PSF Indonesia 1.2D x 38mm Semidull Indorama Brand", "0", "0", "58998.69", "1954961714", "15823.01", "524306369"),
    ("Xơ ", "MN1001203811643001ID", "PSF China 1.2D x 38mm Semidull Recycle BHF brand", "302.05", "8973737", "0", "0", "302.05", "8973737"),
    ("Xơ ", "MN1000143812806001", "PSF Vietnam 1.4D x 38mm Semidull Recycle", "161.82", "3589677", "0", "0", "161.82", "3589677"),
    ("Do cty sx", YARN_CODE, "CM 20/1", "28077.84", "2314732367", "127909.94", "10499588485", "23854.32", "1958100295"),
    ("Mua ngoài", "MM0907503610000329IDR", "FDY 75D/36F/1", "44.44", "6466365", "44.44", "6466320", "44.44", "6466397"),
]  # fmt: skip


@pytest.fixture(autouse=True)
def _november_rate() -> None:
    ExchangeRateRepository().add(ExchangeRate(effective_date=date(2026, 10, 1), rate=D(25800), created_by="test"))


def xlsx(rows: list[list], title: str = "Sheet1") -> bytes:
    book = Workbook()
    sheet = book.active
    sheet.title = title
    for row in rows:
        sheet.append(row)
    stream = BytesIO()
    book.save(stream)
    return stream.getvalue()


def stock_file(rows: list[tuple] = STOCK_ROWS) -> UploadedFileDTO:
    data = [STOCK_HEADER]
    for ica, code, name, sl_ton, gt_ton, sl_xuat, gt_xuat, sl_cuoi, gt_cuoi in rows:
        data.append(
            [ica, None, None, None, code, name, "KG", 0, "N", float(sl_ton), float(gt_ton), 0, 0,
             float(sl_xuat), float(gt_xuat), float(sl_cuoi), 0, float(gt_cuoi), PERIOD_TEXT]
        )  # fmt: skip
    data.append([None] * 15 + [1789636.271])  # total row without ITT_CODE
    return UploadedFileDTO(filename="GIÁ SỢI 4 THÁNG 10.xlsx", content=xlsx(data))


ARRIVAL_HEADER_TOP = [None, "SUPPLIER", "COMMODITY", None, None, "Contract No.", None, "DELIVERY", None, None, None,
                      "COUNTRY OF ORIGIN", "SHIPMENT DATE", "ETA AT PORT", "ETA AT WAREHOUSE", "WAREHOUSE", "NOTE",
                      "Giá nhập kho"]  # fmt: skip
ARRIVAL_HEADER_LOW = [None, None, "Good Description", "TYPE", "Spec", "NO.", "DATE", "Quantity in kg", "Unit price",
                      "Term", "Value\n(USD)"]  # fmt: skip


def arrival_row(supplier, desc, qty, price, eta, warehouse, receiving=None, commodity="Polyester") -> list:
    return [None, supplier, commodity, desc, "1.2D*38MM", "C-1", "16/10/2026", qty, price, "CIF", None, "INDONESIA",
            None, None, eta, warehouse, None, receiving]  # fmt: skip


INDORAMA = "PT Indorama Polychem Indonesia"
INDO_DESC = "100% Polyester Staple Fiber"


def arrival_file(rows: list[list]) -> UploadedFileDTO:
    data = [["THEO DÕI XƠ VỀ"], ARRIVAL_HEADER_TOP, ARRIVAL_HEADER_LOW, *rows]
    content = xlsx(data, title="Update Fiber arrival 06.11")
    return UploadedFileDTO(filename="Ke hoach xo ve NM - 06.11.xlsx", content=content)


def default_arrivals() -> list[list]:
    return [
        arrival_row(INDORAMA, INDO_DESC, 50000, 1.255, datetime(2026, 11, 6), "MILL 4", receiving=1.28),
        arrival_row(
            "CARGILL", "US COTTON GC 31-3-37", 140000, 2.1579900844, datetime(2026, 11, 3), "MILL 4", commodity="Cotton"
        ),
        arrival_row(
            "TIMBRO", "BRAZIL COTTON MID", 300000, 1.997993444, datetime(2026, 11, 20), "MILL 4", commodity="Cotton"
        ),
        arrival_row("JIANGSU XINGHENG", "PSF China 1.0Dx38MM", 87, None, datetime(2026, 10, 15), "MILL 1"),
        arrival_row("GDI", "Recycle GDI", 522, 21800, datetime(2026, 11, 10), "MILL 4 (KDNĐ)"),
        arrival_row("TVC", "NANLON FIBER", 1000, 1.1, datetime(2026, 11, 10), "MILL 4 (SXXK)"),
        arrival_row("TVC", "NANLON FIBER", 2000, 1.1, datetime(2026, 11, 10), "MILL 1"),
    ]


def add_group(name: str, kind=PriceGroupKind.XO, origin=None) -> str:
    SavePriceGroupService().handle(SavePriceGroupRequest(name=name, kind=kind, origin=origin))
    setup = GetMaterialSetupService().handle(GetMaterialSetupRequest())
    return next(g.id for g in setup.groups if g.name == name)


def declare_codes(pairs: dict[str, tuple[str | None, MaterialMarket]]) -> None:
    rows = [
        StockItemRowDTO(
            accounting_code=code,
            decision=MaterialDecision.THEO_NHOM if gid else MaterialDecision.KHONG_TINH,
            price_group_id=gid,
            market=market,
        )
        for code, (gid, market) in pairs.items()
    ]
    SaveStockItemSettingsService().handle(SaveStockItemSettingsRequest(rows=rows))


def mapping_rows(pairs: dict[tuple[str, str], str]) -> None:
    listing = ListArrivalsService().handle(ListArrivalsRequest(factory_code=None))
    rows = []
    for m in listing.mappings:
        gid = next((g for (s, d), g in pairs.items() if m.supplier == s and m.description == d), None)
        if gid:
            rows.append(
                ArrivalMappingRowDTO(
                    supplier_key=m.supplier_key,
                    description_key=m.description_key,
                    decision=MaterialDecision.THEO_NHOM,
                    price_group_id=gid,
                )
            )
    SaveArrivalMappingsService().handle(SaveArrivalMappingsRequest(rows=rows))


def save_month(
    period: str = "2026-11", plan=((CottonOrigin.USA, "0.31"), (CottonOrigin.BRAZIL, "0.69")), recoveries=()
):
    SaveMonthlySettingService().handle(
        SaveMonthlySettingRequest(
            period=period,
            norm_factor=D("1.10"),
            default_fi=D("0.03"),
            cotton_plan_note="01/10 – 20/12",
            cotton_plan=[CottonShareDTO(origin=o, percent=D(p)) for o, p in plan],
            recoveries=[RecoveryDTO(group_id=g, usd_per_kg=D(v)) for g, v in recoveries],
        )
    )


def november_setup() -> dict[str, str]:
    """File kho tháng 10, nhóm giá, khai báo mã, hàng về tháng 11, khai báo tháng 11 (như file Giá nguyên liệu)."""
    ImportStockFileService().handle(ImportStockFileRequest(file=stock_file(), commit=True))
    ids = {
        "usa": add_group("Cotton USA", PriceGroupKind.COTTON, CottonOrigin.USA),
        "brazil": add_group("Cotton Brazil", PriceGroupKind.COTTON, CottonOrigin.BRAZIL),
        "indo": add_group("Poly nguyên sinh – Indorama"),
    }
    declare_codes(
        {
            USA: (ids["usa"], MaterialMarket.NOI_DIA),
            BRAZIL: (ids["brazil"], MaterialMarket.NOI_DIA),
            INDO_D: (ids["indo"], MaterialMarket.NOI_DIA),
            INDO_X: (ids["indo"], MaterialMarket.XUAT_KHAU),
        }
    )
    ImportArrivalFileService().handle(ImportArrivalFileRequest(file=arrival_file(default_arrivals()), commit=True))
    mapping_rows(
        {
            (INDORAMA, INDO_DESC): ids["indo"],
            ("CARGILL", "US COTTON GC 31-3-37"): ids["usa"],
            ("TIMBRO", "BRAZIL COTTON MID"): ids["brazil"],
        }
    )
    save_month(recoveries=((COTTON_PLAN_ID, "0.18"), (ids["indo"], "0.07")))
    return ids


def averages(period: str = "2026-11"):
    return GetMaterialAveragesService().handle(GetMaterialAveragesRequest(period=period))


def row_of(result, group_name: str, market: MaterialMarket):
    return next(r for r in result.rows if r.group_name == group_name and r.market == market)


# ---- AC-118 / AC-119: BR-86, BR-87 ----
def test_ac118_stock_file_read_and_saved() -> None:
    preview = ImportStockFileService().handle(ImportStockFileRequest(file=stock_file()))
    assert preview.period == "2026-10" and not preview.committed
    assert (preview.material_count, preview.yarn_count, preview.accessory_count) == (7, 1, 1)
    assert preview.new_codes == 7 and preview.rejected_rows == []
    done = ImportStockFileService().handle(ImportStockFileRequest(file=stock_file(), commit=True))
    assert done.committed and "Đã lưu file kho tháng 10/2026" in done.message
    month = StockMonthRepository().current("2026-10")
    usa = next(line for line in StockLineRepository().for_month(month.id) if line.accounting_code == USA)
    assert usa.closing_qty == D("356255.52") and usa.closing_value == D("17809296933")
    settings = StockItemSettingRepository().by_code()
    assert len(settings) == 7 and all(s.decision == MaterialDecision.CHUA_KHAI_BAO for s in settings.values())
    declare_codes({USA: (None, MaterialMarket.NOI_DIA)})
    again = ImportStockFileService().handle(ImportStockFileRequest(file=stock_file(), commit=True))
    assert again.new_codes == 0
    assert StockMonthRepository().current("2026-10").id != month.id
    assert any(m.id == month.id for m in StockMonthRepository().list_deleted())  # old version flagged, not removed
    assert StockItemSettingRepository().by_code()[USA].decision == MaterialDecision.KHONG_TINH


def test_ac119_market_suggested_from_code_suffix() -> None:
    ImportStockFileService().handle(ImportStockFileRequest(file=stock_file(), commit=True))
    settings = StockItemSettingRepository().by_code()
    assert settings[INDO_D].market == MaterialMarket.NOI_DIA
    assert settings[INDO_X].market == MaterialMarket.XUAT_KHAU
    assert settings["MN1001203811643001ID"].market == MaterialMarket.NOI_DIA
    assert settings["MN1000143812806001"].market == MaterialMarket.CHUNG


# ---- AC-120 / AC-121: BR-92 ----
def test_ac120_cotton_plan_average_matches_sales_file() -> None:
    november_setup()
    result = averages()
    assert result.problem == "" and result.exchange_rate == D(25800) and result.stock_period == "2026-10"
    usa = row_of(result, "Cotton USA", MaterialMarket.NOI_DIA)
    brazil = row_of(result, "Cotton Brazil", MaterialMarket.NOI_DIA)
    assert round(usa.average, 4) == D("1.9998") and round(brazil.average, 4) == D("1.9758")
    plan = row_of(result, "Cotton (phương án)", MaterialMarket.NOI_DIA)
    assert result.rows[0].group_name == "Cotton (phương án)"
    assert round(plan.average, 4) == D("1.9832") and round(plan.net_usd, 4) == D("1.8032")
    assert plan.net_vnd == plan.net_usd * 25800


def test_ac121_poly_domestic_export_and_shared_lot() -> None:
    november_setup()
    result = averages()
    domestic = row_of(result, "Poly nguyên sinh – Indorama", MaterialMarket.NOI_DIA)
    export = row_of(result, "Poly nguyên sinh – Indorama", MaterialMarket.XUAT_KHAU)
    assert round(domestic.average, 4) == D("1.1822") and round(domestic.net_usd, 4) == D("1.1122")
    assert round(export.average, 4) == D("1.2810")
    lot = next(x for x in ArrivalLotRepository().list_all() if x.supplier == INDORAMA)
    ArrivalLotRepository().save(lot.model_copy(update={"market": MaterialMarket.XUAT_KHAU}))
    domestic = row_of(averages(), "Poly nguyên sinh – Indorama", MaterialMarket.NOI_DIA)
    assert round(domestic.average, 4) == D("1.0608")


# ---- AC-122 / AC-123: BR-88, BR-85 ----
def test_ac122_new_month_copies_previous_and_months_stay_apart() -> None:
    save_month(recoveries=((COTTON_PLAN_ID, "0.18"),))
    december = GetMonthlySettingService().handle(GetMonthlySettingRequest(period="2026-12"))
    assert not december.saved and december.copied_from == "2026-11"
    assert december.norm_factor == D("1.10") and december.default_fi == D("0.03")
    assert [(s.origin, s.percent) for s in december.cotton_plan] == [
        (CottonOrigin.USA, D("0.31")),
        (CottonOrigin.BRAZIL, D("0.69")),
    ]
    save_month("2026-12", recoveries=((COTTON_PLAN_ID, "0.20"),))
    november = GetMonthlySettingService().handle(GetMonthlySettingRequest(period="2026-11"))
    assert november.saved and november.recoveries[0].usd_per_kg == D("0.18")
    fresh = GetMonthlySettingService().handle(GetMonthlySettingRequest(period="2026-01"))
    assert fresh.norm_factor == D("1.10") and fresh.cotton_plan == [] and fresh.copied_from == ""


def test_ac123_monthly_and_group_validation() -> None:
    with pytest.raises(AppError, match=r"Tổng tỷ lệ phương án pha bông phải bằng 100% \(hiện là 90%\)\."):
        save_month(plan=((CottonOrigin.USA, "0.31"), (CottonOrigin.BRAZIL, "0.59")))
    with pytest.raises(AppError, match="Hệ số phải lớn hơn 0."):
        SaveMonthlySettingService().handle(
            SaveMonthlySettingRequest(period="2026-11", norm_factor=D(0), default_fi=D("0.03"))
        )
    assert not GetMonthlySettingService().handle(GetMonthlySettingRequest(period="2026-11")).saved
    with pytest.raises(AppError, match="Nhóm cotton phải chọn xuất xứ."):
        SavePriceGroupService().handle(SavePriceGroupRequest(name="Cotton USA", kind=PriceGroupKind.COTTON))
    indo = add_group("Poly nguyên sinh – Indorama")
    with pytest.raises(AppError, match="Đã có nhóm giá 'poly nguyên sinh – indorama'."):
        SavePriceGroupService().handle(SavePriceGroupRequest(name="poly nguyên sinh – indorama"))
    ImportStockFileService().handle(ImportStockFileRequest(file=stock_file(), commit=True))
    with pytest.raises(AppError, match=f"Mã {INDO_D}: vui lòng chọn nhóm giá."):
        SaveStockItemSettingsService().handle(
            SaveStockItemSettingsRequest(
                rows=[
                    StockItemRowDTO(
                        accounting_code=INDO_D, decision=MaterialDecision.THEO_NHOM, market=MaterialMarket.NOI_DIA
                    )
                ]
            )
        )
    declare_codes({INDO_D: (indo, MaterialMarket.NOI_DIA), INDO_X: (indo, MaterialMarket.XUAT_KHAU)})
    deleted = SavePriceGroupService().handle(SavePriceGroupRequest(group_id=indo, delete=True))
    assert deleted.message == "Đã xoá nhóm giá 'Poly nguyên sinh – Indorama'; 2 mã kho trở về Chưa khai báo."
    settings = StockItemSettingRepository().by_code()
    assert settings[INDO_D].decision == MaterialDecision.CHUA_KHAI_BAO and settings[INDO_D].price_group_id is None


# ---- AC-124 / AC-125: BR-90, BR-91 ----
def test_ac124_arrival_file_rules_and_reimport() -> None:
    preview = ImportArrivalFileService().handle(ImportArrivalFileRequest(file=arrival_file(default_arrivals())))
    assert preview.sheet == "Update Fiber arrival 06.11" and preview.valid_count == 6
    assert [r.reason for r in preview.rejected_rows] == ["Chưa có đơn giá."]
    ImportArrivalFileService().handle(ImportArrivalFileRequest(file=arrival_file(default_arrivals()), commit=True))
    lots = {(lot.supplier, lot.factory_code): lot for lot in ArrivalLotRepository().list_all()}
    indo = lots[(INDORAMA, FactoryCode.S4)]
    assert (
        indo.market == MaterialMarket.CHUNG
        and indo.unit_price == D("1.255")
        and indo.eta_warehouse == date(2026, 11, 6)
    )
    assert lots[("GDI", FactoryCode.S4)].price_currency.value == "VND"
    assert lots[("GDI", FactoryCode.S4)].market == MaterialMarket.NOI_DIA
    assert lots[("TVC", FactoryCode.S4)].market == MaterialMarket.XUAT_KHAU
    assert ("TVC", FactoryCode.S1) in lots
    listing = ListArrivalsService().handle(ListArrivalsRequest())
    edited = listing.lots[0]
    SaveArrivalLotsService().handle(
        SaveArrivalLotsRequest(
            rows=[
                ArrivalLotRowDTO(
                    id=edited.id,
                    supplier=edited.supplier,
                    description=edited.description,
                    quantity=D(999),
                    unit_price=edited.unit_price,
                    eta_warehouse=edited.eta_warehouse,
                    warehouse=edited.warehouse,
                    factory_code=edited.factory_code,
                    market=edited.market,
                )
            ]
        )
    )
    assert ArrivalLotRepository().get(edited.id).quantity == D(999)
    again = ImportArrivalFileService().handle(
        ImportArrivalFileRequest(file=arrival_file(default_arrivals()), commit=True)
    )
    assert again.replace_count == 6 and "thay 6 lô cũ" in again.message
    assert ArrivalLotRepository().get(edited.id) is None  # file wins (5a): manual edit replaced, row flagged
    assert len(ArrivalLotRepository().list_all()) == 6
    with pytest.raises(AppError, match="Dòng 1: Số lượng phải lớn hơn 0."):
        SaveArrivalLotsService().handle(
            SaveArrivalLotsRequest(
                rows=[
                    ArrivalLotRowDTO(
                        supplier="X",
                        description="Y",
                        quantity=D(0),
                        unit_price=D(1),
                        eta_warehouse=date(2026, 11, 1),
                        warehouse="MILL 4",
                    )
                ]  # fmt: skip
            )
        )


def test_ac125_pairs_remembered_and_receiving_price() -> None:
    indo = add_group("Poly nguyên sinh – Indorama")
    ImportArrivalFileService().handle(ImportArrivalFileRequest(file=arrival_file(default_arrivals()), commit=True))
    listing = ListArrivalsService().handle(ListArrivalsRequest(only_unmapped=True))
    assert listing.unmapped_count == len(listing.lots) == 5  # S4 by default (one lot is MILL 1)
    mapping_rows({(INDORAMA, INDO_DESC): indo})
    rows = [
        *default_arrivals(),
        arrival_row(
            "PT INDORAMA POLYCHEM  INDONESIA", "100% polyester staple fiber", 10, 1.3, datetime(2026, 11, 2), "MILL 4"
        ),
    ]
    ImportArrivalFileService().handle(ImportArrivalFileRequest(file=arrival_file(rows), commit=True))
    listing = ListArrivalsService().handle(ListArrivalsRequest(group_id=indo))
    assert len(listing.lots) == 2 and {lot.group_name for lot in listing.lots} == {"Poly nguyên sinh – Indorama"}
    ImportStockFileService().handle(ImportStockFileRequest(file=stock_file(), commit=True))
    result = averages()
    assert result.undeclared_lots == 4 and result.undeclared_codes == 7
    domestic = row_of(result, "Poly nguyên sinh – Indorama", MaterialMarket.NOI_DIA)
    # no stock declared: 50 000 kg × 1,28 (giá nhập kho) + 10 kg × 1,3 (unit price, no giá nhập kho)
    assert domestic.arrival_qty == D(50010)
    assert domestic.average == (D(50000) * D("1.28") + D(10) * D("1.3")) / D(50010)


# ---- AC-126..AC-129: BR-93..BR-97 ----
def put_quote_yarn(trial: bool = True) -> Yarn:
    lines = [
        PriceLine(
            line_code="S4-5001",
            line_type=LineType.THUONG,
            cost=CostBreakdown(labor=D(20000)),
            accounting_code=YARN_CODE,
        )
    ]
    if trial:
        lines.append(
            PriceLine(line_code="S4-5001TN", line_type=LineType.THI_NGHIEM, cost=CostBreakdown(labor=D(60000)))
        )
    yarn = Yarn(
        factory_code=FactoryCode.S4,
        yarn_code="S4-5001",
        base_code="S4-5001",
        yarn_name="CVC 20/1 (60/40)",
        status=YarnStatus.CO_MA_KE_TOAN,
        components=[
            YarnComponent(material_label="CM - Ring", ratio=D("0.6"), carding_stage="C1", pass_no=1, nsm_carding=D(60)),
            YarnComponent(material_label="PE", ratio=D("0.4"), carding_stage="C2", pass_no=1, nsm_carding=D(60)),
        ],
        lines=lines,
        stage_details=[
            StageCostDetail(
                sequence=1,
                stage_code="C1",
                stage_name="Chải thô",
                material_label="CM - Ring",
                pass_no=1,
                run_minutes=D(1),
                cumulative_loss=D("0.15"),
            ),
            StageCostDetail(
                sequence=2,
                stage_code="C2",
                stage_name="Chải thô",
                material_label="PE",
                pass_no=1,
                run_minutes=D(1),
                cumulative_loss=D("0.08"),
            ),
        ],  # fmt: skip
    )
    YarnRepository().save_many([yarn])
    return yarn


def quote_request(ids: dict[str, str], **changes) -> CalculateQuoteRequest:
    values = {
        "period": "2026-11",
        "line_code": "S4-5001",
        "accounting_code": YARN_CODE,
        "customer_name": "Salponpat",
        "market": MaterialMarket.NOI_DIA,
        "order_qty": D(4000),
        "norm_factor": D("1.10"),
        "gp_percent": D("0.10"),
        "commission_percent": D("0.02"),
        "incoterm": Incoterm.CIF,
        "fi_usd": D("0.03"),
        "groups": {"CM - Ring": COTTON_PLAN_ID, "PE": ids["indo"]},
    }
    return CalculateQuoteRequest(**(values | changes))


def set_yarn_stock(qty: str, value: str) -> None:
    """Sợi tồn of month 10 for YARN_CODE (AC-126: 1.000 kg, 64.500.000 đ = 2,5 USD/kg)."""
    month = StockMonthRepository().current("2026-10")
    repo = StockLineRepository()
    line = next(x for x in repo.for_month(month.id) if x.accounting_code == YARN_CODE)
    repo.save(line.model_copy(update={"closing_qty": D(qty), "closing_value": D(value)}))


def test_ac126_quote_numbers() -> None:
    ids = november_setup()
    put_quote_yarn()
    set_yarn_stock("1000", "64500000")
    form = GetQuoteFormService().handle(GetQuoteFormRequest(line_code="S4-5001", period="2026-11"))
    assert [(c.material_label, c.loss, c.suggested_group_id) for c in form.components] == [
        ("CM - Ring", D("0.15"), COTTON_PLAN_ID),
        ("PE", D("0.08"), ""),
    ]
    assert form.default_accounting_code == YARN_CODE and form.norm_factor == D("1.10") and form.default_fi == D("0.03")
    assert form.accounting_suggestions[0].code == YARN_CODE and form.accounting_suggestions[0].stock_qty == D(1000)
    quote = CalculateQuoteService().handle(quote_request(ids)).quote
    assert round(quote.material_usd, 4) == D("1.7564")
    assert round(quote.norm_usd, 4) == D("0.8527")
    assert round(quote.new_cost_usd, 4) == D("2.6091")
    assert quote.stock_qty == D(1000) and round(quote.stock_cost_usd, 4) == D("2.5")
    assert round(quote.avg_cost_usd, 4) == D("2.5873")
    assert round(quote.fob_usd, 4) == D("2.9401") and round(quote.cif_usd, 4) == D("2.9701")
    assert round(quote.fob_usd * quote.exchange_rate) == 75855
    assert quote.quote_no == ""  # Tính thử: nothing saved
    assert ListQuotesService().handle(ListQuotesRequest()).items == []


def test_ac127_trial_line_and_fob() -> None:
    ids = november_setup()
    put_quote_yarn()
    quote = (
        CalculateQuoteService()
        .handle(quote_request(ids, price_kind=PriceKind.THI_NGHIEM, accounting_code="", incoterm=Incoterm.FOB))
        .quote
    )
    assert round(quote.norm_usd, 4) == D("2.5581")
    assert quote.avg_cost_usd == quote.new_cost_usd and quote.stock_cost_usd is None
    assert quote.cif_usd is None and quote.fi_usd == 0


def test_ac128_quote_checks() -> None:
    ids = november_setup()
    put_quote_yarn()
    service = CalculateQuoteService()
    with pytest.raises(AppError, match="Tổng GP và Commission phải nhỏ hơn 100%."):
        service.handle(quote_request(ids, gp_percent=D("0.9"), commission_percent=D("0.1")))
    with pytest.raises(AppError, match="Thành phần 'PE' chưa chọn nhóm giá."):
        service.handle(quote_request(ids, groups={"CM - Ring": COTTON_PLAN_ID}))
    empty = add_group("Viscose – Birla")
    with pytest.raises(AppError, match="Nhóm 'Viscose – Birla' \\(Nội địa\\) chưa có giá tháng 11/2026"):
        service.handle(quote_request(ids, groups={"CM - Ring": COTTON_PLAN_ID, "PE": empty}))
    with pytest.raises(AppError, match=r"Chưa có file kho tháng 11/2026 \(tháng trước tháng tính\)"):
        service.handle(quote_request(ids, period="2026-12"))
    with pytest.raises(AppError, match="Số lượng đơn hàng phải lớn hơn 0."):
        service.handle(quote_request(ids, order_qty=D(0)))


def test_ac128_missing_exchange_rate() -> None:
    ids = november_setup()
    put_quote_yarn()
    with pytest.raises(AppError, match="Chưa có tỷ giá cho tháng 12/2025."):
        CalculateQuoteService().handle(quote_request(ids, period="2025-12"))
    assert averages("2025-12").problem == "Chưa có tỷ giá cho tháng 12/2025. Phòng SO thêm tỷ giá ở màn Dữ liệu nền."


def test_ac129_save_list_export_delete() -> None:
    ids = november_setup()
    put_quote_yarn()
    with acting_as(SALES):
        first = CalculateQuoteService().handle(quote_request(ids, commit=True))
        second = CalculateQuoteService().handle(quote_request(ids, commit=True, customer_name="Khách B"))
    year = date.today().year
    assert first.saved and first.quote.quote_no == f"BG-{year}-0001" and second.quote.quote_no == f"BG-{year}-0002"
    assert first.message.startswith(f"Đã lưu báo giá BG-{year}-0001 cho sợi CVC 20/1 (60/40): FOB ")
    listing = ListQuotesService().handle(ListQuotesRequest())
    assert [q.quote_no for q in listing.items] == [f"BG-{year}-0002", f"BG-{year}-0001"]
    assert listing.customers == ["Khách B", "Salponpat"]
    assert [q.quote_no for q in ListQuotesService().handle(ListQuotesRequest(customer="salponpat")).items] == [
        f"BG-{year}-0001"
    ]
    file = ExportQuotesService().handle(ExportQuotesRequest())
    rows = ExcelReader(sheet_name="Gia bao khach").read(UploadedFileDTO(filename=file.filename, content=file.content))
    # real yarn stock of month 10 (23 854,32 kg) is averaged in: FOB as computed, rounded to 4 decimals
    assert len(rows) == 2 and rows[1]["Giá FOB (USD/kg)"] == pytest.approx(float(first.quote.fob_usd), abs=1e-4)
    assert rows[1]["SL sợi tồn (kg)"] == pytest.approx(23854.32)
    assert "CM - Ring 60.0% · Cotton (phương án) 1.8032" in rows[1]["Thành phần"]
    stored = first.quote.fob_usd
    save_month(recoveries=((COTTON_PLAN_ID, "0.50"),))  # dữ liệu nền đổi: số đã lưu giữ nguyên (BR-97)
    assert ListQuotesService().handle(ListQuotesRequest()).items[1].fob_usd == stored
    with acting_as(SALES_B), pytest.raises(AppError, match="Chỉ người tính hoặc Phòng SO được xoá báo giá này."):
        DeleteQuoteService().handle(DeleteQuoteRequest(quote_id=first.quote.id))
    with acting_as(SALES):
        assert DeleteQuoteService().handle(DeleteQuoteRequest(quote_id=first.quote.id)).message == (
            f"Đã xoá báo giá BG-{year}-0001."
        )
        third = CalculateQuoteService().handle(quote_request(ids, commit=True))
    assert third.quote.quote_no == f"BG-{year}-0003"  # numbers never reused
    assert [q.quote_no for q in ListQuotesService().handle(ListQuotesRequest()).items] == [
        f"BG-{year}-0003",
        f"BG-{year}-0002",
    ]


# ---- AC-130: BR-84 ----
@pytest.mark.parametrize("roles", [("XS4",), ("KT",), ()])
def test_ac130_only_sales_and_so(roles: tuple[str, ...]) -> None:
    message = "Chỉ Sales hoặc Phòng SO được xem và thao tác giá nguyên liệu, giá báo khách."
    with acting_as(user_with(*roles, username="other")):
        for call in (
            lambda: GetMaterialAveragesService().handle(GetMaterialAveragesRequest(period="2026-11")),
            lambda: ListQuotesService().handle(ListQuotesRequest()),
            lambda: ListArrivalsService().handle(ListArrivalsRequest()),
            lambda: GetMaterialSetupService().handle(GetMaterialSetupRequest()),
            lambda: GetStockOutComparisonService().handle(GetStockOutComparisonRequest()),
        ):
            with pytest.raises(AppError, match=message):
                call()
    with acting_as(SALES):
        assert ListQuotesService().handle(ListQuotesRequest()).items == []
        add_group("Poly tái chế – BHF")


# ---- AC-131: BR-99 ----
def test_ac131_stock_out_comparison() -> None:
    ids = november_setup()
    put_quote_yarn()
    result = GetStockOutComparisonService().handle(GetStockOutComparisonRequest(period="2026-10"))
    indo = next(r for r in result.material_rows if r.accounting_code == INDO_D)
    assert round(indo.out_unit_usd, 4) == D("1.0608") and indo.note == "chưa có giá BQ tháng 10/2026"
    usa = next(r for r in result.material_rows if r.accounting_code == USA)
    assert usa.note == "chưa có giá BQ tháng 10/2026"
    yarn = result.yarn_rows[0]
    assert round(yarn.out_unit_usd, 4) == D("3.1816") and round(yarn.out_unit_vnd) == 82086
    assert yarn.note == "chưa tính giá báo khách"
    assert all(r.accounting_code != "MM0907503610000329IDR" for r in result.material_rows + result.yarn_rows)
    with acting_as(SALES):
        CalculateQuoteService().handle(quote_request(ids, commit=True))
    from backend.features.yarn_costing.repositories.material_price_repository import QuoteRepository

    repo = QuoteRepository()
    saved = repo.list_all()[0]
    repo.save(saved.model_copy(update={"avg_cost_usd": D("2.90")}))
    result = GetStockOutComparisonService().handle(GetStockOutComparisonRequest(period="2026-10"))
    yarn = result.yarn_rows[0]
    assert yarn.quote_no == saved.quote_no and round(yarn.difference_percent, 2) == D("9.71") and not yarn.is_gap
    tight = GetStockOutComparisonService().handle(GetStockOutComparisonRequest(period="2026-10", gap_percent=D(5)))
    assert tight.yarn_rows[0].is_gap and tight.gap_count >= 1
    with pytest.raises(AppError, match="Mức cảnh báo phải là số lớn hơn 0."):
        GetStockOutComparisonService().handle(GetStockOutComparisonRequest(gap_percent=D(0)))
    assert GetStockOutComparisonService().handle(GetStockOutComparisonRequest()).period == "2026-10"


# ---- AC-132: the existing behaviour stays ----
def test_ac132_existing_rate_and_prices_untouched() -> None:
    november_setup()
    put_quote_yarn()
    ExchangeRateRepository().add(ExchangeRate(effective_date=date(2026, 11, 1), rate=D(26000), created_by="test"))
    yarn = next(y for y in YarnRepository().list_all() if y.yarn_code == "S4-5001")
    assert yarn.regular_line.total_vnd == D(20000)  # VND price never changes with a rate
    assert averages().exchange_rate == D(26000)  # month 11 takes the rate of 01/11
    assert averages("2026-10").exchange_rate == D(25800)


# ---- Fix 2026-11-13: re-importing replaces every lot exactly once, recorded under the account that saved ----
def test_fix_reimport_replaces_all_lots_in_one_go() -> None:
    from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository

    first = arrival_file(default_arrivals())
    with acting_as(SALES):
        ImportArrivalFileService().handle(ImportArrivalFileRequest(file=first, commit=True))
        bigger = [*default_arrivals(), arrival_row(INDORAMA, INDO_DESC, 10, 1.3, datetime(2026, 11, 2), "MILL 4")]
        done = ImportArrivalFileService().handle(ImportArrivalFileRequest(file=arrival_file(bigger), commit=True))
    assert done.valid_count == 7 and done.replace_count == 6
    assert len(ArrivalLotRepository().list_all()) == 7  # every lot of the file, none lost
    assert len(ArrivalLotRepository().list_deleted()) == 6  # the previous lots flagged, never removed
    last = sorted(AuditLogRepository().list_all(), key=lambda a: a.created_at)[-1]
    assert last.username == "sales" and "6 → 7 lô" in last.detail


# ---- Supima (bổ sung 2026-11-13): BR-110..BR-113, AC-147..AC-152 ----
PIMA = "MN1100171614001009IDR"
PIMA_ROW = (
    "Bông",
    PIMA,
    "COTTON USA SJV PIMA 3.5~4.9 GC 2-2-48",
    "17244.91",
    "1619225117",
    "8550",
    "802809347",
    "8694.91",
    "816415770",
)


def supima_setup(supima_group: bool = True, loss_groups: bool = True) -> dict[str, str]:
    from backend.features.yarn_costing.models.enums import Technology
    from backend.features.yarn_costing.models.loss_group import LossGroup

    ids = november_setup()
    ids["pima"] = add_group("Cotton Pima")
    ImportStockFileService().handle(ImportStockFileRequest(file=stock_file([*STOCK_ROWS, PIMA_ROW]), commit=True))
    declare_codes({PIMA: (ids["pima"], MaterialMarket.NOI_DIA)})
    if loss_groups:
        from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository

        common = {"R": D("0.002"), "W": D("0.01"), "C1": D("0.075"), "DCM": D("0.005")}
        LossGroupRepository().save_many(
            [
                LossGroup(factory_code=FactoryCode.S4, group_key="CM COMPACT", yarn_group_label="CM COMPACT",
                          technology=Technology.RING, losses={**common, "CM": D("0.145"), "S Compact": D("0.005")}),
                LossGroup(factory_code=FactoryCode.S4, group_key="CM (SUPIMA 100%)", yarn_group_label="CM (SUPIMA 100%)",
                          technology=Technology.RING, losses={**common, "CM": D("0.12"), "S": D("0.005")}),
            ]
        )  # fmt: skip
    SaveMonthlySettingService().handle(
        SaveMonthlySettingRequest(
            period="2026-11",
            norm_factor=D("1.10"),
            default_fi=D("0.03"),
            cotton_plan=[CottonShareDTO(origin=CottonOrigin.USA, percent=D("0.31")), CottonShareDTO(origin=CottonOrigin.BRAZIL, percent=D("0.69"))],
            recoveries=[RecoveryDTO(group_id=COTTON_PLAN_ID, usd_per_kg=D("0.18")), RecoveryDTO(group_id=ids["indo"], usd_per_kg=D("0.07")),
                        RecoveryDTO(group_id=ids["pima"], usd_per_kg=D("0.30"))],
            supima_group_id=ids["pima"] if supima_group else "",
        )
    )  # fmt: skip
    return ids


def put_supima_yarn(code: str = "S4-6001", name: str = "CM 40/1 (SUPIMA 50%) COMPACT") -> Yarn:
    yarn = Yarn(
        factory_code=FactoryCode.S4,
        yarn_code=code,
        base_code=code,
        yarn_name=name,
        is_compact="COMPACT" in name,
        status=YarnStatus.DA_TINH_GIA,
        components=[YarnComponent(material_label="CM - Ring", ratio=D(1), carding_stage="C1", pass_no=1, nsm_carding=D(60))],
        lines=[PriceLine(line_code=code, line_type=LineType.THUONG, cost=CostBreakdown(labor=D(20000)))],
        stage_details=[StageCostDetail(sequence=1, stage_code="C1", stage_name="Chải thô", material_label="CM - Ring", pass_no=1,
                                       run_minutes=D(1), cumulative_loss=D("0.217"))],
    )  # fmt: skip
    YarnRepository().save_many([yarn])
    return yarn


def supima_request(**changes) -> CalculateQuoteRequest:
    values = {
        "period": "2026-11",
        "line_code": "S4-6001",
        "market": MaterialMarket.NOI_DIA,
        "order_qty": D(1000),
        "groups": {"CM - Ring": COTTON_PLAN_ID},
        "supima_percent": D("0.5"),
    }
    return CalculateQuoteRequest(**(values | changes))


PIMA_NET = D("816415770") / D(25800) / D("8694.91") - D("0.30")  # BQ Pima tồn tháng 10 − hồi phế 0,30


def plan_net() -> Decimal:
    return row_of(averages(), "Cotton (phương án)", MaterialMarket.NOI_DIA).net_usd


def test_ac147_supima_read_from_name_and_form() -> None:
    supima_setup()
    put_supima_yarn()
    put_supima_yarn("S4-6002", "CM 30/1 SUPIMA")
    put_supima_yarn("S4-6003", "CM 30/1")
    forms = {
        c: GetQuoteFormService().handle(GetQuoteFormRequest(line_code=c, period="2026-11"))
        for c in ("S4-6001", "S4-6002", "S4-6003")
    }
    assert [forms[c].supima_percent for c in ("S4-6001", "S4-6002", "S4-6003")] == [D("0.5"), D(1), D(0)]
    assert [(s.origin, s.percent) for s in forms["S4-6001"].cotton_plan] == [
        (CottonOrigin.USA, D("0.31")),
        (CottonOrigin.BRAZIL, D("0.69")),
    ]


def test_ac148_supima_formula_with_and_without_coin() -> None:
    supima_setup()
    put_supima_yarn()
    cotton = plan_net()
    no_coin = CalculateQuoteService().handle(supima_request()).quote
    expected = D("0.5") * cotton / (1 - D("0.242")) + D("0.5") * PIMA_NET / (1 - D("0.217"))
    assert round(no_coin.material_usd, 6) == round(expected, 6)
    part = no_coin.components[0]
    assert (part.supima_ratio, part.normal_loss, part.supima_loss) == (D("0.5"), D("0.242"), D("0.217"))
    assert round(part.normal_net, 6) == round(cotton, 6) and no_coin.coin_fee_usd == 0 and not no_coin.supima_coin
    coin = CalculateQuoteService().handle(supima_request(supima_coin=True)).quote
    fee = D("0.552") * D("1.05")
    assert coin.coin_fee_usd == fee and coin.supima_coin
    assert round(coin.material_usd - no_coin.material_usd, 6) == round(D("0.5") * fee / (1 - D("0.217")), 6)
    full = CalculateQuoteService().handle(supima_request(supima_percent=D(1))).quote  # 100%: the yarn's own loss
    assert round(full.material_usd, 6) == round(PIMA_NET / (1 - D("0.217")), 6)


def test_ac149_own_cotton_plan() -> None:
    supima_setup()
    put_supima_yarn()
    usa = row_of(averages(), "Cotton USA", MaterialMarket.NOI_DIA).average
    quote = (
        CalculateQuoteService()
        .handle(
            supima_request(supima_percent=D(0), cotton_plan=[CottonShareDTO(origin=CottonOrigin.USA, percent=D(1))])
        )
        .quote
    )
    assert round(quote.components[0].net_usd, 6) == round(usa - D("0.18"), 6)
    assert [(s.origin, s.percent) for s in quote.cotton_plan] == [(CottonOrigin.USA, D(1))]
    assert GetMonthlySettingService().handle(GetMonthlySettingRequest(period="2026-11")).cotton_plan[0].percent == D(
        "0.31"
    )
    with pytest.raises(AppError, match=r"Tổng tỷ lệ phương án bông phải bằng 100% \(hiện là 90%\)\."):
        CalculateQuoteService().handle(
            supima_request(cotton_plan=[CottonShareDTO(origin=CottonOrigin.USA, percent=D("0.6")),
                                        CottonShareDTO(origin=CottonOrigin.BRAZIL, percent=D("0.3"))])
        )  # fmt: skip


def test_ac150_supima_checks() -> None:
    supima_setup(supima_group=False, loss_groups=False)
    put_supima_yarn()
    with pytest.raises(AppError, match="Chưa khai báo nhóm giá Supima tháng 11/2026."):
        CalculateQuoteService().handle(supima_request())
    with pytest.raises(AppError, match="Tỷ lệ Supima phải từ 0 đến 100%."):
        CalculateQuoteService().handle(supima_request(supima_percent=D("1.2")))
    setting = GetMonthlySettingService().handle(GetMonthlySettingRequest(period="2026-11"))
    pima = next(g.id for g in setting.group_options if g.name == "Cotton Pima")
    request = SaveMonthlySettingRequest(
        period="2026-11", norm_factor=D("1.10"), default_fi=D("0.03"), cotton_plan=setting.cotton_plan,
        recoveries=setting.recoveries, supima_group_id=pima,
    )  # fmt: skip
    SaveMonthlySettingService().handle(request)
    with pytest.raises(AppError, match=r"Chưa có nhóm tiêu hao 'CM \(SUPIMA 100%\)' ở xưởng S4\."):
        CalculateQuoteService().handle(supima_request())
    with pytest.raises(AppError, match="Giá Supima coin không được âm."):
        SaveMonthlySettingService().handle(request.model_copy(update={"coin_usd": D(-1)}))
    december = GetMonthlySettingService().handle(GetMonthlySettingRequest(period="2026-12"))
    assert (december.supima_group_id, december.coin_usd, december.coin_tax) == (pima, D("0.552"), D("0.05"))


def test_ac151_saved_quote_and_export_show_supima() -> None:
    supima_setup()
    put_supima_yarn()
    saved = CalculateQuoteService().handle(supima_request(supima_coin=True, commit=True)).quote
    listed = ListQuotesService().handle(ListQuotesRequest()).items[0]
    assert (listed.supima_percent, listed.supima_coin, listed.coin_fee_usd) == (D("0.5"), True, D("0.552") * D("1.05"))
    file = ExportQuotesService().handle(ExportQuotesRequest())
    row = ExcelReader(sheet_name="Gia bao khach").read(UploadedFileDTO(filename=file.filename, content=file.content))[0]
    assert row["Tỷ lệ Supima"] == 50 and row["Truyền điểm coin"] == "Có"
    assert row["Phí coin (USD/kg)"] == pytest.approx(0.5796) and row["Phương án bông"] == "USA 31.0% + Brazil 69.0%"
    assert saved.quote_no
