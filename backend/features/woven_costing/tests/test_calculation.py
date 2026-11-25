"""Calculation rules BR-10..BR-29 and the ACs that test them one by one (AC-10..AC-16, AC-18)."""

from datetime import date
from decimal import Decimal

from backend.features.woven_costing.business.costing_business import CostingBusiness
from backend.features.woven_costing.business.dyeing_hcm_business import DyeingHcmBusiness
from backend.features.woven_costing.business.dyeing_tcdn_business import DyeingTcdnBusiness
from backend.features.woven_costing.business.norm_lookup_business import NormLookupBusiness
from backend.features.woven_costing.business.pricing_business import PricingBusiness
from backend.features.woven_costing.business.quantity_business import QuantityBusiness
from backend.features.woven_costing.business.twist_business import TwistBusiness
from backend.features.woven_costing.business.yarn_cost_business import YarnCostBusiness
from backend.features.woven_costing.constants import STAGE_SINGEING
from backend.features.woven_costing.models.cost_items import CostItems
from backend.features.woven_costing.models.costing_context import CostingContext
from backend.features.woven_costing.models.costsheet_input import (
    HcmDyeingInput,
    PriceInput,
    TcdnDyeingInput,
    TcdnStageInput,
    TwistLine,
    YarnLine,
)
from backend.features.woven_costing.models.enums import (
    DyePlant,
    FactorStage,
    FiberSystem,
    OrderType,
    PriceType,
    SaleForm,
    ShrinkageException,
    YarnDirection,
)
from backend.features.woven_costing.models.master import initial_fabric_factors
from backend.features.woven_costing.models.norm_set import initial_tables
from backend.features.woven_costing.models.parameter_set import ParameterValues
from backend.features.woven_costing.tests.test_ac09_real_costsheets import R1, R2, R3

D = Decimal
P = ParameterValues()


def _context(sheet, **changes):  # type: ignore[no-untyped-def]
    return CostingContext(costsheet=sheet.model_copy(update=changes), tables=initial_tables(), params=P)


def test_ac10_quantity_factor() -> None:
    """AC-10 (BR-23): 7 500 m greige -> 1.025; Thí Nghiệm -> 2; table points."""
    q = QuantityBusiness()
    assert q.quantity_factor(D(7500), SaleForm.FINISHED, OrderType.PRODUCTION, P) == D("1.025")
    assert q.quantity_factor(D(7500), SaleForm.FINISHED, OrderType.TRIAL, P) == D(2)
    assert q.quantity_factor(D(4000), SaleForm.GREIGE, OrderType.PRODUCTION, P) == D("1.1")
    assert q.quantity_factor(D(15000), SaleForm.GREIGE, OrderType.PRODUCTION, P) == D(1)
    assert q.quantity_factor(D(50000), SaleForm.GREIGE, OrderType.PRODUCTION, P) == D("0.92")
    assert q.quantity_factor(D(200000), SaleForm.GREIGE, OrderType.PRODUCTION, P) == D("0.9")
    assert q.quantity_factor(D(7500), SaleForm.DYED, OrderType.PRODUCTION, P) == 0


def test_ac11_weft_loss_and_br11_warp_loss() -> None:
    """AC-11 (BR-12): width 150 with Se -> 6.19%; BR-11 example 0.82% + 1% + 2.06% = 3.88%."""
    yarns = YarnCostBusiness()
    assert round(yarns.weft_loss(D(150), True, P) * 100, 2) == D("6.19")
    line = YarnLine(direction=YarnDirection.WARP, seq=1, is_twisted=True, is_sized=True)
    assert yarns.warp_loss(line, P) == D("0.0388")


def test_ac12_fabric_factor() -> None:
    """AC-12 (BR-24): ES17020213 -> Vật tư dệt = norm x 1.12 + 231."""
    lookup = NormLookupBusiness(initial_tables())
    norm = lookup.weave_norm(25)
    factored = lookup.apply_factors(norm.items, FactorStage.WEAVING, "ES17020213", date(2026, 3, 1),
                                    initial_fabric_factors())  # fmt: skip
    assert factored.material == norm.items.material * D("1.12") + 231
    assert factored.labor == norm.items.labor * D("1.25")
    other = lookup.apply_factors(
        norm.items, FactorStage.WEAVING, "EM35790026", date(2026, 3, 1), initial_fabric_factors()
    )
    assert other == norm.items


