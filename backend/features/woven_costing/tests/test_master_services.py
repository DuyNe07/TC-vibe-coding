"""Phòng SO services: fabric files (UC-01..UC-04, UC-39), labels (UC-26), rates, norm / parameter sets, factors,
holidays, customers (UC-05..UC-13, UC-18, UC-31..UC-38) and the fabric override on a costsheet (UC-14)."""

from datetime import date
from decimal import Decimal

import pytest

from backend.core.base import EmptyRequest
from backend.core.exceptions import AppError, BusinessRuleViolation, ConflictError
from backend.features.woven_costing.dto.costsheet_dto import UpdateFabricOverrideRequest
from backend.features.woven_costing.dto.fabric_dto import (
    FabricSpecsDTO,
    FabricYarnDTO,
    LabelInputDTO,
    PreviewFabricImportRequest,
    PrintLabelRequest,
    SaveFabricRequest,
    SearchFabricsRequest,
)
from backend.features.woven_costing.dto.list_dto import AddCustomerRequest
from backend.features.woven_costing.dto.master_dto import (
    CustomerImportRequest,
    ListCustomersRequest,
    ParameterValueInputDTO,
    SaveExchangeRateRequest,
    SaveFabricFactorRequest,
    SaveHolidayRequest,
    SaveNormSetRequest,
    SaveParameterSetRequest,
    UpdateCustomerRequest,
    ViewNormSetRequest,
)
from backend.features.woven_costing.models.enums import (
    CostItem,
    CostsheetAction,
    CustomerTeam,
    FabricSource,
    FactorStage,
    HolidayAction,
    ImportResult,
    YarnDirection,
)
from backend.features.woven_costing.repositories.costing_data import load_costing_data
from backend.features.woven_costing.repositories.norm_repository import NormSetRepository
from backend.features.woven_costing.services.add_customer_service import AddCustomerService
from backend.features.woven_costing.services.create_costsheet_service import CreateCostsheetService
from backend.features.woven_costing.services.download_norm_template_service import DownloadNormTemplateService
from backend.features.woven_costing.services.get_costsheet_options_service import GetCostsheetOptionsService
from backend.features.woven_costing.services.list_customers_service import ListCustomersService
from backend.features.woven_costing.services.list_exchange_rates_service import ListExchangeRatesService
from backend.features.woven_costing.services.list_fabric_factors_service import ListFabricFactorsService
from backend.features.woven_costing.services.list_fabric_imports_service import ListFabricImportsService
from backend.features.woven_costing.services.list_holidays_service import ListHolidaysService
from backend.features.woven_costing.services.list_parameter_sets_service import ListParameterSetsService
from backend.features.woven_costing.services.preview_customer_import_service import PreviewCustomerImportService
from backend.features.woven_costing.services.preview_fabric_import_service import PreviewFabricImportService
from backend.features.woven_costing.services.preview_norm_set_service import PreviewNormSetService
from backend.features.woven_costing.services.print_label_service import PrintLabelService
from backend.features.woven_costing.services.save_customer_import_service import SaveCustomerImportService
from backend.features.woven_costing.services.save_exchange_rate_service import SaveExchangeRateService
from backend.features.woven_costing.services.save_fabric_factor_service import SaveFabricFactorService
from backend.features.woven_costing.services.save_fabric_import_service import SaveFabricImportService
from backend.features.woven_costing.services.save_fabric_service import SaveFabricService
from backend.features.woven_costing.services.save_holiday_service import SaveHolidayService
from backend.features.woven_costing.services.save_norm_set_service import SaveNormSetService
from backend.features.woven_costing.services.save_parameter_set_service import SaveParameterSetService
from backend.features.woven_costing.services.search_fabrics_service import SearchFabricsService
from backend.features.woven_costing.services.update_customer_service import UpdateCustomerService
from backend.features.woven_costing.services.update_fabric_override_service import UpdateFabricOverrideService
from backend.features.woven_costing.services.view_norm_set_service import ViewNormSetService
from backend.features.woven_costing.tests.helpers import (
    SALES_FS1,
    SO,
    TODAY,
    as_user,
    create_request,
    seed_master,
    xlsx,
)
from backend.shared.file_io import ExcelReader, WordReader

