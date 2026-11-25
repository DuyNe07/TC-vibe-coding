"""Validation rules (passing + failing case each) and the Se / Hồ hints (AC-06, AC-07, AC-08)."""

from datetime import date
from decimal import Decimal

import pytest

from backend.core.exceptions import BusinessRuleViolation
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.customer_business import CustomerBusiness
from backend.features.woven_costing.business.fabric_business import FabricBusiness
from backend.features.woven_costing.business.hint_business import HintBusiness
from backend.features.woven_costing.business.label_business import LabelBusiness
from backend.features.woven_costing.business.master_business import MasterBusiness
from backend.features.woven_costing.business.norm_business import NormBusiness
from backend.features.woven_costing.business.submission_business import SubmissionBusiness
from backend.features.woven_costing.business.workflow_business import WorkflowBusiness
from backend.features.woven_costing.models.costsheet import Costsheet, FabricSnapshot
from backend.features.woven_costing.models.enums import (
    CostsheetStatus,
    CustomerTeam,
    FabricSource,
    YarnDirection,
    YarnKind,
)
from backend.features.woven_costing.models.fabric import FabricSpecs, FabricYarn
from backend.features.woven_costing.models.master import Customer
from backend.features.woven_costing.models.norm_file import NormWorkbook
from backend.features.woven_costing.models.parameter_set import ParameterValues
from backend.features.woven_costing.tests.helpers import HEAD, LEAD_FS1, LEAD_FS2, SALES_FS1, SALES_FS2, SO, make_fabric

D = Decimal
W, F = YarnDirection.WARP, YarnDirection.WEFT


def _sheet(status: CostsheetStatus = CostsheetStatus.NHAP, **changes: object) -> Costsheet:
    values = {"costsheet_no": "CS-ICHI-2026-00001", "costing_date": date(2026, 11, 20), "tcfno": "EM35790026",
              "fabric_snapshot": FabricSnapshot(tcfno="EM35790026"), "status": status, "team": "FS1",
              "sales_username": "sales1"}  # fmt: skip
    return Costsheet(**(values | changes))


def _snapshot(name: str, *yarns: FabricYarn) -> FabricSnapshot:
    return FabricSnapshot(tcfno="EM00000000", fabric_name=name, yarns=list(yarns))


def test_ac06_spun_single_without_twist_needs_size() -> None:
    snap = _snapshot("TC34/1", FabricYarn(direction=W, seq=1, yarn_name="TC 34/1 (65/35)", raw_yarn_name="TC 34/1 (65/35)",
                                          rate=D(100), yarn_kind=YarnKind.SINGLE))  # fmt: skip
    lines = HintBusiness().build_yarn_lines(snap)
    assert lines[0].is_sized and lines[0].size_suggest_reason == "Sợi spun không se"


def test_ac07_him_filament_with_twist() -> None:
    snap = _snapshot("EM0415", FabricYarn(direction=W, seq=1, yarn_name="DTY 75D/36F/1 HIM - 400T/M",
                                          raw_yarn_name="DTY 75D/36F HIM", rate=D(100), twist_tpm="400T/M"))  # fmt: skip
    lines = HintBusiness().build_yarn_lines(snap)
    assert not lines[0].is_sized and lines[0].is_twisted


def test_ac08_khong_is_not_ho_but_ho_word_is() -> None:
    hints = HintBusiness()
    assert not hints.name_needs_size("TC 40/1 KHONG SE")
    assert hints.name_needs_size("PE 75D HO SOI") and hints.name_needs_size("DTY SIMHO")


def test_br08_spun_count_50_and_sim_filament() -> None:
    hints = HintBusiness()
    count = FabricYarn(direction=W, seq=1, yarn_name="TC 50/2 - 800T/M", raw_yarn_name="TC 50/1", rate=D(50),
                       twist_tpm="800T/M", yarn_kind=YarnKind.TWISTED)  # fmt: skip
    sim = FabricYarn(direction=W, seq=2, yarn_name="DTY 75D/72F/1 SIM", raw_yarn_name="DTY 75D/72F/1 SIM", rate=D(50))
    assert hints.warp_size_reasons([count, sim]) == ["Sợi spun chi số ≥ 50", "Filament SIM/NIM"]
    weft = FabricYarn(direction=F, seq=1, yarn_name="TC 50/1", raw_yarn_name="TC 50/1", rate=D(100))
    assert not HintBusiness().build_yarn_lines(_snapshot("X", weft))[0].is_sized  # BR-09: weft never sized


