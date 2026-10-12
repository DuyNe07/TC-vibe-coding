"""Every business rule BR-xx: a passing and a failing case (pure business layer)."""

from datetime import date
from decimal import Decimal

import pytest

from backend.core.exceptions import BusinessRuleViolation
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.analysis_business import AnalysisBusiness
from backend.features.yarn_costing.business.dashboard_business import DashboardBusiness
from backend.features.yarn_costing.business.import_business import ImportBusiness
from backend.features.yarn_costing.business.loss_business import LossBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.name_business import YarnNameBusiness
from backend.features.yarn_costing.business.nsm_business import NsmInputBusiness
from backend.features.yarn_costing.business.price_line_business import PriceLineBusiness
from backend.features.yarn_costing.business.request_business import RejectReasonRule, RequestBusiness
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.costing import AdjustmentInput, NsmInput
from backend.features.yarn_costing.models.enums import (
    FactoryCode,
    GroupCode,
    LineType,
    LossGroupLevel,
    Technology,
    YarnOrigin,
    YarnStatus,
)
from backend.features.yarn_costing.models.loss_group import LossComponent, LossGroup
from backend.features.yarn_costing.models.master_checks import FileCheck
from backend.features.yarn_costing.models.packaging_type import PackagingType
from backend.features.yarn_costing.models.rate_version import RateLine
from backend.features.yarn_costing.models.user_group import GroupMember, UserGroup
from backend.features.yarn_costing.models.yarn import CostBreakdown, PriceLine, Yarn, YarnComponent
from backend.features.yarn_costing.repositories.stage_repository import StageRepository

D = Decimal

S4 = FactoryCode.S4


def yarn(code: str = "S4-1", name: str = "PE 30/1", status: YarnStatus = YarnStatus.DA_TINH_GIA, **extra) -> Yarn:
    parsed = YarnNameBusiness().analyze(name)
    return Yarn(
        factory_code=extra.pop("factory_code", S4),
        yarn_code=code,
        base_code=extra.pop("base_code", code),
        yarn_name=name,
        yarn_group=parsed.yarn_group,
        count=parsed.count,
        loss_group_key=parsed.loss_group_key,
        technology=YarnNameBusiness().technology(name),
        status=status,
        **extra,
    )


def regular(code: str, total: str, accounting: str | None = None) -> PriceLine:
    return PriceLine(
        line_code=code, line_type=LineType.THUONG, cost=CostBreakdown(labor=D(total)), accounting_code=accounting
    )


def messages(exc: pytest.ExceptionInfo) -> str:
    return exc.value.message


# ---- BR-01..BR-06 ---------------------------------------------------------------------------------------------------
def test_br01_br02_br03_br04_name_analysis() -> None:
    names = YarnNameBusiness()
    parsed = names.analyze("CVC 26/1 (50/50) (Re-PE 50%) MVS BCI")  # AC-43
    assert parsed.valid and parsed.count == 26 and parsed.yarn_group == "CVC"
    assert parsed.loss_group_key == "CVC (50/50) (RE-PE 50%) MVS BCI" and names.technology("x MVS") == Technology.MVS
    assert names.analyze("CVC 30/1 (60/40) recycle").loss_group_key == "CVC (60/40) RECYCLE"
    assert names.analyze("CM 40/1 COMPACT").is_compact and names.technology("CM 40/1 COMPACT") == Technology.RING
    assert names.analyze("VISCOSE 7.5/1").count == D("7.5")
    with pytest.raises(BusinessRuleViolation) as exc:  # AC-04
        names.ensure_valid(names.analyze("CVC 30 (60/40)"))
    assert "chi số dạng '<số>/1'" in messages(exc)


def test_br05_next_code_never_reuses_numbers() -> None:
    business = RequestBusiness()
    assert business.next_base_code(S4, []) == "S4-2020"  # AC-03 (legacy highest S4-2019)
    assert business.next_base_code(FactoryCode.S1, []) == "S1-1317"
    cancelled = yarn("S4-2021", status=YarnStatus.DA_HUY)
    accounting_like = yarn("S42003000010000000")
    assert business.next_base_code(S4, [cancelled, accounting_like]) == "S4-2022"  # AC-06


