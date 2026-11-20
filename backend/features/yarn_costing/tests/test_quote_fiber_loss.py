"""Mở rộng 2026-11-20: tiêu hao báo giá theo loại xơ, cúi CM / cúi CD - BR-117..BR-120, AC-170..AC-176."""

from decimal import Decimal

import pytest

from backend.core.base import UploadedFileDTO
from backend.core.exceptions import AppError
from backend.features.yarn_costing.business.quote_business import QuoteBusiness
from backend.features.yarn_costing.dto.common_dto import YarnComponentDTO
from backend.features.yarn_costing.dto.loss_dto import CreatePrimaryLossGroupRequest
from backend.features.yarn_costing.dto.material_dto import (
    CalculateQuoteRequest,
    ExportQuotesRequest,
    GetMonthlySettingRequest,
    GetQuoteFormRequest,
    ListQuotesRequest,
    SaveMonthlySettingRequest,
)
from backend.features.yarn_costing.dto.pricing_dto import SaveYarnNsmRequest
from backend.features.yarn_costing.dto.request_dto import CreateYarnRequestRequest
from backend.features.yarn_costing.models.enums import (
    FactoryCode,
    FiberType,
    LineType,
    MaterialMarket,
    Technology,
    YarnStatus,
)
from backend.features.yarn_costing.models.loss_group import LossGroup
from backend.features.yarn_costing.models.material_price import COTTON_PLAN_ID, MonthlyMaterialSetting
from backend.features.yarn_costing.models.yarn import CostBreakdown, PriceLine, Yarn, YarnComponent
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository
from backend.features.yarn_costing.services.calculate_quote_service import CalculateQuoteService
from backend.features.yarn_costing.services.create_primary_loss_group_service import CreatePrimaryLossGroupService
from backend.features.yarn_costing.services.create_yarn_request_service import CreateYarnRequestService
from backend.features.yarn_costing.services.export_quotes_service import ExportQuotesService
from backend.features.yarn_costing.services.get_monthly_setting_service import GetMonthlySettingService
from backend.features.yarn_costing.services.get_quote_form_service import GetQuoteFormService
from backend.features.yarn_costing.services.list_quotes_service import ListQuotesService
from backend.features.yarn_costing.services.save_monthly_setting_service import SaveMonthlySettingService
from backend.features.yarn_costing.services.save_yarn_nsm_service import SaveYarnNsmService
from backend.features.yarn_costing.tests.helpers import setup_factory
from backend.features.yarn_costing.tests.test_material_price import (
    averages,
    november_setup,
    put_quote_yarn,
    put_supima_yarn,
    quote_request,
    row_of,
    supima_request,
    supima_setup,
)
from backend.shared.file_io.excel import ExcelReader

D = Decimal
S1, S4 = FactoryCode.S1, FactoryCode.S4
S1_CODE = "S1-5101"
OWN_TAIL = D("0.03")  # MD1 1% + R 1% + S 1% (C1 là chải thô, không cộng)


def form(line_code: str, period: str = "2026-11"):
    return GetQuoteFormService().handle(GetQuoteFormRequest(line_code=line_code, period=period))


def indo_net() -> Decimal:
    return row_of(averages(), "Poly nguyên sinh – Indorama", MaterialMarket.NOI_DIA).net_usd


def put_loss_groups(cm: bool = True, cd: bool = True, own_key: str = "CVC (60/40)") -> None:
    rows = [
        LossGroup(factory_code=S1, group_key=own_key, yarn_group_label=own_key, technology=Technology.RING,
                  losses={"C1": D("0.02"), "MD1": D("0.01"), "R": D("0.01"), "S": D("0.01")}),
    ]  # fmt: skip
    if cm:
        rows.append(LossGroup(factory_code=S4, group_key="CÚI CM", yarn_group_label="CÚI CM",
                              technology=Technology.RING, losses={"C1": D("0.075"), "CM": D("0.145")}))  # fmt: skip
    if cd:
        rows.append(LossGroup(factory_code=S4, group_key="CÚI CHẢI THÔ COTTON", yarn_group_label="CÚI CHẢI THÔ COTTON",
                              technology=Technology.RING, losses={"C1": D("0.075")}))  # fmt: skip
    LossGroupRepository().save_many(rows)