def test_br05_ratio_rule() -> None:
    hints = HintBusiness()
    assert hints.is_valid(D("1.00005"))
    assert hints.collect_violations(D("0.95"))[0].message.startswith("Tỷ lệ sợi không đúng (tổng = 95.00%)")


def test_br02_clean_code() -> None:
    fabric = FabricBusiness()
    assert fabric.clean_code("GEF29900023") == ("EF29900023", "")
    assert fabric.clean_code("EF2950.00.23SN04") == ("EF29500023", "SN04")
    with pytest.raises(BusinessRuleViolation) as error:
        fabric.ensure_code("04GC  0620")
    assert error.value.message == 'Mã vải "04GC  0620" không hợp lệ: cần đủ 10 ký tự chữ và số.'


def test_br04_yarn_normalisation_and_br72() -> None:
    from backend.features.woven_costing.models.fabric_import import YarnRecord

    yarns = FabricBusiness().normalize_yarns([
        YarnRecord(raw_code="X", direction="Sợi dọc", yarn_code="Y1", yarn_name="TC 50/2 - 800T/M", rate=D(60),
                   raw_yarn_code="0", raw_rate=D(0), yarn_kind="Soi se"),
        YarnRecord(raw_code="X", direction="Weft", yarn_name="DTY 150D", rate=D(40), tpm="400"),
    ])  # fmt: skip
    assert yarns[0].raw_yarn_code == "Y1" and yarns[0].raw_yarn_name == "TC 50/2 - 800T/M" and yarns[0].raw_rate == 100
    assert yarns[0].twist_tpm == "800T/M" and yarns[0].yarn_kind == YarnKind.TWISTED and yarns[1].twist_tpm == "400T/M"
    FabricBusiness().ensure_manual_yarns(yarns)
    with pytest.raises(BusinessRuleViolation, match="Cần ít nhất 1 sợi dọc và 1 sợi ngang."):
        FabricBusiness().ensure_manual_yarns(yarns[:1])


def test_br03_br47_fabric_rules() -> None:
    fabric = FabricBusiness()
    assert fabric.ensure_exists(make_fabric(), "EM35790026").tcfno == "EM35790026"
    with pytest.raises(BusinessRuleViolation, match="chưa có trong dữ liệu gốc"):
        fabric.ensure_exists(None, "ZZ12340026")
    fabric.ensure_override_allowed(FabricSnapshot(tcfno="ZZ12340026"), FabricSource.MANUAL)
    with pytest.raises(BusinessRuleViolation, match="lấy từ dữ liệu gốc Peace / WFX"):
        fabric.ensure_override_allowed(FabricSnapshot(tcfno="EM35790026"), FabricSource.PEACE)