def test_br06_duplicate_name() -> None:
    business = RequestBusiness()
    existing = yarn("S4-2020", "PE 30/1", YarnStatus.CHO_XUONG_XEM)
    with pytest.raises(BusinessRuleViolation) as exc:  # AC-05
        business.ensure_unique_name(yarn("S4-2021", "pe  30/1"), [existing])
    assert "mã S4-2020" in messages(exc)
    business.ensure_unique_name(yarn("S4-2021", "pe 30/1"), [existing.model_copy(update={"status": YarnStatus.DA_HUY})])


def test_br07_br08_pending_requests() -> None:
    RequestBusiness().ensure_pending(yarn(status=YarnStatus.CHO_XUONG_XEM))
    with pytest.raises(BusinessRuleViolation) as exc:
        RequestBusiness().ensure_pending(yarn(status=YarnStatus.DA_TINH_GIA))
    assert "đang ở trạng thái 'Đã tính giá'" in messages(exc)
    RejectReasonRule().check("Không có máy")
    with pytest.raises(BusinessRuleViolation, match="Vui lòng nhập lý do."):
        RejectReasonRule().check("  ")


def test_br33_br44_codes() -> None:
    business = RequestBusiness()
    assert business.next_revision(
        "S4-586",
        [
            yarn("S4-586 (ĐCNSM1)", base_code="S4-586", revision_no=1),
            yarn("S4-586 (ĐCNSM2)", base_code="S4-586", revision_no=2),
        ],
    ) == ("S4-586 (ĐCNSM3)", 3)
    assert business.normalize_import_code("S4 - 586 (ĐCNSM2)") == ("S4-586 (ĐCNSM2)", "S4-586", 2)  # AC-26
    assert business.normalize_import_code("S4-586(ĐCNSM)") == ("S4-586 (ĐCNSM1)", "S4-586", 1)
    assert business.normalize_import_code("S42003000010000000") == ("S42003000010000000", "S42003000010000000", 0)


# ---- BR-09..BR-12, BR-32, BR-33, BR-38 ------------------------------------------------------------------------------
def comp(label: str, ratio: str, line: str = "", nsm: int | None = None) -> YarnComponent:
    return YarnComponent(
        material_label=label, ratio=D(ratio), carding_stage=line, nsm_carding=D(nsm) if nsm is not None else None
    )


def nsm_input(**kw) -> NsmInput:
    base = {
        "yarn_code": "S4-1",
        "components": [comp("Cotton", "0.6", "C1", 65), comp("PE", "0.4")],
        "nsm": {"MD1": D(65)},
        "max_passes": {"C1": 1, "C2": 3, "C3": 3},
        "has_compact_stage": True,
    }
    return NsmInput(**(base | kw))


def test_br09_to_br12_nsm_input() -> None:
    business = NsmInputBusiness()
    business.ensure_valid(nsm_input())
    violations = business.collect_violations(nsm_input(components=[comp("Cotton", "0.6"), comp("PE", "0.3")]))
    assert violations[0].message == "Tổng tỷ lệ pha phải bằng 100% (hiện là 90,00%)."  # AC-10
    no_nsm = nsm_input(nsm={"MD1": D(0), "F": D(3)}, components=[comp("Cotton", "1", "C1", 0)])
    assert business.collect_violations(no_nsm)[0].rule_code == "BR-10"  # AC-44
    compact = business.collect_violations(nsm_input(is_compact=True, nsm={"S": D(10)}))
    assert compact[0].rule_code == "BR-11"  # AC-11
    assert business.collect_violations(nsm_input(nsm={"S": D(10)})) == []
    assert business.collect_violations(nsm_input(packaging_valid=False))[0].rule_code == "BR-12"


def test_br32_br33_br38() -> None:
    business = NsmInputBusiness()
    business.ensure_editable(nsm_input())
    with pytest.raises(BusinessRuleViolation, match="đã có mã kế toán nên không sửa được"):
        business.ensure_editable(nsm_input(is_locked=True))
    business.ensure_adjust_reason(nsm_input(adjust_reason="Đơn lớn"))
    with pytest.raises(BusinessRuleViolation, match="Vui lòng nhập lý do điều chỉnh."):
        business.ensure_adjust_reason(nsm_input())
    business.ensure_warning_reason(nsm_input(warning_stages=["C1"], warning_reason="Pima"))
    with pytest.raises(BusinessRuleViolation, match=r"NSM khác sợi cùng nhóm \(S4-9\) ở công đoạn: C1"):
        business.ensure_warning_reason(nsm_input(warning_stages=["C1"], reference_yarn_code="S4-9"))