D = Decimal
SPEC = ["Width", "Cut W.", "Weight", "G/Mt", "Density Warp", "Density Weft", "Wale", "Gause", "Loop", "Needle",
        "SHR-Warp", "SHR-Weft", "Course"]  # fmt: skip
PEACE_HEAD = ["TCFNO_INST", "TCFNO", "Code", "Fabric", "Structure", "Fabric Kind", "TCFNO Status", "Date create",
              "Before", *SPEC[1:], "After", *SPEC[1:]]  # fmt: skip
WFX_HEAD = ["TCFNO", "Code", "Fabric", "Structure", "Date create", "Before", *SPEC[1:], "After", *SPEC[1:], "Remark"]
STD_HEAD = ["TCFNO", "YARN", "TCFNO-YARN", "CONDITIONS", "SEARCH", "FCODE", "CSP", "Code", "FNAME", "YCODE", "YNAME",
            "Direction", "Rate", "Direction", "YSEL", "Loai soi", "YCODE", "YNAME", "RATE"]  # fmt: skip
SPECS = [175, 175, 124, 217, 431, 252, 0, 0, 0, 0, 7.5, 5, 0]
FINISHED = [154, 154, 150, 230, 470, 280, 0, 0, 0, 0, 3, 2, 0]


def _peace_files() -> list:
    weaving = xlsx([PEACE_HEAD, [None, None, None, None, None, None, None, None, *SPEC, *SPEC],
                    ["GE", "GEF29900023", "C1", "FD 75D PEACE", "EF", "Export", "OFFICIAL", "2026/07/08", *SPECS, *FINISHED],
                    ["ZZ", "ZZ12340026", "C2", "MANUAL NOW PEACE", "ZZ", "", "", "2026/07/09", *SPECS, *FINISHED]],
                   "Weaving control.xlsx")  # fmt: skip
    standard = xlsx([STD_HEAD,
                     ["GEF29900023", "WARP", "", "", "", "", "", "", "", "Y1", "DTY 150D/48F/1 HIM", 1, 60, "Soi doc", "", "Soi don", "", "", 0],
                     ["GEF29900023", "WEFT", "", "", "", "", "", "", "", "Y2", "DTY 300D/96F/1 HIM", 2, 40, "Soi ngang", "", "Soi don", "", "", 0],
                     ["ZZ12340026", "WARP", "", "", "", "", "", "", "", "Y1", "TC 40/1", 1, 50, "", "", "", "", "", 0],
                     ["ZZ12340026", "WEFT", "", "", "", "", "", "", "", "Y1", "TC 40/1", 2, 50, "", "", "", "", "", 0]],
                    "TCFNO STANDARD.xlsx")  # fmt: skip
    return [weaving, standard]


def _wfx_files() -> list:
    weaving = xlsx([WFX_HEAD,
                    ["EF29900023", "W1", "FD 75D WFX", "EF", "08/07/2026", *SPECS, *FINISHED, ""],
                    ["EL37140026", "W2", "ONLY IN WFX", "EL", "09/07/2026", *SPECS, *FINISHED, "THONG SO"]],
                   "Weaving_Control_Report.xlsx")  # fmt: skip
    standard = xlsx([[*STD_HEAD, "TPM"],
                     ["EL37140026", "Warp", "", "", "", "", "", "", "", "Y3", "TC 30/1", 1, 55, "Sợi dọc", "", "Sợi đơn", "", "", 0, "0"],
                     ["EL37140026", "Weft", "", "", "", "", "", "", "", "Y4", "DTY 150D", 2, 45, "Sợi ngang", "", "Sợi se", "", "", 0, "400"]],
                    "TCFNO_Standard_Report.xlsx")  # fmt: skip
    return [weaving, standard]


