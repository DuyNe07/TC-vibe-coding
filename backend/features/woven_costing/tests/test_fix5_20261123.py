"""Fix of 5 points (2026-11-23): norm tables in 4 groups (AC-58), TCDN extra stages = stages with a norm row (AC-59),
cone 1 suggestion (BR-87, AC-60), calculation without saving (UC-16, AC-61), live Se line suggestion (BR-86, AC-62)."""

from decimal import Decimal

from backend.core.base import EmptyRequest
from backend.features.woven_costing.business.hint_business import HintBusiness
from backend.features.woven_costing.dto.costsheet_dto import (
    CostsheetInputRequest,
    CostsheetResponse,
    GetCostsheetRequest,
    HcmDyeingInputDTO,
    TcdnDyeingInputDTO,
    TcdnStageInputDTO,
    TwistLineDTO,
)
from backend.features.woven_costing.dto.master_dto import ViewNormSetRequest
from backend.features.woven_costing.models.costsheet_input import TwistLine, WeavingInput
from backend.features.woven_costing.models.enums import DyePlant, FiberSystem, YarnDirection
from backend.features.woven_costing.models.fabric import Fabric, FabricSpecs, FabricYarn
from backend.features.woven_costing.models.norm_set import initial_tables
from backend.features.woven_costing.repositories.costsheet_repository import CostsheetRepository
from backend.features.woven_costing.repositories.fabric_repository import FabricRepository
from backend.features.woven_costing.services.calculate_costsheet_service import CalculateCostsheetService
from backend.features.woven_costing.services.create_costsheet_service import CreateCostsheetService
from backend.features.woven_costing.services.get_costsheet_options_service import GetCostsheetOptionsService
from backend.features.woven_costing.services.get_costsheet_service import GetCostsheetService
from backend.features.woven_costing.services.save_draft_service import SaveDraftService
from backend.features.woven_costing.services.view_norm_set_service import ViewNormSetService
from backend.features.woven_costing.tests.helpers import (
    SALES_FS1,
    TODAY,
    as_user,
    create_request,
    full_input,
    seed_master,
)

D = Decimal
MISSING_NORM = "không có trong bảng tra"


def _request(sheet: CostsheetResponse, **changes: object) -> CostsheetInputRequest:
    data = sheet.input.model_dump() | changes
    return CostsheetInputRequest(costsheet_id=sheet.id, **data)


def _calc(sheet: CostsheetResponse, **changes: object) -> CostsheetResponse:
    with as_user(SALES_FS1):
        return CalculateCostsheetService(today=TODAY).handle(_request(sheet, **changes))


# ---- AC-58: Screen 5 norm tables in 4 sub-tabs ------------------------------------------------------------------------
def test_ac58_norm_tables_grouped_in_four_tabs() -> None:
    view = ViewNormSetService(today=TODAY).handle(ViewNormSetRequest())
    tables = [*view.selected.tables, *view.selected.optional_tables]
    groups: dict[str, list[str]] = {}
    for table in tables:
        groups.setdefault(table.group, []).append(table.title)
    assert list(groups) == ["Dệt", "Nhuộm HCM", "Nhuộm TCDN", "Danh mục chọn"]
    assert groups["Dệt"] == [
        "Đơn giá theo phút", "Tham số Se", "Tham số Mắc / Kiểm", "Định mức Hồ", "Định mức Dệt", "Chi số",
        "Spandex cộng thêm",
    ]  # fmt: skip
    assert len(groups["Nhuộm HCM"]) == 3 and len(groups["Nhuộm TCDN"]) == 2
    assert groups["Danh mục chọn"] == ["Danh mục chọn"]