# ---- BR-24..BR-29 ---------------------------------------------------------------------------------------------------
def group(key: str, losses: dict | None = None, components: list | None = None) -> LossGroup:
    return LossGroup(
        factory_code=S4,
        group_key=key,
        yarn_group_label=key,
        technology=Technology.RING,
        losses=losses or {},
        components=components or [],
        level=LossGroupLevel.THU_CAP if components else LossGroupLevel.SO_CAP,
    )


def test_br26_secondary_losses() -> None:
    stages = StageRepository().for_factory("S4")
    pe = group("PE NORMAL - RING", {"W": D("0.01"), "C2": D("0.025")})
    vi = group("VISCOSE - RING", {"W": D("0.02")})
    comps = [
        LossComponent(component_group_key=pe.group_key, ratio=D("0.65")),
        LossComponent(component_group_key=vi.group_key, ratio=D("0.35")),
    ]
    losses = LossBusiness().secondary_losses(comps, {g.group_key: g for g in (pe, vi)}, stages)
    assert losses["W"] == D("0.0135")  # AC-20 (Bình quân)
    assert losses["C2"] == D("0.025")  # Cộng thẳng


def test_br24_affected_and_locked_groups() -> None:
    business = LossBusiness()
    pe = group("PE NORMAL - RING", {"W": D("0.01")})
    tr = group("TR (65/35)", components=[LossComponent(component_group_key=pe.group_key, ratio=D(1))])
    affected = business.affected_groups(pe.group_key, [pe, tr])
    assert affected == {pe.group_key, tr.group_key}
    locked_yarn = yarn("S4-5", "TR 30/1 (65/35)", lines=[regular("S4-5", "100", "KT1")])
    codes = business.locked_codes(affected, "S4", [locked_yarn])
    assert codes == ["S4-5"]
    with pytest.raises(BusinessRuleViolation) as exc:  # AC-18
        business.ensure_can_edit(pe.group_key, codes, is_so=False)
    assert "Chỉ Phòng SO được sửa." in messages(exc)
    business.ensure_can_edit(pe.group_key, codes, is_so=True)
    business.ensure_can_edit(pe.group_key, [], is_so=False)  # AC-19


def test_br25_br28_primary_group_values() -> None:
    business = LossBusiness()
    assert business.manual_losses({"W": D("0.012"), "XX": D("0.1"), "R": D(0)}, ["W", "R"]) == {"W": D("0.012")}
    business.ensure_valid_group("LINEN - RING", "S4", False, {"W": D("0.012")})
    with pytest.raises(BusinessRuleViolation, match="Tiêu hao phải từ 0% đến dưới 100%."):  # AC-37
        business.ensure_valid_group("LINEN - RING", "S4", False, {"W": D("1.2")})
    with pytest.raises(BusinessRuleViolation, match="đã có ở xưởng S4"):
        business.ensure_valid_group("LINEN - RING", "S4", True, {})


def test_br27_components() -> None:
    business = LossBusiness()
    a, b = group("A", {"W": D("0.01")}), group("B", {"W": D("0.02")})
    business.check_component_rows("C", [("A", D("0.5")), ("B", D("0.5"))], [a, b])
    with pytest.raises(BusinessRuleViolation, match=r"Tổng tỷ lệ thành phần phải bằng 100% \(hiện là 90,00%\)"):
        business.check_component_rows("C", [("A", D("0.5")), ("B", D("0.4"))], [a, b])
    with pytest.raises(BusinessRuleViolation, match="cần từ 1 đến 5 thành phần"):
        business.check_component_rows("C", [], [a, b])
    c = group("C", components=[LossComponent(component_group_key="A", ratio=D(1))])
    with pytest.raises(BusinessRuleViolation, match="không thể là thành phần của chính nó"):  # AC-46
        business.check_component_rows("A", [("C", D(1))], [a, b, c])


def test_br29_delete_group() -> None:
    LossBusiness().ensure_deletable(0, 0)
    with pytest.raises(BusinessRuleViolation, match="đang được dùng bởi 2 mã sợi / 1 nhóm sợi pha"):
        LossBusiness().ensure_deletable(2, 1)


