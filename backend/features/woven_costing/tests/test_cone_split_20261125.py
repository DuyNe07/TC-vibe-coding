"""Extension 2026-11-26: cone table 4.14a - Ngang yarns twisted together / apart (BR-100, AC-84..AC-88).

(This file first held an unconfirmed reading of the change, "2 Ngang counts -> cone 1 / cone 2", which is wrong for
EF27920021; it now tests the confirmed BR-100.)"""

from decimal import Decimal

from backend.features.woven_costing.business.cone_business import ConeBusiness
from backend.features.woven_costing.dto.costsheet_dto import (
    ConeLineDTO,
    CostsheetInputRequest,
    CostsheetResponse,
    TwistLineDTO,
    WeavingInputDTO,
)
from backend.features.woven_costing.models.costsheet_input import TwistLine, YarnLine
from backend.features.woven_costing.models.enums import YarnDirection
from backend.features.woven_costing.services.calculate_costsheet_service import CalculateCostsheetService
from backend.features.woven_costing.services.create_costsheet_service import CreateCostsheetService
from backend.features.woven_costing.tests.helpers import SALES_FS1, TODAY, as_user, create_request, seed_master

D = Decimal


def _se(count: str, kg: str, twist: int = 400, direction: str = "Ngang") -> TwistLine:
    return TwistLine(direction=direction, count=count, twist=twist, quantity_kg=D(kg))


def _weft_yarn(seq: int, raw: str, twist: str = "400T/M") -> YarnLine:
    return YarnLine(direction=YarnDirection.WEFT, seq=seq, yarn_name=raw, source_yarn_name=f"{raw} - {twist}",
                    twist_tpm=twist, is_twisted=True)  # fmt: skip


def _rows(lines: list) -> list[tuple[str, Decimal | None]]:
    return [(c.count, c.quantity_kg) for c in lines]


# ---- AC-84: carbon twisted together with its main yarn (EF27920021) -------------------------------------------------
def test_ac84_carbon_twisted_with_main_yarn_is_one_cone() -> None:
    yarns = [_weft_yarn(1, "BR1 30D/6F/1"), _weft_yarn(2, "DTY 150D/48F/1 HIM")]
    se = [_se("75D", "919", direction="Dọc"), _se("30D", "12.50"), _se("150D", "64.01")]
    lines, warnings = ConeBusiness().suggest_lines(se, yarns)
    assert _rows(lines) == [("150D + 30D", D("76.51"))]
    assert lines[0].members == "150D (400 T/M) + 30D (400 T/M)" and lines[0].suggested
    assert warnings == []


# ---- AC-85: main yarns twisted apart, one cone each; same count + twist gathered ------------------------------------
def test_ac85_main_yarns_one_cone_each() -> None:
    cones = ConeBusiness()
    three = [_se("75D", "21"), _se("150D", "30"), _se("300D", "10")]
    assert _rows(cones.suggest_lines(three, [])[0]) == [("75D", D(21)), ("150D", D(30)), ("300D", D(10))]
    yarns = [_weft_yarn(1, "EC 75D/48F/1"), _weft_yarn(2, "EY 75D/24F/1")]  # EF15690111: same count and twist
    gathered = [_se("75D", "21.18"), _se("75D", "21.52")]
    assert _rows(cones.suggest_lines(gathered, yarns)[0]) == [("75D", D("42.70"))]


# ---- AC-86: spandex joins its main yarn; ambiguous carbon -> check warning -----------------------------------------
def test_ac86_spandex_and_ambiguous_carbon() -> None:
    cones = ConeBusiness()
    yarns = [_weft_yarn(1, "TR 40/2 (65/35)", "800T/M"), _weft_yarn(2, "SPANDEX 40D", "800T/M")]
    lines, _ = cones.suggest_lines([_se("40/2", "46.29", 800), _se("40D", "3.48", 800)], yarns)
    assert _rows(lines) == [("40/2 + SP 40", D("49.77"))]
    yarns = [_weft_yarn(1, "DTY 150D/48F/1"), _weft_yarn(2, "DTY 75D/36F/1"), _weft_yarn(3, "WHITE CACBON 20D/3F/1")]
    se = [_se("150D", "60"), _se("75D", "15"), _se("20D + CB", "2")]
    lines, warnings = cones.suggest_lines(se, yarns)
    # "20D + CB" = 40: 15 x 40 / 75 = 8 is nearer 2 than 60 x 40 / 150 = 16
    assert _rows(lines) == [("150D", D(60)), ("75D + CB", D(17))]
    assert warnings == ["Kiểm tra lại cone: sợi 20D + CB có thể se chung với 75D hoặc 150D."]


