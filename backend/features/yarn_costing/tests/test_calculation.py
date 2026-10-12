"""AC-01 / AC-12 / AC-45: the calculation reproduces the real Excel results (BR-13..BR-23)."""

from decimal import Decimal

import pytest

from backend.features.yarn_costing.builders.dto_builders import components_from_rows
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.business.display_business import DisplayBusiness, format_usd, format_vnd
from backend.features.yarn_costing.business.name_business import YarnNameBusiness
from backend.features.yarn_costing.business.nsm_business import number_passes
from backend.features.yarn_costing.models.enums import FactoryCode, Technology
from backend.features.yarn_costing.models.exchange_rate import ExchangeRate
from backend.features.yarn_costing.models.yarn import Yarn
from backend.features.yarn_costing.repositories.factory_data_loader import load_factory_data
from backend.features.yarn_costing.tests.helpers import (
    S1_COMPONENTS,
    S1_NAME,
    S1_NSM,
    S4_COMPONENTS,
    S4_NAME,
    S4_NSM,
    TODAY,
    setup_factory,
)

D = Decimal

TOL = D("0.0001")


def make_yarn(factory: FactoryCode, code: str, name: str, nsm: dict, components: list, packaging: str) -> Yarn:
    parsed = YarnNameBusiness().analyze(name)
    return Yarn(
        factory_code=factory,
        yarn_code=code,
        base_code=code,
        yarn_name=name,
        yarn_group=parsed.yarn_group,
        count=parsed.count,
        loss_group_key=parsed.loss_group_key,
        technology=YarnNameBusiness().technology(name),
        is_compact=parsed.is_compact,
        packaging_code=packaging,
        nsm=nsm,
        components=number_passes(components_from_rows(components)),
    )


def by_stage(result) -> dict:
    return {d.stage_code: d for d in result.details}


def test_s4_2017_matches_the_workbook() -> None:
    setup_factory(FactoryCode.S4)
    yarn = make_yarn(FactoryCode.S4, "S4-2017", S4_NAME, S4_NSM, S4_COMPONENTS, "Type 3")
    result = CostingBusiness().calculate(yarn, load_factory_data(FactoryCode.S4))
    assert result.passed, result.reasons
    assert abs(result.cost.total - D("19777.8356")) < TOL
    stages = by_stage(result)
    expected = {
        "C1": ("0.9473", "0.2596", "3248.1454"),
        "C3": ("0.4060", "0.0701", "966.2922"),
        "CM": ("0.8526", "0.1811", "1217.9266"),
        "MD1": ("0.6", "0.0361", "437.0346"),
        "V": ("2.4", "0.0315", "11914.9353"),
    }
    for code, (minutes, cumulative, cost) in expected.items():
        assert abs(stages[code].run_minutes - D(minutes)) < TOL, code
        assert abs(stages[code].cumulative_loss - D(cumulative)) < TOL, code
        assert abs(stages[code].cost_per_kg - D(cost)) < TOL, code
    assert abs(stages["MD2"].cost_per_kg - D("485.2919")) < TOL
    assert abs(stages["MD3"].cost_per_kg - D("525.1312")) < TOL
    assert abs(stages["F"].cost_per_kg - D("983.0783")) < TOL  # AC-45: 4.479,605 × 0,2195
    assert stages["F"].cumulative_loss == 0 and stages["F"].nsm is None  # BR-18
    assert (stages["C3"].material_label, stages["C3"].pass_no) == ("Other - C3.3", 1)  # 4.14: one row per pass
    # AC-01: USD with 25.000 VND/USD, displayed 19.778 VND/kg and 0,7911 USD/kg (BR-22, BR-23)
    usd = CostingBusiness().usd_per_kg(result.cost.total, ExchangeRate(effective_date=TODAY, rate=D(25000)))
    assert format_vnd(result.cost.total) == "19.778"
    assert format_usd(usd) == "0,7911"  # type: ignore[arg-type]


def test_s1_1310_matches_the_workbook() -> None:
    setup_factory(FactoryCode.S1)
    yarn = make_yarn(FactoryCode.S1, "S1-1310", S1_NAME, S1_NSM, S1_COMPONENTS, "Type 1")
    result = CostingBusiness().calculate(yarn, load_factory_data(FactoryCode.S1))
    assert result.passed, result.reasons
    assert abs(result.cost.total - D("12169.6248")) < TOL
    stages = by_stage(result)
    assert abs(stages["C1"].run_minutes - D("2.04")) < TOL
    assert abs(stages["C1"].cumulative_loss - D("0.0644")) < TOL
    expected = {
        "C1": "2669.4087",
        "PD2": "430.5496",
        "MD1": "430.5496",
        "MD2": "428.2116",
        "MD3": "808.8624",
        "V": "5623.2387",
        "F": "1778.8043",
    }
    for code, cost in expected.items():
        assert abs(stages[code].cost_per_kg - D(cost)) < TOL, code
    assert format_vnd(result.cost.total) == "12.170"