# ---- BR-30..BR-35 ---------------------------------------------------------------------------------------------------
def test_br30_br31_trial_and_adjustment_lines() -> None:
    business = PriceLineBusiness()
    base = CostBreakdown(labor=D("19273.3054"))
    assert business.trial_cost(base, D(3)).total == D("57819.9162")  # AC-13
    assert business.adjustment_cost(base, LineType.CHIET_KHAU, D("0.05")).total == D("18309.64013")
    assert business.adjustment_cost(base, LineType.PHU_PHI, D("0.1")).total == D("21200.63594")
    y = yarn("S4-2020", lines=[regular("S4-2020", "1000")])
    y, ck = business.new_adjustment_line(
        y, LineType.CHIET_KHAU, AdjustmentInput(percent=D("0.05"), reason="x", order_ref="PO"), "a"
    )
    assert ck.line_code == "S4-2020 (CK1)" and ck.total_vnd == D(950)  # AC-14
    y = y.model_copy(update={"lines": [x for x in y.lines if x.line_code != ck.line_code]})
    _, ck2 = business.new_adjustment_line(
        y, LineType.CHIET_KHAU, AdjustmentInput(percent=D("0.05"), reason="x", order_ref="PO"), "a"
    )
    assert ck2.line_code == "S4-2020 (CK2)"  # never reused


def test_br32_status_follows_accounting_codes() -> None:
    business = PriceLineBusiness()
    assert business.status_for(yarn(lines=[regular("S4-1", "1", "KT")])) == YarnStatus.CO_MA_KE_TOAN
    assert (
        business.status_for(yarn(status=YarnStatus.CO_MA_KE_TOAN, lines=[regular("S4-1", "1")]))
        == YarnStatus.DA_TINH_GIA
    )


def test_br34_br35_adjustment_rules() -> None:
    business = PriceLineBusiness()
    business.ensure_adjustment_valid(AdjustmentInput(percent=D("0.05"), reason="Lớn", order_ref="PO-1"))
    with pytest.raises(BusinessRuleViolation, match="phải lớn hơn 0 và nhỏ hơn 100"):
        business.ensure_adjustment_valid(AdjustmentInput(percent=D(1), reason="Lớn", order_ref="PO-1"))
    with pytest.raises(BusinessRuleViolation, match="Vui lòng nhập lý do và đơn hàng cụ thể."):
        business.ensure_adjustment_valid(AdjustmentInput(percent=D("0.05"), reason="Lớn"))
    line = PriceLine(line_code="S4-1 (CK1)", line_type=LineType.CHIET_KHAU)
    business.ensure_deletable(line)
    with pytest.raises(BusinessRuleViolation, match="đã có mã kế toán, không xoá được"):  # AC-32
        business.ensure_deletable(line.model_copy(update={"accounting_code": "KT"}))
    with pytest.raises(BusinessRuleViolation):
        business.ensure_deletable(regular("S4-1", "1"))


# ---- BR-37..BR-39, BR-53..BR-55 -------------------------------------------------------------------------------------
def test_br37_br38_reference_yarn_and_warning() -> None:
    target = yarn("S4-3", "CVC 40/1 (60/40)", YarnStatus.CHO_XUONG_XEM)
    near = yarn("S4-1", "CVC 30/1 (60/40)", nsm={"S": D(12)}, components=[comp("Cotton", "1", "C1", 65)])
    far = yarn("S4-2", "CVC 20/1 (60/40)", components=[comp("Cotton", "1", "C1", 60)])
    other_tech = yarn("S4-4", "CVC 40/1 (60/40) MVS")
    reference = AnalysisBusiness().reference_yarn(target, [near, far, other_tech, target])
    assert reference is near  # AC-22
    stages = StageRepository().for_factory("S4")
    changed = target.model_copy(update={"nsm": {"S": D(10)}, "components": [comp("Cotton", "1", "C1", 60)]})
    assert AnalysisBusiness().warning_stages(changed, near, stages) == ["C1 (Cotton)"]  # S (Con) not warned
    assert AnalysisBusiness().reference_yarn(yarn("S4-9", "LINEN 30/1"), [near]) is None