def test_fabric_import_peace_first_wfx_kept_and_saved() -> None:
    """AC-01 (G removed, Peace priority, WFX-only kept), AC-02, AC-04 (manual -> Peace), UC-39."""
    with as_user(SO):
        SaveFabricService().handle(SaveFabricRequest(
            tcfno="ZZ12340026", fabric_name="Vải thí nghiệm", greige_width_cm=D(150), greige_warp_density=D(400),
            greige_weft_density=D(250), greige_g_per_m=D(200),
            yarns=[FabricYarnDTO(direction=YarnDirection.WARP, yarn_name="TC 40/1", rate=D(50)),
                   FabricYarnDTO(direction=YarnDirection.WEFT, yarn_name="TC 40/1", rate=D(50))]))  # fmt: skip
        request = PreviewFabricImportRequest(files=_peace_files() + _wfx_files())
        preview = PreviewFabricImportService().handle(request)
        rows = {r.tcfno: r for r in preview.rows}
        assert rows["EF29900023"].source == "Peace" and rows["EL37140026"].source == "WFX"
        assert rows["ZZ12340026"].result == ImportResult.CHANGED and preview.new_count == 2
        saved = SaveFabricImportService().handle(request)
        found = SearchFabricsService().handle(SearchFabricsRequest(keyword="EL3714", selected_tcfno="EL37140026"))
        manual = SearchFabricsService().handle(SearchFabricsRequest(selected_tcfno="ZZ12340026")).detail
        logs = ListFabricImportsService().handle(EmptyRequest())
    assert saved.message.startswith("Đã lưu: 2 mã mới, 1 mã cập nhật.")
    assert found.total == 1 and found.detail.greige_width_cm == D(175) and len(found.detail.yarns) == 2
    assert found.detail.yarns[1].twist_tpm == "400T/M" and found.detail.remark == "THONG SO"
    assert manual.source == FabricSource.PEACE and manual.fabric_name == "MANUAL NOW PEACE"
    peace = SearchFabricsService().handle(SearchFabricsRequest(selected_tcfno="EF29900023")).detail
    assert peace.fabric_name == "FD 75D PEACE" and peace.yarns[0].yarn_name == "DTY 150D/48F/1 HIM"
    assert len(logs.rows) == 1 and logs.rows[0].new_count == 2


def test_fabric_file_without_tcfno_column() -> None:
    """AC-03 (BR-70): nothing saved."""
    bad = xlsx([["Code", "Fabric", "Before"], ["X", "Y", 1]], "bad.xlsx")
    with as_user(SO), pytest.raises(BusinessRuleViolation) as error:
        PreviewFabricImportService().handle(PreviewFabricImportRequest(files=[bad]))
    assert error.value.message == "File bad.xlsx không đúng mẫu: thiếu cột TCFNO."


def test_manual_fabric_rules() -> None:
    """AC-05 (BR-72), UC-03 duplicate, PD allowed, Sales refused."""
    base = {"tcfno": "ZZ12340026", "fabric_name": "Thử", "greige_width_cm": D(150), "greige_warp_density": D(400),
            "greige_weft_density": D(250), "greige_g_per_m": D(200)}  # fmt: skip
    warp_only = SaveFabricRequest(
        **base, yarns=[FabricYarnDTO(direction=YarnDirection.WARP, yarn_name="TC", rate=D(100))]
    )
    with as_user(SO), pytest.raises(BusinessRuleViolation, match="Cần ít nhất 1 sợi dọc và 1 sợi ngang."):
        SaveFabricService().handle(warp_only)
    good = SaveFabricRequest(**base, yarns=[FabricYarnDTO(direction=YarnDirection.WARP, yarn_name="TC", rate=D(60)),
                                            FabricYarnDTO(direction=YarnDirection.WEFT, yarn_name="TC", rate=D(40))])  # fmt: skip
    with as_user(SO):
        assert SaveFabricService().handle(good).message == "Đã lưu mã vải ZZ12340026."
        with pytest.raises(ConflictError, match="Hãy dùng chức năng Sửa"):
            SaveFabricService().handle(good)
    with as_user(SALES_FS1), pytest.raises(BusinessRuleViolation):
        SaveFabricService().handle(good.model_copy(update={"is_new": False}))