# ---- AC-59: TCDN extra stages -----------------------------------------------------------------------------------------
def test_ac59_tcdn_stages_are_the_stages_with_a_norm_row() -> None:
    options = GetCostsheetOptionsService(today=TODAY).handle(EmptyRequest())
    expected = list(
        dict.fromkeys(p.code for p in initial_tables().tcdn_processes if not p.code.startswith("Nhuộm tiêu chuẩn"))
    )
    assert options.tcdn_stages == expected
    assert len(options.tcdn_stages) == 28  # distinct stage codes of 4.5.10 in the initial norm set
    for name in ("Suse 2", "Ageing room 2", "Setting", "Soaping", "CPB", "WR", "Xếp vải"):
        assert name in options.tcdn_stages
    for name in ("Suse 1", "Ageing room", "Kuster", "Dyeing", "Dry", "Mở khổ", "Suse 3", "Nhuộm Khăn", "Coating 1",
                 "Xếp Vải"):  # fmt: skip
        assert name not in options.tcdn_stages


def test_ac59_every_tcdn_stage_calculates_without_missing_norm() -> None:
    seed_master()
    with as_user(SALES_FS1):
        created = CreateCostsheetService(today=TODAY).handle(create_request(dye_plant=DyePlant.TCDN))
    stages = GetCostsheetOptionsService(today=TODAY).handle(EmptyRequest()).tcdn_stages
    for start in range(0, len(stages), 13):
        chunk = [TcdnStageInputDTO(name=n, chemical_price=D(100)) for n in stages[start : start + 13]]
        tcdn = TcdnDyeingInputDTO(dye_material="Poly", color_level="Light", extra_stages=chunk)
        calc = _calc(created, tcdn_dyeing=tcdn)
        assert not [w.message for w in calc.warnings if MISSING_NORM in w.message]
        names = {line.name for line in calc.result.dyeing_lines}
        assert {s.name for s in chunk} <= names


# ---- AC-60: BR-87 cone 1 suggestion ----------------------------------------------------------------------------------
def test_br87_cone_suggestion_rules() -> None:
    hints = HintBusiness()
    weft = [TwistLine(direction="Ngang", count="150D", twist=400, quantity_kg=D(388))]
    filled = hints.suggest_cone(WeavingInput(), weft)
    assert (filled.cone_qty_1, filled.cone_count_1) == (D(388), "150D")
    assert filled.cone_qty_1_suggested and filled.cone_count_1_suggested
    two = [*weft, TwistLine(direction="Ngang", count="75D", twist=400, quantity_kg=D(12))]
    both = hints.suggest_cone(filled, two)
    assert (both.cone_qty_1, both.cone_count_1) == (D(400), "")
    typed = hints.suggest_cone(WeavingInput(cone_count_1="100D", cone_qty_1=D(300)), weft)
    assert (typed.cone_qty_1, typed.cone_count_1) == (D(300), "100D")
    # stored rows: typed values kept; an empty quantity is the Se total (as before) and is now shown
    old = WeavingInput.model_validate({"cone_count_1": "150D", "cone_qty_1": "930"})
    assert not old.cone_qty_1_suggested and hints.suggest_cone(old, weft).cone_qty_1 == D(930)
    old_empty = WeavingInput.model_validate({"cone_count_1": "150D"})
    assert hints.suggest_cone(old_empty, weft).cone_qty_1 == D(388)
    assert hints.suggest_cone(filled, []).cone_qty_1 is None


def test_ac60_cone_prefilled_and_kept_when_sales_edits() -> None:
    seed_master()
    with as_user(SALES_FS1):
        created = CreateCostsheetService(today=TODAY).handle(create_request())
    line = TwistLineDTO(direction="Ngang", count="150D", twist=400, quantity_kg=D(388))
    calc = _calc(created, twist_lines=[line])
    weave = calc.input.weaving
    assert (weave.cone_qty_1, weave.cone_count_1) == (D(388), "150D")
    assert weave.cone_qty_1_suggested and weave.cone_count_1_suggested
    assert any(s.stage == "Cone 1" and s.quantity == D(388) and s.norm > 0 for s in calc.result.weaving_stages)
    assert not [w for w in calc.warnings if "sợi cone" in w.message]
    more = line.model_copy(update={"quantity_kg": D(500)})
    follows = _calc(calc, twist_lines=[more])
    assert follows.input.weaving.cone_qty_1 == D(500)
    edited = calc.input.weaving.model_copy(update={"cone_qty_1": D(300), "cone_qty_1_suggested": False})
    kept = _calc(calc, twist_lines=[more], weaving=edited)
    assert kept.input.weaving.cone_qty_1 == D(300) and kept.input.weaving.cone_count_1 == "150D"
    several = [more, TwistLineDTO(direction="Ngang", count="75D", twist=400, quantity_kg=D(10))]
    mixed = _calc(calc, twist_lines=several)
    assert mixed.input.weaving.cone_count_1 == "" and mixed.input.weaving.cone_qty_1 == D(510)
    assert any("SL gợi ý 510.00 kg" in w.message for w in mixed.warnings)