def test_br39_price_anomalies() -> None:
    a = yarn("S4-1", "CVC 30/1 (60/40)", lines=[regular("S4-1", "20000")])
    b = yarn("S4-2", "CVC 40/1 (60/40)", lines=[regular("S4-2", "19500")])
    items = AnalysisBusiness().price_anomalies([a, b])
    assert [i.reason for i in items] == ["Chi số cao hơn nhưng giá không cao hơn"]  # AC-23
    ok = b.model_copy(update={"lines": [regular("S4-2", "21000")]})
    assert AnalysisBusiness().price_anomalies([a, ok]) == []


def test_br54_nsm_anomalies() -> None:
    ys = [
        yarn(f"S4-{i}", f"CM {20 + i}/1", components=[comp("Cotton", "1", "C1", v)]) for i, v in enumerate((65, 65, 60))
    ]
    items = AnalysisBusiness().nsm_anomalies(ys, {"S4": StageRepository().for_factory("S4")})
    assert [(i.yarn_code, i.stage_code, i.common_value) for i in items] == [("S4-2", "C1 (Cotton)", D(65))]  # AC-24


def test_br53_dashboard_fulfilment() -> None:
    statuses = [YarnStatus.DA_TINH_GIA] * 6 + [YarnStatus.TU_CHOI] * 2 + [YarnStatus.CHO_XUONG_XEM] * 2
    ys = [yarn(f"S4-{i}", f"CM {20 + i}/1", s, origin=YarnOrigin.YEU_CAU_SALES) for i, s in enumerate(statuses)]
    stats = DashboardBusiness().stats(ys, [], [], date(2000, 1, 1), date(2100, 1, 1))
    assert stats.new_request_count == 10 and stats.fulfilment_ratio == D(75)  # AC-25
    assert stats.waiting_count == 2
    empty = DashboardBusiness().stats([], [], [], date(2000, 1, 1), date(2000, 1, 2))
    assert empty.fulfilment_ratio is None and empty.quoted_count == 0


def test_br55_legacy_comparison() -> None:
    priced = yarn("S4-1", lines=[regular("S4-1", "1000.5")])
    assert AnalysisBusiness().compare_legacy("S4-1", D(1000), priced).matched
    diff = AnalysisBusiness().compare_legacy("S4-1", D(900), priced)
    assert not diff.matched and diff.diff_vnd == D("100.5")
    assert AnalysisBusiness().compare_legacy("S4-1", D(0), priced).diff_percent is None
    assert AnalysisBusiness().compare_legacy("S4-9", D(10), None).app_total is None


# ---- BR-41..BR-52 ---------------------------------------------------------------------------------------------------
def test_br41_br45_file_rules() -> None:
    business = ImportBusiness()
    business.ensure_file_valid(FileCheck(extension_ok=True, size_ok=True))
    with pytest.raises(BusinessRuleViolation, match=r"\.xlsx, \.xlsm hoặc \.xls"):  # AC-27
        business.ensure_file_valid(FileCheck(extension_ok=False, size_ok=True))
    assert business.sheet_skip_message("1. Input NSM", is_so=False) == ""
    assert (
        business.sheet_skip_message("Dinh muc (phut)", is_so=False)
        == "Sheet 'Dinh muc (phut)' chỉ Phòng SO được cập nhật, đã bỏ qua."
    )
    assert business.sheet_skip_message("Dinh muc (phut)", is_so=True) == ""


def test_br46_br47_br48_access() -> None:
    access = AccessBusiness()
    groups = [
        UserGroup(
            code=GroupCode.XS4,
            name="Xưởng Sợi 4",
            factory_code=S4,
            access_code="XS4-2026",
            members=[GroupMember(name="An")],
        ),
        UserGroup(code=GroupCode.SALES, name="Sales", access_code="SALES1", members=[GroupMember(name="Bình")]),
    ]
    assert access.verify("XS4", "XS4-2026", "An", groups, "UC-21", "S4").code == GroupCode.XS4
    with pytest.raises(BusinessRuleViolation, match="nhập đúng mã nội bộ"):  # AC-28
        access.verify("XS4", "sai", "An", groups, "UC-21")
    with pytest.raises(BusinessRuleViolation, match="Nhóm 'Sales' không được thực hiện thao tác này."):
        access.verify("SALES", "SALES1", "Bình", groups, "UC-21")
    with pytest.raises(BusinessRuleViolation, match="Bạn chỉ được thao tác dữ liệu của xưởng S4."):
        access.verify("XS4", "XS4-2026", "An", groups, "UC-21", "S1")
    entry = access.audit_entry(groups[0], "An", "UC-28", "S4-1", "a → b", "lý do")  # BR-49
    assert entry.action == "Nhập / sửa / xoá mã kế toán" and entry.group_code == "XS4"