def put_s1_yarn(
    code: str = S1_CODE, name: str = "CVC 30/1 (60/40)", group: str = "CVC", key: str = "CVC (60/40)"
) -> Yarn:
    yarn = Yarn(
        factory_code=S1, yarn_code=code, base_code=code, yarn_name=name, yarn_group=group, loss_group_key=key,
        status=YarnStatus.DA_TINH_GIA,
        components=[YarnComponent(material_label="Cotton", ratio=D("0.6"), carding_stage=""),
                    YarnComponent(material_label="PE", ratio=D("0.4"), carding_stage="C1", pass_no=1, nsm_carding=D(60))],
        lines=[PriceLine(line_code=code, line_type=LineType.THUONG, cost=CostBreakdown(labor=D(30000)))],
    )  # fmt: skip
    YarnRepository().save_many([yarn])
    return yarn


def put_sliver_yarn(code: str = "S4-7001", vnd: str = "4866") -> None:
    YarnRepository().save_many(
        [
            Yarn(factory_code=S4, yarn_code=code, base_code=code, yarn_name="CÚI CM", yarn_group="CÚI CM",
                 loss_group_key="CÚI CM", status=YarnStatus.DA_TINH_GIA,
                 lines=[PriceLine(line_code=code, line_type=LineType.THUONG, cost=CostBreakdown(labor=D(vnd)))])
        ]
    )  # fmt: skip


def s1_request(ids: dict[str, str], **changes) -> CalculateQuoteRequest:
    values = {
        "period": "2026-11",
        "line_code": S1_CODE,
        "market": MaterialMarket.NOI_DIA,
        "order_qty": D(1000),
        "norm_factor": D("1.10"),
        "groups": {"Cotton": COTTON_PLAN_ID, "PE": ids["indo"]},
        "losses": {"Cotton": D("0.25"), "PE": D("0.04")},
    }
    return CalculateQuoteRequest(**(values | changes))


# ---- AC-170 ----
def test_ac170_losses_by_fiber_filled_and_editable() -> None:
    ids = november_setup()
    put_quote_yarn()
    data = form("S4-5001")
    assert [(c.material_label, c.fiber_type, c.default_loss) for c in data.components] == [
        ("CM - Ring", FiberType.COTTON_CHAI_KY, D("0.24")),
        ("PE", FiberType.XO_PE, D("0.04")),
    ]
    assert data.sliver_type is None and data.loss_problem == ""
    losses = {"CM - Ring": D("0.24"), "PE": D("0.04")}
    quote = CalculateQuoteService().handle(quote_request(ids, losses=losses)).quote
    pe = quote.components[1]
    assert pe.loss == D("0.04") and pe.default_loss == D("0.04") and pe.fiber_type == FiberType.XO_PE
    assert round(pe.cost_usd, 8) == round(D("0.4") * indo_net() / D("0.96"), 8)
    assert quote.loss_version == 2
    edited = CalculateQuoteService().handle(quote_request(ids, losses=losses | {"PE": D("0.046")})).quote
    assert round(edited.components[1].cost_usd, 8) == round(D("0.4") * indo_net() / D("0.954"), 8)
    assert edited.components[1].default_loss == D("0.04")  # điền sẵn vẫn ghi lại
    with pytest.raises(AppError, match="Tiêu hao của PE phải từ 0% đến dưới 100%."):
        CalculateQuoteService().handle(quote_request(ids, losses=losses | {"PE": D(1)}))


# ---- AC-171 ----
@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("PE NORMAL - MVS", FiberType.XO_PE),
        ("PE COMPACT - RING", FiberType.XO_PE),
        ("PE RECYCLE - RING", FiberType.XO_KHAC),
        ("PE (GDI RE-PE) MVS - MVS", FiberType.XO_KHAC),
        ("PE (RE 1.5D) MVS - MVS", FiberType.XO_KHAC),
        ("VISCOSE - RING", FiberType.XO_KHAC),
        ("SPANDEX 40D - MVS", FiberType.XO_KHAC),
        ("CDP - RING", FiberType.XO_KHAC),
        ("CD - RING", FiberType.COTTON_CHAI_THO),
        ("CM - RING", FiberType.COTTON_CHAI_KY),
        ("CM SIRO - RING", FiberType.COTTON_CHAI_KY),
    ],
)
def test_ac171_fiber_type_from_material_name(label: str, expected: FiberType) -> None:
    yarn = Yarn(factory_code=S4, yarn_code="S4-1", base_code="S4-1", yarn_name="X 30/1")
    component = YarnComponent(material_label=label, ratio=D(1), carding_stage="C1")
    assert QuoteBusiness().fiber_type(yarn, component) == expected