def test_ac13_hcm_trial_doubles_chemical_and_labour() -> None:
    """AC-13 (BR-26): Thí Nghiệm -> HCTN and Tiền lương x2, other items unchanged."""
    hcm = HcmDyeingInput(dye_material="TC/CVC/TR thường", color_level="Đậm", dye_loss_rate=D("0.024"))
    prod = DyeingHcmBusiness(_context(R3, hcm_dyeing=hcm)).calculate(D(2000), D("2.78"))
    trial = DyeingHcmBusiness(_context(R3, hcm_dyeing=hcm, order_type=OrderType.TRIAL)).calculate(D(2000), D("2.78"))
    a, b = prod.lines[0].items, trial.lines[0].items
    assert b.chemical == a.chemical * 2 and b.labor == a.labor * 2
    assert b.depreciation == a.depreciation and b.power == a.power and b.overhead == a.overhead


def test_ac14_tcdn_coating_without_price() -> None:
    """AC-14 (BR-25): Coating without price -> chemical 0 and the "liên hệ TCDN" warning."""
    tcdn = TcdnDyeingInput(dye_material="Poly", color_level="White", extra_stages=[TcdnStageInput(name="Coating")])
    outcome = DyeingTcdnBusiness(_context(R2, tcdn_dyeing=tcdn)).calculate(D("0.1"), D("5.7"))
    coating = next(line for line in outcome.lines if line.name == "Coating")
    assert coating.items.chemical == 0
    assert "Thiếu giá hóa chất cho Coating: đang tính 0 (liên hệ TCDN)." in [w.message for w in outcome.warnings]


def test_ac15_interest_reduces_op() -> None:
    """AC-15 (BR-28): interest 500 đ/m -> OP lower by exactly 500."""
    business = CostingBusiness()
    base = business.calculate(_context(R3))
    with_interest = business.calculate(_context(R3, price=R3.price.model_copy(update={"interest_cost": D(500)})))
    assert base.op - with_interest.op == D(500)


def test_ac16_freight_by_price_type() -> None:
    """AC-16 (BR-29): CIF needs F&I; FOB -> F&I = 0 (hidden)."""
    pricing = PricingBusiness()
    assert not pricing.freight_check(PriceType.CIF, D(0)).ok
    assert pricing.collect_violations(pricing.freight_check(PriceType.CIF, D(0)))[0].message == (
        "Loại giá CIF cần nhập chi phí vận chuyển (và bảo hiểm)."
    )
    assert pricing.freight_check(PriceType.CIF, D(100)).ok
    assert pricing.effective_freight(PriceType.FOB, D(300)) == 0


def test_ac17_ac18_shrinkage_exception_and_pre_setting() -> None:
    """AC-17 (BR-13/BR-14): low shrinkage needs a reason; "Mộc khách đã ổn định" -> 0.
    AC-18 (BR-15): "Có pre-setting" calculates exactly like no exception."""
    business = CostingBusiness()
    low = R3.fabric_snapshot.model_copy(
        update={"specs": R3.fabric_snapshot.specs.model_copy(update={"finished_weft_density": D(249)})}
    )
    plain = business.calculate(_context(R3, fabric_snapshot=low))
    assert any(w.code == "BR-14" and w.blocking for w in plain.warnings)
    stable = business.calculate(_context(R3, fabric_snapshot=low, shrinkage_exception=ShrinkageException.STABLE_GREIGE))
    assert stable.shrinkage == 0 and stable.low_shrinkage and not any(w.code == "BR-14" for w in stable.warnings)
    pre = business.calculate(_context(R3, fabric_snapshot=low, shrinkage_exception=ShrinkageException.PRE_SETTING))
    assert pre.gp_pct == plain.gp_pct and pre.low_shrinkage and not any(w.code == "BR-14" for w in pre.warnings)