# ---- AC-61: UC-16 calculates without saving ---------------------------------------------------------------------------
def test_ac61_calculation_is_not_saved_until_save_draft() -> None:
    seed_master()
    with as_user(SALES_FS1):
        created = CreateCostsheetService(today=TODAY).handle(create_request())
        saved = SaveDraftService(today=TODAY).handle(full_input(created))
        other = HcmDyeingInputDTO(dye_material="TC/CVC/TR thường", color_level="Nhạt", dye_loss_rate=D("0.024"))
        request = full_input(saved, hcm_dyeing=other)
        calc = CalculateCostsheetService(today=TODAY).handle(request)
        reopened = GetCostsheetService().handle(GetCostsheetRequest(costsheet_id=saved.id))
    assert calc.saved is False and calc.result.dyeing_total != saved.result.dyeing_total
    assert calc.result.gp_pct != saved.result.gp_pct
    assert reopened.result.dyeing_total == saved.result.dyeing_total
    assert reopened.input.hcm_dyeing.color_level == "Đậm"
    with as_user(SALES_FS1):
        SaveDraftService(today=TODAY).handle(request)
        after = GetCostsheetService().handle(GetCostsheetRequest(costsheet_id=saved.id))
    assert after.result.dyeing_total == calc.result.dyeing_total and after.input.hcm_dyeing.color_level == "Nhạt"


# ---- AC-62: BR-86 live Se line suggestion -----------------------------------------------------------------------------
def _ef_fabric() -> Fabric:
    yarns = [
        FabricYarn(direction=YarnDirection.WARP, seq=1, yarn_name="TC 45/1", raw_yarn_name="TC 45/1", rate=D(60),
                   raw_rate=D(100)),
        FabricYarn(direction=YarnDirection.WARP, seq=2, yarn_name="WHITE CACBON 20D/3F/1 400T/M",
                   raw_yarn_name="WHITE CACBON 20D/3F/1", rate=D(1), raw_rate=D(100), twist_tpm="400T/M"),
        FabricYarn(direction=YarnDirection.WARP, seq=3, yarn_name="DTY 75D/72F/1 SIM FD 400T/M",
                   raw_yarn_name="DTY 75D/72F/1 SIM FD", rate=D(4), raw_rate=D(100), twist_tpm="400T/M"),
        FabricYarn(direction=YarnDirection.WEFT, seq=1, yarn_name="DTY 150D/48F/1", raw_yarn_name="DTY 150D/48F/1",
                   rate=D(35), raw_rate=D(100)),
    ]  # fmt: skip
    specs = FabricSpecs(
        greige_width_cm=D(175), greige_weft_density=D(252), greige_warp_density=D(431), greige_g_per_m=D(217),
        greige_gsm=D(124), finished_width_cm=D(154), finished_weft_density=D(280), finished_warp_density=D(470),
        finished_g_per_m=D(230), finished_gsm=D(150),
    )  # fmt: skip
    return Fabric(tcfno="EF35320026", fabric_name="TC + CARBON", specs=specs, yarns=yarns)


def _estimated_matches(calc: CostsheetResponse) -> bool:
    total = sum((t.quantity_kg or D(0) for t in calc.input.twist_lines), D(0))
    return abs(total - calc.result.twist_estimated_kg) < D("0.000001")