def _request(sheet: CostsheetResponse, **changes: object) -> CostsheetInputRequest:
    return CostsheetInputRequest(costsheet_id=sheet.id, **(sheet.input.model_dump() | changes))


def _calc(sheet: CostsheetResponse, **changes: object) -> CostsheetResponse:
    with as_user(SALES_FS1):
        return CalculateCostsheetService(today=TODAY).handle(_request(sheet, **changes))


def _created() -> CostsheetResponse:
    seed_master()
    with as_user(SALES_FS1):
        return CreateCostsheetService(today=TODAY).handle(create_request())


# ---- AC-87: sales edits kept, deleted suggestions not made again, added line costed, empty count blocks -----------
def test_ac87_sales_edits_on_the_cone_table() -> None:
    se = [TwistLineDTO(direction="Ngang", count="150D", twist=400, quantity_kg=D(100)),
          TwistLineDTO(direction="Ngang", count="75D", twist=400, quantity_kg=D(20))]  # fmt: skip
    calc = _calc(_created(), twist_lines=se)
    assert _rows(calc.input.weaving.cone_lines) == [("150D", D(100)), ("75D", D(20))]
    first, _second = calc.input.weaving.cone_lines
    edited = calc.input.weaving.model_copy(update={"cone_lines": [first.model_copy(update={"quantity_kg": D(300)})]})
    more = [se[0].model_copy(update={"quantity_kg": D(120)}), se[1]]
    kept = _calc(calc, twist_lines=more, weaving=edited)
    assert _rows(kept.input.weaving.cone_lines) == [("150D", D(300))]  # 75D deleted by sales: not suggested again
    added = kept.input.weaving.model_copy(
        update={"cone_lines": [*kept.input.weaving.cone_lines, ConeLineDTO(count="300D", quantity_kg=D(5))]}
    )
    with_added = _calc(kept, twist_lines=more, weaving=added)
    assert any(s.stage == "Cone 2" and s.quantity == D(5) and s.norm > 0 for s in with_added.result.weaving_stages)
    no_count = with_added.input.weaving.model_copy(
        update={"cone_lines": [*with_added.input.weaving.cone_lines, ConeLineDTO(count="", quantity_kg=D(7))]}
    )
    blocked = _calc(with_added, twist_lines=more, weaving=no_count)
    assert any(
        w.blocking and w.message == "Cone dòng 3: có 7.00 kg sợi cone, vui lòng nhập chi số." for w in blocked.warnings
    )


# ---- AC-88: no Ngang Se -> no cone; costsheets stored before keep their cones -------------------------------------
def test_ac88_no_weft_se_and_stored_costsheets() -> None:
    created = _created()
    warp_only = [TwistLineDTO(direction="Dọc", count="75D", twist=400, quantity_kg=D(50))]
    calc = _calc(created, twist_lines=warp_only)
    assert calc.input.weaving.cone_lines == []
    assert not [s for s in calc.result.weaving_stages if s.stage.startswith("Cone")]
    stored = WeavingInputDTO(cone_count_1="150D", cone_qty_1=D(388))  # cells of a costsheet stored before 2026-11-26
    old = _calc(created, twist_lines=warp_only, weaving=stored)
    assert _rows(old.input.weaving.cone_lines) == [("150D", D(388))] and not old.input.weaving.cone_lines[0].suggested
    assert any(s.stage == "Cone 1" and s.quantity == D(388) and s.norm > 0 for s in old.result.weaving_stages)
    weft = [TwistLineDTO(direction="Ngang", count="75D", twist=400, quantity_kg=D(20))]
    still_old = _calc(created, twist_lines=weft, weaving=stored)  # typed cones: no suggestion added
    assert _rows(still_old.input.weaving.cone_lines) == [("150D", D(388))]