def test_br10_missing_specs_give_warning_not_error() -> None:
    specs = R3.fabric_snapshot.specs.model_copy(update={"greige_g_per_m": None})
    result = CostingBusiness().calculate(
        _context(R3, fabric_snapshot=R3.fabric_snapshot.model_copy(update={"specs": specs}))
    )
    assert not result.calculated and "thiếu g/m mộc" in result.warnings[0].message


def test_br20_singeing_and_count_check() -> None:
    """BR-20: Filament count with CB adds the singeing cost; Spun with a D count is an error."""
    lookup = NormLookupBusiness(initial_tables())
    twist = TwistBusiness()
    with_cb = twist.twist_norm(TwistLine(fiber_system=FiberSystem.FILAMENT, count="75D + CB", twist=400), lookup)
    tables = initial_tables()
    no_singe = tables.model_copy(update={"minute_rates": [
        r.model_copy(update={"rates": CostItems()}) if r.stage == STAGE_SINGEING else r for r in tables.minute_rates]})  # fmt: skip
    without = twist.twist_norm(TwistLine(fiber_system=FiberSystem.FILAMENT, count="75D + CB", twist=400),
                               NormLookupBusiness(no_singe))  # fmt: skip
    assert round(without.total, 2) == D("15279.10")  # value of the Excel files (sheet DM Se 2025)
    assert with_cb.total > without.total
    bad = twist.count_matches(TwistLine(fiber_system=FiberSystem.SPUN, count="75D", twist=400))
    assert twist.collect_violations(bad)[0].message == "Chi số 75D không khớp hệ sợi Spun. Vui lòng chọn lại."
    assert twist.count_matches(TwistLine(fiber_system=FiberSystem.SPUN, count="45/2", twist=800)).ok


def test_br21_twist_quantity_rule() -> None:
    from backend.features.woven_costing.models.checks import TwistQuantity

    yarns = YarnCostBusiness()
    assert yarns.is_valid(TwistQuantity(entered=D("10.005"), estimated=D(10)))
    assert yarns.collect_violations(TwistQuantity(entered=D(9), estimated=D(10)))[0].rule_code == "BR-21"


def test_br27_dyed_fabric_uses_bought_greige() -> None:
    """BR-27: Vải Nhuộm -> greige price x greige meters + dyeing - B/C; no weaving cost (BR-22)."""
    result = CostingBusiness().calculate(_context(R3, sale_form=SaleForm.DYED, greige_buy_price=D(21000)))
    assert result.weaving_total == 0 and result.quantity_factor == 0
    expected = D(21000) * result.greige_meters + result.dyeing_total - result.bc_liquidation
    assert result.total_cost == expected


def test_br28_usd_and_vat() -> None:
    result = CostingBusiness().calculate(_context(R1))
    assert result.sell_price_vnd == D("2.13") * D(26080)
    assert result.price_with_vat == result.sell_price_vnd * D("1.08")
    assert result.sa == result.cogs_vnd * D("0.1009")


def test_tcdn_factor_and_greige_without_dyeing() -> None:
    """BR-25 hệ số h; Mộc has no dyeing (BR-17 -> loss 0)."""
    small = _context(R2, order_meters=D(120))
    assert DyeingTcdnBusiness(small).factor() == D("1.2")
    large = _context(R2, order_meters=D(60000))
    assert DyeingTcdnBusiness(large).factor() == D("0.95")
    partial = _context(
        R2, order_meters=D(80), tcdn_dyeing=TcdnDyeingInput(extra_stages=[TcdnStageInput(name="Setting")])
    )
    assert DyeingTcdnBusiness(partial).factor() == D("1.5")
    assert DyeingHcmBusiness(_context(R1)).dye_loss() == 0
    assert _context(R1, dye_plant=DyePlant.TCDN).costsheet.sale_form == SaleForm.GREIGE


def test_price_input_defaults() -> None:
    assert PriceInput().commission == 0