def test_ac62_suggested_se_lines_follow_the_ticks_and_meters() -> None:
    seed_master()
    FabricRepository().add(_ef_fabric())
    with as_user(SALES_FS1):
        created = CreateCostsheetService(today=TODAY).handle(create_request(tcfno="EF35320026"))
    assert created.input.twist_lines_live and [t.count for t in created.input.twist_lines] == ["20D + CB", "75D"]
    assert all(t.suggested and t.suggestion_key for t in created.input.twist_lines)
    # untick Se on the carbon warp yarn -> its suggested line goes, the other follows
    yarns = [
        y.model_copy(update={"is_twisted": False}) if y.seq == 2 and y.direction == YarnDirection.WARP else y
        for y in created.input.yarn_lines
    ]
    unticked = _calc(created, yarn_lines=yarns)
    assert [t.count for t in unticked.input.twist_lines] == ["75D"] and _estimated_matches(unticked)
    assert not [w for w in unticked.warnings if w.code == "BR-21"]
    # more meters -> suggested quantities follow
    more = _calc(created, order_meters=D(20000))
    assert _estimated_matches(more)
    assert more.input.twist_lines[1].quantity_kg > created.input.twist_lines[1].quantity_kg
    # sales edits the 75D quantity -> kept, not suggested again; the 20D line still follows
    lines = list(more.input.twist_lines)
    lines[1] = lines[1].model_copy(update={"quantity_kg": D(7)})
    edited = _calc(more, twist_lines=lines, order_meters=D(30000))
    counts = [(t.count, t.suggested) for t in edited.input.twist_lines]
    assert counts == [("20D + CB", True), ("75D", False)]
    assert edited.input.twist_lines[1].quantity_kg == D(7)
    assert edited.input.twist_lines[0].quantity_kg > more.input.twist_lines[0].quantity_kg
    # sales deletes the 20D line -> not made again
    deleted = _calc(edited, twist_lines=[edited.input.twist_lines[1]], order_meters=D(30000))
    again = _calc(deleted, order_meters=D(40000))
    assert [t.count for t in again.input.twist_lines] == ["75D"]
    assert again.input.twist_lines[0].quantity_kg == D(7)
    # a sales-added line stays
    added = [*again.input.twist_lines, TwistLineDTO(direction="Ngang", count="150D", twist=300, quantity_kg=D(5))]
    with_added = _calc(again, twist_lines=added)
    assert [(t.direction, t.count) for t in with_added.input.twist_lines] == [("Dọc", "75D"), ("Ngang", "150D")]


def test_ac62_se_lines_stored_before_stay_unchanged() -> None:
    """CS-ICHI-2026-00001 style: Se lines stored before 2026-11-23 (no new fields) are sales lines, kept as is."""
    seed_master()
    FabricRepository().add(_ef_fabric())
    with as_user(SALES_FS1):
        created = CreateCostsheetService(today=TODAY).handle(create_request(tcfno="EF35320026"))
    repository = CostsheetRepository()
    stored = repository.get(created.id)
    old_line = TwistLine.model_validate(
        {"direction": "Dọc", "fiber_system": "Filament", "count": "75D + CB", "twist": 400, "quantity_kg": "14"}
    )
    old = stored.model_copy(
        update={"twist_lines": [old_line], "twist_lines_suggested": True, "twist_lines_live": False,
                "twist_suggestions": [], "twist_suggestion_skips": []}
    )  # fmt: skip
    repository.update(old)
    with as_user(SALES_FS1):
        opened = GetCostsheetService().handle(GetCostsheetRequest(costsheet_id=created.id))
        calc = CalculateCostsheetService(today=TODAY).handle(_request(opened, order_meters=D(25000)))
    lines = calc.input.twist_lines
    assert len(lines) == 1 and not lines[0].suggested and not calc.input.twist_lines_live
    assert (lines[0].count, lines[0].twist, lines[0].quantity_kg, lines[0].fiber_system) == (
        "75D + CB", 400, D(14), FiberSystem.FILAMENT,
    )  # fmt: skip