def test_br50_br51_br52_master_rules() -> None:
    master = MasterBusiness()
    stages = StageRepository().for_factory("S4")
    master.ensure_valid_stages("S4", stages, set(), {s.stage_code for s in stages})
    duplicate = [*stages, stages[0].model_copy(update={"sequence": 99})]
    with pytest.raises(BusinessRuleViolation, match="Mã công đoạn 'C1' đã có ở xưởng S4."):  # AC-33
        master.ensure_valid_stages("S4", duplicate, set(), set())
    with pytest.raises(BusinessRuleViolation, match="Không xoá được công đoạn 'V'"):
        master.ensure_valid_stages(
            "S4", [s for s in stages if s.stage_code != "V"], {"V"}, {s.stage_code for s in stages}
        )
    line = RateLine(rate_code="C1", labor=D(1), depreciation=D(1), electricity=D(1), materials=D(1), overhead=D(1))
    master.ensure_valid_rate_version([line], ["C1"], False, date.today(), "Năm mới")
    with pytest.raises(BusinessRuleViolation, match="Thiếu định mức cho: Type 2."):  # AC-49
        master.ensure_valid_rate_version([line], ["C1", "Type 2"], False, date.today(), "Năm mới")
    with pytest.raises(BusinessRuleViolation, match="Vui lòng chọn ngày hiệu lực và nhập lý do."):
        master.ensure_valid_rate_version([line], ["C1"], False, None, "")
    pk = PackagingType(factory_code=S4, code="Type 1", name="x", minutes_per_kg=D("0.2"))
    master.ensure_valid_packaging("S4", [pk])
    with pytest.raises(BusinessRuleViolation, match="Mã đóng gói 'Type 1' đã có ở xưởng S4."):
        master.ensure_valid_packaging("S4", [pk, pk.model_copy(update={"id": "2"})])
    assert not master.is_selectable(pk, None)
    with pytest.raises(YarnValidationError, match="Mã nội bộ phải dài từ 4 đến 20 ký tự."):
        master.ensure_access_code("abc")


# ---- BR-56..BR-60 (2026-09-28) --------------------------------------------------------------------------------------
def test_br56_passes_and_duplicate_materials() -> None:
    business = NsmInputBusiness()
    three = [comp(f"M{i}", "0.25", "C3", 40) for i in range(3)]
    numbered = business.number_passes([*three, comp("Cotton", "0.25", "C1", 45)])
    assert [c.pass_no for c in numbered] == [1, 2, 3, 1]  # AC-52: lượt theo thứ tự dòng
    business.ensure_valid(nsm_input(components=[*three, comp("Cotton", "0.25", "C1", 45)]))
    four = [comp(f"M{i}", "0.25", "C3", 40) for i in range(4)]
    with pytest.raises(BusinessRuleViolation, match="C3 chỉ chạy tối đa 3 nguyên liệu trong một sợi."):  # AC-53
        business.ensure_valid(nsm_input(components=four))
    with pytest.raises(BusinessRuleViolation, match="Nguyên liệu 'PE' bị nhập 2 lần."):
        business.ensure_valid(nsm_input(components=[comp("PE", "0.5", "C2", 40), comp("pe", "0.5", "C3", 40)]))


def test_br57_material_of_the_loss_group() -> None:
    business = NsmInputBusiness()
    options = ["PE Normal - Ring", "Viscose - Ring"]
    ok = [comp("PE Normal - Ring", "0.65", "C2", 45), comp("Viscose - Ring", "0.35", "C3", 45)]
    business.ensure_valid(nsm_input(components=ok, material_options=options, group_key="TR (65/35)"))
    wrong = [comp("PE Normal - Ring", "0.65", "C2", 45), comp("Modal - Ring", "0.35", "C3", 45)]
    with pytest.raises(BusinessRuleViolation, match="Nguyên liệu 'Modal - Ring' không có trong nhóm tiêu hao"):  # AC-58
        business.ensure_valid(nsm_input(components=wrong, material_options=options, group_key="TR (65/35)"))
    business.ensure_valid(nsm_input(components=wrong))  # no loss group components → free text