def test_labels_four_on_one_page() -> None:
    """AC-37 / UC-26: 4 labels -> one 2 x 2 table, file nhan-<first>.docx."""
    seed_master()
    request = PrintLabelRequest(labels=[LabelInputDTO(tcfno="EM35790026", remark=f"R{i}") for i in range(4)])
    file = PrintLabelService().handle(request)
    content = WordReader().read(file.content)
    assert file.filename == "nhan-EM35790026.docx"
    assert len(content.tables) == 1 and len(content.tables[0]) == 2 and len(content.tables[0][0]) == 2
    assert "WIDTH: 154 CM / 61 INCH" in content.tables[0][0][0]
    with pytest.raises(AppError, match="Mã vải ZZ00000000 chưa có trong dữ liệu gốc."):
        PrintLabelService().handle(PrintLabelRequest(labels=[LabelInputDTO(tcfno="ZZ00000000")]))


def test_rates_holidays_factors() -> None:
    """UC-05 / UC-31, UC-11 / UC-34 (soft delete + restore), UC-10 / UC-33 (seed + new line)."""
    seed_master()
    with as_user(SO):
        msg = SaveExchangeRateService().handle(SaveExchangeRateRequest(month=9, year=2026, rate=D(26080)))
        SaveExchangeRateService().handle(SaveExchangeRateRequest(month=9, year=2026, rate=D(26100)))
        SaveHolidayService().handle(SaveHolidayRequest(date=date(2026, 9, 2), name="Quốc khánh"))
        SaveHolidayService().handle(SaveHolidayRequest(action=HolidayAction.DELETE, date=date(2026, 9, 2)))
        SaveHolidayService().handle(SaveHolidayRequest(date=date(2026, 9, 2), name="Quốc khánh"))
        SaveFabricFactorService().handle(SaveFabricFactorRequest(
            tcfno="EM35790026", stage=FactorStage.WEAVING, cost_item=CostItem.MATERIAL, multiplier=D("1.1"),
            effective_from=date(2026, 1, 1)))  # fmt: skip
    assert msg.message == "Đã lưu tỷ giá tháng 09/2026: 26.080."
    rates = ListExchangeRatesService().handle(EmptyRequest()).rows
    assert (rates[0].month, rates[0].rate) == (11, D(26000)) and rates[1].rate == D(26100)
    assert [h.name for h in ListHolidaysService().handle(EmptyRequest()).rows] == ["Quốc khánh"]
    factors = ListFabricFactorsService().handle(EmptyRequest()).rows
    assert len(factors) == 7 and {f.tcfno for f in factors} == {"ES17020213", "ES17020413", "EM35790026"}
    with as_user(SO), pytest.raises(BusinessRuleViolation, match="Tỷ giá phải lớn hơn 0."):
        SaveExchangeRateService().handle(SaveExchangeRateRequest(month=9, year=2026, rate=D(0)))


def test_parameter_sets() -> None:
    """UC-09 / UC-32, BR-64, BR-65."""
    first = ListParameterSetsService().handle(EmptyRequest())
    assert first.sets[0].effective_from == date(2026, 1, 1)
    assert next(p for p in first.latest if p.code == "sa_rate").default_value == D("0.1009")
    with as_user(SO):
        with pytest.raises(BusinessRuleViolation, match="Đã có bộ hiệu lực từ 01/01/2026"):
            SaveParameterSetService().handle(SaveParameterSetRequest(effective_from=date(2026, 1, 1)))
        with pytest.raises(AppError, match="VAT không hợp lệ."):
            SaveParameterSetService().handle(SaveParameterSetRequest(
                effective_from=date(2027, 1, 1), values=[ParameterValueInputDTO(code="vat_rate", value=D(2))]))  # fmt: skip
        SaveParameterSetService().handle(SaveParameterSetRequest(
            effective_from=date(2027, 1, 1), values=[ParameterValueInputDTO(code="sa_rate", value=D("0.1"))]))  # fmt: skip
    latest = ListParameterSetsService().handle(EmptyRequest())
    assert len(latest.sets) == 2 and next(p for p in latest.latest if p.code == "sa_rate").default_value == D("0.1")