def test_ac171_generic_cotton_follows_combing_stage() -> None:
    component = YarnComponent(material_label="cotton - Ring", ratio=D("0.6"), carding_stage="C1")
    combed = Yarn(factory_code=S4, yarn_code="S4-2", base_code="S4-2", yarn_name="CVC 30/1 (60/40) COMPACT",
                  nsm={"CM": D(50), "MD1": D(100)})  # fmt: skip
    carded = Yarn(factory_code=S4, yarn_code="S4-3", base_code="S4-3", yarn_name="CVC 30/1 (60/40)",
                  nsm={"PCD1": D(100), "MD1": D(100)})  # fmt: skip
    assert QuoteBusiness().fiber_type(combed, component) == FiberType.COTTON_CHAI_KY
    assert QuoteBusiness().fiber_type(carded, component) == FiberType.COTTON_CHAI_THO


def test_ac171_default_from_month() -> None:
    yarn = Yarn(factory_code=S4, yarn_code="S4-1", base_code="S4-1", yarn_name="X 30/1",
                components=[YarnComponent(material_label=n, ratio=D("0.25"), carding_stage="C1")
                            for n in ("PE", "VISCOSE", "CD - RING", "CM - RING")])  # fmt: skip
    found = QuoteBusiness().default_losses(yarn, MonthlyMaterialSetting(period="2026-11"), [])
    assert [loss for _, loss in found] == [D("0.04"), D("0.08"), D("0.12"), D("0.24")]


# ---- AC-172 ----
def test_ac172_monthly_defaults_saved_copied_and_checked() -> None:
    november_setup()
    put_quote_yarn()
    SaveMonthlySettingService().handle(
        SaveMonthlySettingRequest(period="2026-12", norm_factor=D("1.10"), default_fi=D("0.03"), loss_combed=D("0.22"))
    )
    assert form("S4-5001", "2026-12").components[0].default_loss == D("0.22")
    assert form("S4-5001", "2026-11").components[0].default_loss == D("0.24")
    january = GetMonthlySettingService().handle(GetMonthlySettingRequest(period="2027-01"))
    assert not january.saved and january.loss_combed == D("0.22") and january.loss_pe == D("0.04")
    with pytest.raises(AppError, match="Tiêu hao mặc định phải từ 0% đến dưới 100%."):
        SaveMonthlySettingService().handle(
            SaveMonthlySettingRequest(period="2026-12", norm_factor=D("1.10"), default_fi=D("0.03"), loss_pe=D(1))
        )


# ---- AC-173 ----
def test_ac173_sliver_loss_adds_up() -> None:
    put_loss_groups()
    put_s1_yarn()
    data = form(S1_CODE)
    assert [(c.material_label, c.fiber_type, c.default_loss) for c in data.components] == [
        ("Cotton", FiberType.CUI_CM, D("0.22") + OWN_TAIL),
        ("PE", FiberType.XO_PE, D("0.04")),
    ]
    assert data.sliver_type == FiberType.CUI_CM
    put_s1_yarn("S1-5102", "CVCD 24/1 (60/40) MVS", "CVCD", "CVCD (60/40) MVS")
    carded = form("S1-5102")
    assert carded.components[0].fiber_type == FiberType.CUI_CD and carded.components[0].default_loss == D("0.075")
    assert carded.sliver_type == FiberType.CUI_CD
    wool = Yarn(factory_code=S1, yarn_code="S1-9", base_code="S1-9", yarn_name="COTTON/WOOL 16/1 (85/15)",
                yarn_group="COTTON/WOOL")  # fmt: skip
    assert QuoteBusiness().fiber_type(wool, YarnComponent(material_label="Cotton", ratio=D(1))) == FiberType.CUI_CM


def test_ac173_missing_sliver_group() -> None:
    put_loss_groups(cm=False)
    put_s1_yarn()
    data = form(S1_CODE)
    assert data.loss_problem == "Chưa có nhóm tiêu hao 'CÚI CM' ở xưởng S4."


# ---- AC-174 ----
def test_ac174_sliver_cost_ticked_and_saved() -> None:
    ids = november_setup()
    put_loss_groups()
    put_s1_yarn()
    put_sliver_yarn()
    plain = CalculateQuoteService().handle(s1_request(ids)).quote
    rate = plain.exchange_rate
    assert not plain.sliver_cost and plain.sliver_usd == 0
    assert round(plain.norm_usd, 8) == round(D(30000) / rate * D("1.10"), 8)
    ticked = CalculateQuoteService().handle(s1_request(ids, sliver_cost=True, commit=True)).quote
    sliver = D("0.6") * D(4866) / rate
    assert ticked.sliver_cost and ticked.sliver_code == "S4-7001" and ticked.sliver_vnd == D(4866)
    assert round(ticked.sliver_usd, 8) == round(sliver, 8)
    assert round(ticked.norm_usd, 8) == round((D(30000) / rate + sliver) * D("1.10"), 8)
    listed = ListQuotesService().handle(ListQuotesRequest()).items[0]
    assert listed.sliver_cost and listed.sliver_code == "S4-7001" and listed.loss_version == 2
    file = ExportQuotesService().handle(ExportQuotesRequest())
    row = ExcelReader(sheet_name="Gia bao khach").read(UploadedFileDTO(filename=file.filename, content=file.content))[0]
    assert row["Cúi (Có / Không)"] == "Có" and row["Mã cúi"] == "S4-7001"