def test_br30_to_br37_workflow_rules() -> None:
    flow = WorkflowBusiness()
    flow.ensure_transition(_sheet(), CostsheetStatus.CHO_DUYET)
    with pytest.raises(BusinessRuleViolation, match='Không thể chuyển costsheet từ "Nháp" sang "Đã duyệt".'):
        flow.ensure_transition(_sheet(), CostsheetStatus.DA_DUYET)
    flow.ensure_editable(_sheet(CostsheetStatus.TRA_LAI))
    with pytest.raises(BusinessRuleViolation, match="Costsheet đang ở trạng thái Chờ duyệt, không sửa được."):
        flow.ensure_editable(_sheet(CostsheetStatus.CHO_DUYET))
    flow.ensure_pending(_sheet(CostsheetStatus.CHO_DUYET))
    with pytest.raises(BusinessRuleViolation, match="Costsheet không ở trạng thái Chờ duyệt."):
        flow.ensure_pending(_sheet())
    flow.ensure_return_reason("Giá cao quá")
    with pytest.raises(BusinessRuleViolation, match="Vui lòng nhập lý do trả lại."):
        flow.ensure_return_reason("abc")
    flow.ensure_cancel(_sheet(), "Khách hủy")
    with pytest.raises(BusinessRuleViolation, match="Costsheet đã chốt đơn không hủy được."):
        flow.ensure_cancel(_sheet(CostsheetStatus.DA_CHOT_DON), "x")
    with pytest.raises(BusinessRuleViolation, match="Cần nhập OC trước khi chốt đơn."):
        flow.ensure_can_close(_sheet(CostsheetStatus.DA_DUYET), "")
    v1, v2 = _sheet(CostsheetStatus.DA_DUYET, version=1), _sheet(CostsheetStatus.NHAP, version=2)
    flow.ensure_no_open_version([v1])
    with pytest.raises(BusinessRuleViolation, match="đang có phiên bản 2 chưa duyệt"):
        flow.ensure_no_open_version([v1, v2])


def test_br40_oc_and_br41_number() -> None:
    flow = WorkflowBusiness()
    assert flow.clean_oc(" KDV10-SX-LO-0726-6564.1(VC260511), ") == "KDV10-SX-LO-0726-6564.1"
    flow.ensure_oc("KDV10-SX-LO-0726-6564")
    with pytest.raises(BusinessRuleViolation, match='OC "6564.1" sai định dạng'):
        flow.ensure_oc("6564.1")
    assert flow.main_oc("KDV10-SX-LO-0726-6564.1") == "KDV10-SX-LO-0726-6564"
    assert flow.costsheet_number("ICHI", 2026, ["CS-ABC-2026-00007", "CS-ICHI-2025-00099"]) == "CS-ICHI-2026-00008"
    closed = _sheet(CostsheetStatus.DA_CHOT_DON, costsheet_no="CS-A-2026-00002", oc_no="KDV10-SX-LO-0726-6564.1")
    flow.ensure_oc_free("KDV10-SX-LO-0726-6564.2", _sheet(), [closed])
    with pytest.raises(BusinessRuleViolation, match="đã được chốt ở costsheet CS-A-2026-00002"):
        flow.ensure_oc_free("KDV10-SX-LO-0726-6564.1", _sheet(), [closed])


def test_br44_working_days() -> None:
    """AC-29: Monday 16/11 -> Monday 23/11 = 5 working days; with a holiday = 4."""
    sub = SubmissionBusiness()
    assert sub.working_days(date(2026, 11, 16), date(2026, 11, 23), set()) == 5
    assert sub.working_days(date(2026, 11, 16), date(2026, 11, 23), {date(2026, 11, 18)}) == 4


def test_br42_br43_missing_data() -> None:
    sub = SubmissionBusiness()
    missing = sub.missing_data(_sheet())
    assert "khách hàng" in missing and "giá bán" in missing
    from backend.features.woven_costing.models.enums import SaleForm

    assert sub.missing_dyeing(_sheet(sale_form=SaleForm.FINISHED)) == [
        "nguyên liệu nhuộm + cấp màu, hoặc chi phí phát sinh"
    ]
    assert sub.missing_dyeing(_sheet(sale_form=SaleForm.GREIGE)) == []


def test_br50_customers() -> None:
    business = CustomerBusiness()
    ichi = Customer(customer_code="ICHI", name="Ichimura Sangyo", team=CustomerTeam.FS1)
    assert business.normalize("ichimura  sangyo.") == "ICHIMURA SANGYO"
    with pytest.raises(BusinessRuleViolation, match="Khách hàng Ichimura Sangyo đã có."):
        business.ensure_name_free("ichimura sangyo.", [ichi])  # AC-31
    assert [c.name for c in business.similar("Ichimura", [ichi])] == ["Ichimura Sangyo"]
    assert business.suggest_code("Ichimura Trading", {"ICHI"}) == "ICHI2"  # AC-42 / BR-50
    with pytest.raises(BusinessRuleViolation, match="Mã khách hàng ICHI đã dùng cho Ichimura Sangyo."):
        business.ensure_code("ICHI", [ichi])
    business.ensure_code("TOYO", [ichi])