def test_norm_template_round_trip_and_dates() -> None:
    """UC-06 template -> UC-37 preview (no error, no change) -> UC-07 save -> UC-08 view; AC-35 (BR-62); AC-36."""
    template = DownloadNormTemplateService(today=TODAY).handle(EmptyRequest())
    assert template.filename == "bo-dinh-muc-20261120.xlsx"
    upload = template.model_copy(update={}).content
    from backend.core.base import UploadedFileDTO

    file = UploadedFileDTO(filename="dm.xlsx", content=upload)
    with as_user(SO):
        preview = PreviewNormSetService().handle(SaveNormSetRequest(file=file, effective_from=date(2027, 1, 1)))
        assert preview.errors == [] and preview.changes == [] and len(preview.sheet_counts) == 12
        saved = SaveNormSetService().handle(SaveNormSetRequest(file=file, effective_from=date(2027, 1, 1), note="2027"))
    assert saved.message == "Đã lưu bộ định mức DM-20270101-01, hiệu lực từ 01/01/2027."
    repo = NormSetRepository()
    assert repo.effective_on(date(2026, 12, 31)).norm_set_code == "DM-20260101-01"
    assert repo.effective_on(date(2027, 1, 2)).norm_set_code == "DM-20270101-01"
    new_tables, old_tables = repo.by_code("DM-20270101-01").tables, repo.by_code("DM-20260101-01").tables
    assert len(new_tables.tcdn_processes) == len(old_tables.tcdn_processes)
    assert new_tables.twist_levels == old_tables.twist_levels and new_tables.lists == old_tables.lists
    view = ViewNormSetService(today=TODAY).handle(ViewNormSetRequest(norm_set_code="DM-20270101-01"))
    assert len(view.sets) == 2 and len(view.selected.tables) == 12
    sheets = ExcelReader().sheet_names(upload)
    missing = xlsx([], "thieu.xlsx", sheets={name: [["x"]] for name in sheets if name != "DinhMucDet"})
    with as_user(SO), pytest.raises(AppError) as error:
        SaveNormSetService().handle(SaveNormSetRequest(file=missing, effective_from=date(2028, 1, 1)))
    assert "Sheet DinhMucDet dòng 0: thiếu sheet." in error.value.details


def test_customers_import_add_update() -> None:
    """AC-40 (UC-12 / UC-36), AC-31 (UC-18), UC-13 (draft costsheets renamed), UC-35."""
    file = xlsx([["Team", "Customer", "Mã KH", "Other"], ["FS1", "Ichimura Sangyo", "ICHI", 1],
                 ["FS2", "ichimura  sangyo.", "", 2], ["FS3", "Other Team", "", 3],
                 ["FS1", "TEAM FORECAST FS1", "", 4], ["FS2", "Toyota Tsusho", "", 5]], "Data_clean.xlsx")  # fmt: skip
    with as_user(SO):
        preview = PreviewCustomerImportService().handle(CustomerImportRequest(file=file))
        saved = SaveCustomerImportService().handle(CustomerImportRequest(file=file))
    assert (preview.added, preview.skipped) == (2, 1) and saved.message == "Đã thêm 2 khách hàng, bỏ qua 1 tên trùng."
    assert [c.customer_code for c in ListCustomersService().handle(ListCustomersRequest()).rows] == ["ICHI", "TOYO"]
    with as_user(SALES_FS1):
        with pytest.raises(BusinessRuleViolation, match="Khách hàng Ichimura Sangyo đã có."):
            AddCustomerService().handle(AddCustomerRequest(name="ichimura sangyo."))
        ask = AddCustomerService().handle(AddCustomerRequest(name="Ichimura"))
        assert (
            [c.name for c in ask.similar] == ["Ichimura Sangyo"] and not ask.created and ask.suggested_code == "ICHI2"
        )
        done = AddCustomerService().handle(AddCustomerRequest(name="Ichimura", confirm_new=True))
    assert done.created and done.customer_code == "ICHI2"
    seed_master_fabric_and_rate()
    with as_user(SALES_FS1):
        sheet = CreateCostsheetService(today=TODAY).handle(create_request())
    customer = next(c for c in ListCustomersService().handle(ListCustomersRequest(keyword="ichimura s")).rows)
    with as_user(SO):
        UpdateCustomerService().handle(UpdateCustomerRequest(id=customer.id, name="Ichimura Sangyo Co.",
                                                             customer_code="ICHI", team=CustomerTeam.FS1))  # fmt: skip
    from backend.features.woven_costing.repositories.costsheet_repository import CostsheetRepository

    assert CostsheetRepository().get(sheet.id).customer_name == "Ichimura Sangyo Co."