def test_br17_run_minutes_and_br19_cumulative_loss() -> None:
    setup_factory(FactoryCode.S4)
    data = load_factory_data(FactoryCode.S4)
    business = CostingBusiness()
    c1 = data.stage("C1")
    assert c1 is not None
    # AC-12: 60 ÷ 45 × 1,015 × 0,7 = 0,9473
    assert abs(business.run_minutes(c1, D(45), data.recovery, D("0.7")) - D("0.9473")) < TOL
    assert business.run_minutes(c1, D(0), data.recovery, D("0.7")) == 0
    group = data.loss_groups["CORE (COTTON/ FDY 30D/24F/1) (70/30) MVS"]
    assert business.cumulative_loss(c1, group, D(0)) == 0
    # C1 adds SBD, PCD1, PCD2, CM, DCM, MD1..V but not C2 / C3 / PD / PD1
    assert abs(business.cumulative_loss(c1, group, D(1)) - D("0.2596")) < TOL


def test_br20_stage_cost_formula() -> None:
    setup_factory(FactoryCode.S4)
    data = load_factory_data(FactoryCode.S4)
    cost = CostingBusiness().stage_cost(data.rates["Type 3"], D("0.2194564694564695"), D(0))
    assert abs(cost.total - D("983.0783")) < TOL


def test_br13_visible_stages_follow_the_route() -> None:
    setup_factory(FactoryCode.S4)
    data = load_factory_data(FactoryCode.S4)
    codes = CostingBusiness().route_stage_codes(
        "B2 - C1 - C2 - SBD - PD - LF - CM - MD1 - MD2 - MD3 - R - S - W - F", data.stages
    )
    assert codes == ["C1", "C2", "SBD", "PD", "CM", "MD1", "MD2", "MD3", "R", "S", "S Compact", "W", "F"]  # AC-34
    assert CostingBusiness().route_stage_codes("B3 - C3 - V", data.stages) == ["C3", "V", "F"]
    assert CostingBusiness().route_stage_codes("B3 - C3.1 - C3.2 - V", data.stages) == ["C3", "V", "F"]
    everything = CostingBusiness().visible_stages(data, "TC", Technology.RING, {})
    assert len(everything) == len(data.stages)  # no route → every stage


def test_br14_br16_no_price_when_the_check_fails() -> None:
    setup_factory(FactoryCode.S4, with_loss_group=False)
    yarn = make_yarn(FactoryCode.S4, "S4-9", S4_NAME, S4_NSM, S4_COMPONENTS, "Type 3")
    result = CostingBusiness().calculate(yarn, load_factory_data(FactoryCode.S4))
    assert not result.passed and result.cost.total == 0
    assert result.reasons[0].startswith("Chưa có nhóm tiêu hao 'CORE (COTTON/ FDY 30D/24F/1) (70/30) MVS' ở xưởng S4.")


def test_br15_merge_stage_is_exempt_and_normal_stage_is_checked() -> None:
    setup_factory(FactoryCode.S4)
    data = load_factory_data(FactoryCode.S4)
    yarn = make_yarn(FactoryCode.S4, "S4-9", S4_NAME, {**S4_NSM, "R": D(90)}, S4_COMPONENTS, "Type 3")
    reasons = CostingBusiness().check_match(yarn, data)
    assert "Công đoạn R: có NSM nhưng nhóm tiêu hao không có tiêu hao." in reasons  # AC-09
    assert not any("MD2" in r for r in reasons)
    no_packaging = yarn.model_copy(update={"nsm": S4_NSM, "packaging_code": None})
    assert CostingBusiness().check_match(no_packaging, data) == ["Chưa có loại đóng gói."]


def test_br21_totals_are_summed_before_rounding() -> None:
    setup_factory(FactoryCode.S4)
    yarn = make_yarn(FactoryCode.S4, "S4-2017", S4_NAME, S4_NSM, S4_COMPONENTS, "Type 3")
    result = CostingBusiness().calculate(yarn, load_factory_data(FactoryCode.S4))
    rounded_sum = sum(DisplayBusiness().round_vnd(d.cost_per_kg) for d in result.details)
    assert rounded_sum == D(19778 - 1)  # the rounded stage costs add up to 19.777 ...
    assert DisplayBusiness().round_vnd(result.cost.total) == D(19778)  # ... the total is summed unrounded
    assert abs(result.cost.total - sum((d.cost_per_kg for d in result.details), D(0))) < D("1E-20")


@pytest.mark.parametrize(
    ("value", "method", "expected"),
    [
        (D("19777.8356"), "round_vnd", D(19778)),
        (D("0.79111"), "round_usd", D("0.7911")),
        (D("0.2596"), "round_percent", D("25.96")),
    ],
)
def test_br23_display_rounding(value: D, method: str, expected: D) -> None:
    assert getattr(DisplayBusiness(), method)(value) == expected


def test_br22_current_exchange_rate() -> None:
    old = ExchangeRate(effective_date=TODAY.replace(year=TODAY.year - 1), rate=D(25000))
    new = ExchangeRate(effective_date=TODAY, rate=D(26000))
    future = ExchangeRate(effective_date=TODAY.replace(year=TODAY.year + 1), rate=D(30000))
    current = CostingBusiness().current_exchange_rate([old, new, future], TODAY)
    assert current is new
    assert format_usd(D("19777.8356") / current.rate) == "0,7607"  # AC-29