def test_br51_to_br53_access() -> None:
    access = AccessBusiness()
    sheet = _sheet(CostsheetStatus.CHO_DUYET)
    assert access.team(SALES_FS1) == "FS1" and access.can_view(SALES_FS1, sheet) and access.can_view(SO, sheet)
    assert not access.can_view(SALES_FS2, sheet)  # AC-33
    assert access.can_approve(LEAD_FS1, sheet) and access.can_approve(HEAD, sheet)
    assert not access.can_approve(LEAD_FS2, sheet) and not access.can_approve(SALES_FS1, sheet)
    with pytest.raises(BusinessRuleViolation, match="Bạn không có quyền duyệt costsheet này."):
        access.ensure_approve(SALES_FS1, sheet)
    with pytest.raises(BusinessRuleViolation, match="chưa có vai trò"):
        access.ensure_use_case(SALES_FS1, "UC-07")
    access.ensure_use_case(SO, "UC-07")


def test_br60_to_br65_master_rules() -> None:
    master = MasterBusiness()
    master.ensure_rate(D(26000))
    with pytest.raises(BusinessRuleViolation, match="Tỷ giá phải lớn hơn 0."):
        master.ensure_rate(D(0))
    with pytest.raises(BusinessRuleViolation, match="Đã có bộ hiệu lực từ 01/01/2026. Chọn ngày khác."):
        master.ensure_unique_date(date(2026, 1, 1), [date(2026, 1, 1)])
    with pytest.raises(BusinessRuleViolation, match="Chưa có bộ định mức / tham số hiệu lực cho ngày 05/05/2025"):
        master.ensure_in_force(None, date(2025, 5, 5))
    assert master.parameter_violations(ParameterValues()) == []
    bad = ParameterValues(sa_rate=D("1.2"), gp_threshold=D(-2))
    assert master.parameter_violations(bad) == [
        "Tỷ lệ S&A trên giá vốn không hợp lệ.",
        "Ngưỡng cảnh báo GP% không hợp lệ.",
    ]
    values, overrides = master.apply_overrides(ParameterValues(), {"sa_rate": D("0.09"), "gp_threshold": D("0.1")})
    assert values.sa_rate == D("0.09") and values.gp_threshold == D("0.15") and len(overrides) == 1  # BR-46


def test_br63_and_br70_files() -> None:
    from backend.core.base import UploadedFileDTO

    errors = NormBusiness().validate(NormWorkbook())
    assert "Sheet DinhMucDet dòng 0: thiếu sheet." in errors  # AC-36
    with pytest.raises(BusinessRuleViolation, match="chỉ nhận file .xlsx / .xls"):
        MasterBusiness().ensure_file(UploadedFileDTO(filename="a.csv", content=b"x"))
    with pytest.raises(BusinessRuleViolation, match="File a.xlsx không đúng mẫu: thiếu cột TCFNO."):
        MasterBusiness().ensure_columns("a.xlsx", ["TCFNO"])  # AC-03


def test_br75_label() -> None:
    """AC-37: finished specs, WIDTH cm / inch, ratio rate / 100 x raw_rate / 100."""
    fabric = make_fabric("EM19600015").model_copy(
        update={
            "specs": FabricSpecs(
                finished_width_cm=D(154),
                finished_gsm=D(234),
                finished_g_per_m=D(360),
                finished_warp_density=D(608),
                finished_weft_density=D(236),
            ),  # fmt: skip
            "yarns": [FabricYarn(direction=W, seq=1, yarn_name="DTY 150D/48F/1 HIM", rate=D("38.59"), raw_rate=D(100))],
        }
    )
    label = LabelBusiness().build(fabric, "")
    assert (label.width_cm, label.width_inch, label.gsm, label.g_per_m) == ("154", "61", "234", "360")
    assert (label.warp_density, label.weft_density) == ("608", "236")
    assert label.yarn_lines == ["Warp 1: DTY 150D/48F/1 HIM 38.59%"]