def seed_master_fabric_and_rate() -> None:
    from backend.features.woven_costing.models.master import ExchangeRate
    from backend.features.woven_costing.repositories.fabric_repository import FabricRepository
    from backend.features.woven_costing.repositories.master_repository import ExchangeRateRepository
    from backend.features.woven_costing.tests.helpers import make_fabric

    FabricRepository().add(make_fabric())
    ExchangeRateRepository().add(ExchangeRate(month=11, year=2026, rate=D(26000)))


def test_fabric_override_only_for_manual_fabrics() -> None:
    """AC-41 (UC-14, BR-47): Peace fabric -> refused; manual fabric -> snapshot changed, master data unchanged."""
    seed_master()
    with as_user(SALES_FS1):
        peace = CreateCostsheetService(today=TODAY).handle(create_request())
        with pytest.raises(BusinessRuleViolation, match="không được sửa thông số"):
            UpdateFabricOverrideService(today=TODAY).handle(UpdateFabricOverrideRequest(costsheet_id=peace.id))
    with as_user(SO):
        SaveFabricService().handle(SaveFabricRequest(
            tcfno="ZZ12340026", fabric_name="Thử", greige_width_cm=D(150), greige_warp_density=D(400),
            greige_weft_density=D(250), greige_g_per_m=D(200), finished_weft_density=D(280), finished_g_per_m=D(220),
            yarns=[FabricYarnDTO(direction=YarnDirection.WARP, yarn_name="TC 40/1", rate=D(60)),
                   FabricYarnDTO(direction=YarnDirection.WEFT, yarn_name="TC 40/1", rate=D(40))]))  # fmt: skip
    with as_user(SALES_FS1):
        manual = CreateCostsheetService(today=TODAY).handle(create_request(tcfno="ZZ12340026"))
        assert CostsheetAction.EDIT_FABRIC in manual.allowed_actions
        changed = UpdateFabricOverrideService(today=TODAY).handle(
            UpdateFabricOverrideRequest(costsheet_id=manual.id, specs=FabricSpecsDTO(finished_weft_density=D(300)))
        )
    assert changed.fabric_overridden and changed.fabric.overridden_fields == ["finished_weft_density"]
    assert changed.result.shrinkage != manual.result.shrinkage
    assert load_costing_data("ZZ12340026").fabric.specs.finished_weft_density == D(280)


def test_options_and_empty_reads() -> None:
    """UC-38 with an empty database and no user."""
    options = GetCostsheetOptionsService(today=TODAY).handle(EmptyRequest())
    assert options.customers == [] and "Blended" in options.hcm_color_levels and options.counts
    assert "Soaping" in options.tcdn_stages and options.my_team == "FS1"
    assert ListFabricImportsService().handle(EmptyRequest()).rows == []
    assert SearchFabricsService().handle(SearchFabricsRequest()).total == 0