def test_ac174_no_priced_sliver_code() -> None:
    ids = november_setup()
    put_loss_groups()
    put_s1_yarn()
    with pytest.raises(
        AppError, match="Chưa có giá mã Cúi CM ở xưởng S4. Vui lòng nhờ xưởng S4 nhập NSM cho mã Cúi CM."
    ):
        CalculateQuoteService().handle(s1_request(ids, sliver_cost=True))


# ---- AC-175 ----
def create(name: str, factory: FactoryCode = S4) -> str:
    request = CreateYarnRequestRequest(factory_code=factory, yarn_name=name, unknown_word_reason="mã cúi")
    return CreateYarnRequestService().handle(request).yarn.yarn_code


def test_ac175_sliver_code_created_and_priced_without_packaging() -> None:
    setup_factory(S4)
    for label, losses in (
        ("CÚI CM", {"C1": D("0.075"), "CM": D("0.145")}),
        ("CÚI CHẢI THÔ COTTON", {"C1": D("0.075")}),
    ):
        CreatePrimaryLossGroupService().handle(
            CreatePrimaryLossGroupRequest(
                factory_code=S4, yarn_group_label=label, technology=Technology.RING, losses=losses
            )
        )
    code = create("Cúi CM")
    yarn = next(y for y in YarnRepository().list_all() if y.yarn_code == code)
    assert (yarn.yarn_name, yarn.loss_group_key, yarn.count, yarn.packaging_code) == ("CÚI CM", "CÚI CM", None, None)
    cotton = [YarnComponentDTO(material_label="Cotton", ratio=D(1), carding_stage="C1", nsm_carding=D(65))]
    nsm = {"SBD": D(180), "CM": D(50), "DCM": D(83)}
    SaveYarnNsmService().handle(SaveYarnNsmRequest(yarn_code=code, components=cotton, nsm=nsm, save=True))
    priced = next(y for y in YarnRepository().list_all() if y.yarn_code == code)
    assert priced.status == YarnStatus.DA_TINH_GIA, priced.status_reasons
    assert priced.regular_line is not None and priced.regular_line.total_vnd > 0
    assert {d.stage_code for d in priced.stage_details} == {"C1", "SBD", "CM", "DCM"}  # không có F
    carded = create("Cúi chải thô cotton")
    SaveYarnNsmService().handle(SaveYarnNsmRequest(yarn_code=carded, components=cotton, save=True))
    carded_yarn = next(y for y in YarnRepository().list_all() if y.yarn_code == carded)
    assert carded_yarn.loss_group_key == "CÚI CHẢI THÔ COTTON" and carded_yarn.status == YarnStatus.DA_TINH_GIA
    for name, factory in (("Cúi CM", S1), ("Cúi PE", S4)):
        with pytest.raises(AppError, match="chi số dạng"):
            create(name, factory)


# ---- AC-176 ----
def test_ac176_old_way_kept_and_supima_part_unchanged() -> None:
    ids = november_setup()
    put_quote_yarn()
    old = CalculateQuoteService().handle(quote_request(ids, commit=True)).quote  # không gửi tiêu hao = cách cũ
    assert old.loss_version == 1 and [c.loss for c in old.components] == [D("0.15"), D("0.08")]
    assert all(c.fiber_type is None for c in old.components) and not old.sliver_cost


def test_ac176_supima_part_keeps_old_loss() -> None:
    supima_setup()
    put_supima_yarn()
    quote = CalculateQuoteService().handle(supima_request(losses={"CM - Ring": D("0.24")})).quote
    cotton = quote.components[0]
    assert cotton.normal_loss == D("0.24")  # bông thường: tiêu hao của thành phần
    assert cotton.supima_loss == D("0.217")  # phần Supima: nhóm "CM (SUPIMA 100%)" như cũ
    full = (
        CalculateQuoteService()
        .handle(supima_request(supima_percent=D(1), losses={"CM - Ring": D("0.24")}))
        .quote.components[0]
    )
    assert full.supima_loss == D("0.217")  # 100% Supima: tiêu hao cách cũ của thành phần