def test_br58_pass_loss_and_br15_carding_checks() -> None:
    from backend.features.yarn_costing.business.costing_business import CostingBusiness
    from backend.features.yarn_costing.models.costing import FactoryData

    stages = StageRepository().for_factory("S4")
    rates = {
        s.stage_code: RateLine(
            rate_code=s.stage_code, labor=D(1), depreciation=D(1), electricity=D(1), materials=D(1), overhead=D(1)
        )
        for s in stages
        if not s.is_packaging
    }
    rates["Type 1"] = RateLine(
        rate_code="Type 1", labor=D(1), depreciation=D(0), electricity=D(0), materials=D(0), overhead=D(0)
    )
    pe = LossGroup(
        factory_code=S4,
        group_key="PE RECYCLE - RING",
        yarn_group_label="PE RECYCLE - RING",
        material="PE Recycle",
        technology=Technology.RING,
        losses={"C3": D("0.03"), "PD1": D("0.01"), "W": D("0.01")},
    )
    vi = LossGroup(
        factory_code=S4,
        group_key="VISCOSE - RING",
        yarn_group_label="VISCOSE - RING",
        material="Viscose",
        technology=Technology.RING,
        losses={"C3": D("0.034"), "W": D("0.02")},
    )
    blend = LossGroup(
        factory_code=S4,
        group_key="VR (70/30)",
        yarn_group_label="VR (70/30)",
        technology=Technology.RING,
        level=LossGroupLevel.THU_CAP,
        components=[
            LossComponent(component_group_key="VISCOSE - RING", ratio=D("0.7")),
            LossComponent(component_group_key="PE RECYCLE - RING", ratio=D("0.3")),
        ],
        losses={"C3": D("0.064"), "PD1": D("0.01"), "W": D("0.017")},
    )
    data = FactoryData(
        factory_code=S4,
        stages=stages,
        rates=rates,
        packaging={"Type 1": PackagingType(factory_code=S4, code="Type 1", name="x", minutes_per_kg=D("0.2"))},
        loss_groups={g.group_key: g for g in (pe, vi, blend)},
    )
    costing = CostingBusiness()
    both_c3 = [comp("Viscose - Ring", "0.7", "C3", 40), comp("PE Recycle - Ring", "0.3", "C3", 40)]
    y = yarn(
        "S4-7",
        "VR 30/1 (70/30)",
        packaging_code="Type 1",
        nsm={"W": D(50)},
        components=NsmInputBusiness().number_passes(both_c3),
    )
    result = costing.calculate(y, data)
    assert result.passed, result.reasons
    passes = [(d.stage_code, d.pass_no, d.material_label, d.loss) for d in result.details if d.stage_code == "C3"]
    assert passes == [("C3", 1, "Viscose - Ring", D("0.034")), ("C3", 2, "PE Recycle - Ring", D("0.03"))]  # AC-52
    swapped = y.model_copy(update={"components": NsmInputBusiness().number_passes(list(reversed(both_c3)))})
    assert costing.calculate(swapped, data).cost.total == result.cost.total  # order does not change the price
    moved = [both_c3[0], comp("PE Recycle - Ring", "0.3", "C2", 40)]
    y2 = y.model_copy(update={"components": NsmInputBusiness().number_passes(moved)})
    # AC-54 read with BR-64 (confirmed 2026-09-29): only C3 declared, running C2 -> the C3 loss is used, with a note
    borrowed = costing.calculate(y2, data)
    assert borrowed.passed, borrowed.reasons
    c2_borrowed = next(d for d in borrowed.details if d.stage_code == "C2")
    assert c2_borrowed.loss == D("0.03") and c2_borrowed.loss_note == "Tiêu hao lấy từ C3 (C2 chưa khai báo)"
    no_carding = data.model_copy(
        update={"loss_groups": {**data.loss_groups, pe.group_key: pe.model_copy(update={"losses": {"W": D("0.01")}})}}
    )
    assert (
        "C2 lượt 1 (PE Recycle - Ring): có NSM nhưng nguyên liệu chưa khai báo tiêu hao ở C2 hoặc C3. "
        "Vui lòng khai báo tiêu hao chải thô của nguyên liệu." in costing.check_match(y2, no_carding)
    )  # AC-73
    data2 = data.model_copy(
        update={
            "loss_groups": {
                **data.loss_groups,
                pe.group_key: pe.model_copy(update={"losses": {**pe.losses, "C2": D("0.025")}}),
            }
        }
    )
    ok = costing.calculate(y2, data2)
    assert ok.passed, ok.reasons
    c2 = next(d for d in ok.details if d.stage_code == "C2")
    assert c2.cumulative_loss == D("0.025") + D("0.01") + D("0.017")  # C2 + PD1 + W (cumulative_stages of C2)
    missing = y.model_copy(update={"components": NsmInputBusiness().number_passes(both_c3[:1])})
    assert (
        "Nguyên liệu PE Recycle - Ring có tiêu hao chải thô nhưng chưa có dòng thành phần trong sợi."
        in costing.check_match(missing, data)
    )
    primary = data.model_copy(update={"loss_groups": {"VR (70/30)": vi.model_copy(update={"group_key": "VR (70/30)"})}})
    two_c2 = [comp("A", "0.5", "C2", 40), comp("B", "0.5", "C2", 40)]
    y3 = y.model_copy(update={"components": NsmInputBusiness().number_passes(two_c2)})
    assert (
        "C2: nhóm tiêu hao chưa khai báo thành phần nên chưa xác định được tiêu hao từng lượt. Vui lòng khai báo thành phần cho nhóm tiêu hao."
        in costing.check_match(y3, primary)
    )  # AC-57


def test_br59_merge_c3_columns() -> None:
    from backend.features.yarn_costing.models.import_rows import LossRow

    business = ImportBusiness()
    a = LossRow(
        excel_row=5,
        yarn_group_label="MODAL",
        material="Modal",
        technology_text="Ring",
        losses={"C3.1": D("0.034"), "W": D("0.01")},
    )
    b = LossRow(
        excel_row=6,
        yarn_group_label="MODAL",
        material="Modal",
        technology_text="Ring",
        losses={"C3.2": D("0.035"), "W": D("0.01")},
    )
    merged = business.merge_duplicate_rows([a, b], S4)
    assert len(merged) == 1 and merged[0].losses["C3"] == D("0.034") and "C3.1" not in merged[0].losses  # AC-56
    c = b.model_copy(update={"losses": {"C3.2": D("0.035"), "W": D("0.02")}})
    assert len(business.merge_duplicate_rows([a, c], S4)) == 2  # other columns differ → still duplicates (BR-42)
    ratios_a = [None, D(1), None, None, None]  # ratio cell 'Other - C3.12' (primary group run on C3.1)
    ratios_b = [None, None, D(1), None, None]  # ratio cell 'Other - C3.22'
    pa = a.model_copy(update={"component_names": [""] * 5, "component_ratios": ratios_a})
    pb = b.model_copy(update={"component_names": [""] * 5, "component_ratios": ratios_b})
    assert len(business.merge_duplicate_rows([pa, pb], S4)) == 1  # the C3.x ratio cells are C3.x columns too
    single = business.merge_duplicate_rows(
        [LossRow(excel_row=7, yarn_group_label="X", losses={"C3.1": D(0), "C3.3": D("0.02")})], S4
    )
    assert single[0].losses == {"C3": D("0.02")}


def test_br60_default_packaging() -> None:
    master = MasterBusiness()
    t1 = PackagingType(factory_code=S4, code="Type 1", name="x", minutes_per_kg=D("0.2"))
    t3 = PackagingType(factory_code=S4, code="Type 3", name="y", minutes_per_kg=D("0.2"), is_default=True)
    master.ensure_single_default([t1, t3])
    with pytest.raises(BusinessRuleViolation, match="Mỗi xưởng chỉ được chọn một loại đóng gói mặc định."):  # AC-50
        master.ensure_single_default([t1.model_copy(update={"is_default": True}), t3])
    with pytest.raises(BusinessRuleViolation):
        master.ensure_single_default([t3.model_copy(update={"active": False})])
    assert master.default_packaging([t1, t3], None) is None  # no rate yet → not selectable → empty
