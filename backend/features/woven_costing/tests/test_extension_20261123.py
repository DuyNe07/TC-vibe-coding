"""Extension 2026-11-23: free-text count / twist (BR-81..BR-84, BR-86), spandex sheet (4.5.13, BR-63), SO full rights
(BR-31, BR-51..BR-53, BR-85) and the quantity factor display (AC-56). AC-44..AC-57."""

from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest
from openpyxl import load_workbook

from backend.core.base import EmptyRequest, UploadedFileDTO
from backend.core.exceptions import AppError, BusinessRuleViolation
from backend.features.woven_costing.business.count_business import CountBusiness
from backend.features.woven_costing.business.norm_lookup_business import NormLookupBusiness
from backend.features.woven_costing.business.twist_business import TwistBusiness
from backend.features.woven_costing.dto.costsheet_dto import (
    CostsheetActionRequest,
    CostsheetInputRequest,
    CostsheetResponse,
    GetCostsheetRequest,
    TwistLineDTO,
    WeavingInputDTO,
)
from backend.features.woven_costing.dto.list_dto import ListCostsheetsRequest
from backend.features.woven_costing.dto.master_dto import SaveNormSetRequest, ViewNormSetRequest
from backend.features.woven_costing.exceptions import CostsheetValidationError
from backend.features.woven_costing.models.costsheet import Costsheet
from backend.features.woven_costing.models.costsheet_input import TwistLine
from backend.features.woven_costing.models.enums import (
    CostsheetAction,
    CostsheetStatus,
    FiberSystem,
    OrderType,
    YarnDirection,
)
from backend.features.woven_costing.models.fabric import Fabric, FabricSpecs, FabricYarn
from backend.features.woven_costing.models.norm_set import NormTables, SpandexAddition, YarnCount, initial_tables
from backend.features.woven_costing.models.seed_norms import SEED_YARN_COUNTS
from backend.features.woven_costing.repositories.fabric_repository import FabricRepository
from backend.features.woven_costing.repositories.norm_repository import NormSetRepository
from backend.features.woven_costing.services.approve_costsheet_service import ApproveCostsheetService
from backend.features.woven_costing.services.calculate_costsheet_service import CalculateCostsheetService
from backend.features.woven_costing.services.create_costsheet_service import CreateCostsheetService
from backend.features.woven_costing.services.download_norm_template_service import DownloadNormTemplateService
from backend.features.woven_costing.services.get_costsheet_service import GetCostsheetService
from backend.features.woven_costing.services.list_costsheets_service import ListCostsheetsService
from backend.features.woven_costing.services.preview_norm_set_service import PreviewNormSetService
from backend.features.woven_costing.services.save_draft_service import SaveDraftService
from backend.features.woven_costing.services.save_norm_set_service import SaveNormSetService
from backend.features.woven_costing.services.submit_costsheet_service import SubmitCostsheetService
from backend.features.woven_costing.services.view_norm_set_service import ViewNormSetService
from backend.features.woven_costing.tests.helpers import (
    HEAD,
    LEAD_FS1,
    SALES_FS1,
    SALES_FS2,
    SO,
    TODAY,
    as_user,
    create_request,
    full_input,
    seed_master,
    user,
)

D = Decimal
BR81 = 'Chi số "{}" không đúng dạng. Ví dụ đúng: 75D/2 + CB, 30/2, 45 + 75D + SP 70.'
# "34/2 + CB" is 332.706 by the formula; the Excel list keeps it rounded to 333 (the list value wins, BR-81)
ROUNDED_IN_EXCEL = {"34/2 + CB": D("0.3")}


# ---- BR-81 / BR-83 / BR-84 / BR-82 (business) --------------------------------------------------------------------
def test_ac44_formula_matches_every_listed_count() -> None:
    """AC-44: the formula gives the converted count of every count of sheet "Dữ liệu" (and BR-83 its fiber system)."""
    counts = CountBusiness(initial_tables())
    for fiber, count, converted in SEED_YARN_COUNTS:
        value = counts.formula(count).value
        assert value is not None, count
        assert abs(value - D(converted)) <= ROUNDED_IN_EXCEL.get(count, D("0.05")), count
        assert counts.suggest_fiber(count) == FiberSystem(fiber), count
    examples = {"75D/2 + CB": D(170), "20/2": D("531.6"), "30 + 150D + 300D": D("627.2"), "60/2 + SP 40": D("193.2")}
    for count, value in examples.items():
        assert counts.formula(count).value == value
    assert round(counts.formula("45 + 75D + SP 70").value, 2) == D("215.13")


def test_ac46_ac48_ac49_conversion_errors_and_list_priority() -> None:
    """AC-46 (BR-81 format), AC-48 (BR-84 spandex), AC-49 (list value wins over the formula)."""
    counts = CountBusiness(initial_tables())
    bad = counts.convert("75 DD")
    assert not bad.ok and bad.error_code == "BR-81" and bad.error == BR81.format("75 DD")
    missing = counts.convert("75D + SP 20")
    assert missing.error_code == "BR-84"
    assert missing.error == "Chưa có số cộng thêm cho spandex SP 20. Liên hệ SO bổ sung."
    with_sp20 = initial_tables().model_copy(update={"spandex": [SpandexAddition(spandex=D(20), addition=D(10))]})
    assert CountBusiness(with_sp20).convert("75D + SP 20").value == D(85)
    listed = initial_tables().model_copy(update={"yarn_counts": [YarnCount(fiber_system="Filament", count="75D",
                                                                           converted=D(80))]})  # fmt: skip
    assert CountBusiness(listed).convert(" 75d ").value == D(80)
    assert CountBusiness(listed).formula("75D").value == D(75)
    assert counts.convert("75d/2+cb").value == D(170)  # spaces / case do not matter


def test_ac47_twist_range() -> None:
    """AC-47 (BR-82): integer 50..3000."""
    counts = CountBusiness()
    assert counts.twist_violation(30).message == "Độ săn 30 không hợp lệ: phải là số nguyên từ 50 đến 3.000 T/M."
    assert counts.twist_violation(50) is None and counts.twist_violation(3000) is None
    assert counts.twist_violation(3001).rule_code == "BR-82"


def test_ac45_twist_norm_uses_formula_and_chosen_fiber() -> None:
    """AC-45 (BR-81, BR-83, BR-20): "50D/2 + CB" -> 120, Filament suggested, norm with singeing; Spun on request."""
    tables = initial_tables()
    lookup = NormLookupBusiness(tables)
    assert lookup.twist_converted("50D/2 + CB") == D(120)
    assert CountBusiness().suggest_fiber("50D/2 + CB") == FiberSystem.FILAMENT
    assert CountBusiness().suggest_fiber("30/2 + SP 70") == FiberSystem.SPUN
    twist = TwistBusiness()
    auto = twist.twist_norm(TwistLine(count="50D/2 + CB", twist=900), lookup)
    filament = twist.twist_norm(TwistLine(fiber_system=FiberSystem.FILAMENT, count="50D/2 + CB", twist=900), lookup)
    spun = twist.twist_norm(TwistLine(fiber_system=FiberSystem.SPUN, count="50D/2 + CB", twist=900), lookup)
    assert auto is not None and filament is not None and spun is not None
    assert auto.total == filament.total and spun.total != filament.total
    without_cb = twist.twist_norm(TwistLine(count="50D/2", twist=900), lookup)
    assert filament.total > without_cb.total  # bấm đốt added for the carbon part


def test_ac51_listed_counts_keep_their_norm() -> None:
    """AC-51: a listed count gives the same converted count as before (number of the list, e.g. Cone "150D")."""
    lookup = NormLookupBusiness(initial_tables())
    for _fiber, count, converted in SEED_YARN_COUNTS:
        assert lookup.twist_converted(count) == D(converted)


def test_br86_count_read_from_yarn_names() -> None:
    """BR-86: count read from the yarn name (assumption: spun "N/1" -> "N"; carbon -> "+ CB")."""
    counts = CountBusiness()
    assert counts.count_from_yarn_name("WHITE CACBON 20D/3F/1") == "20D + CB"
    assert counts.count_from_yarn_name("DTY 75D/72F/1 SIM FD") == "75D"
    assert counts.count_from_yarn_name("TC 45/2 (65/35)") == "45/2"
    assert counts.count_from_yarn_name("DTY75D/36F/1HIM") == "75D"
    assert counts.count_from_yarn_name("POLY 150D/48F/2 C.TRANG") == "150D/2 + CB"
    assert counts.count_from_yarn_name("TC 34/1 (65/35)") == "34"
    assert counts.count_from_yarn_name("COTTON 100%") == ""
    assert counts.twist_from_text("400T/M") == 400 and counts.twist_from_text("") is None


def test_stored_data_stays_readable() -> None:
    """Stored rows without the new fields load with the defaults (twist line, costsheet, norm set)."""
    old_line = {"direction": "Dọc", "fiber_system": "Filament", "count": "75D + CB", "twist": 400, "quantity_kg": "14"}
    line = TwistLine.model_validate(old_line)
    assert line.fiber_suggested is False and line.fiber_system == FiberSystem.FILAMENT
    sheet = Costsheet.model_validate({"costsheet_no": "CS-ICHI-2026-00001", "costing_date": "2026-11-20",
                                      "tcfno": "X", "fabric_snapshot": {"tcfno": "X"}, "twist_lines": [old_line]})  # fmt: skip
    assert sheet.twist_lines_suggested is False and sheet.twist_lines[0].count == "75D + CB"
    tables = NormTables.model_validate({"minute_rates": []})
    assert [(s.spandex, s.addition) for s in tables.spandex] == [(D(40), D(16)), (D(70), D(22))]


# ---- services: Se lines (BR-81..BR-86) ------------------------------------------------------------------------------
def _request(sheet: CostsheetResponse, **changes: object) -> CostsheetInputRequest:
    data = sheet.input.model_dump() | changes
    return CostsheetInputRequest(costsheet_id=sheet.id, **data)


def test_ac45_ac46_ac47_on_the_costsheet() -> None:
    """AC-45: fiber suggested and kept; AC-46 / AC-47 block the submit with the exact messages."""
    seed_master()
    with as_user(SALES_FS1):
        created = CreateCostsheetService(today=TODAY).handle(create_request())
        line = TwistLineDTO(direction="Dọc", count="50D/2 + CB", twist=900, quantity_kg=D(1))
        calc = CalculateCostsheetService(today=TODAY).handle(_request(created, twist_lines=[line]))
        spun = line.model_copy(update={"fiber_system": FiberSystem.SPUN})
        chosen = CalculateCostsheetService(today=TODAY).handle(_request(created, twist_lines=[spun]))
    first = calc.input.twist_lines[0]
    assert first.fiber_system == FiberSystem.FILAMENT and first.fiber_suggested
    assert calc.result.twist_lines[0].norm > 0 and not calc.result.twist_lines[0].error
    assert not [w for w in calc.warnings if w.code in ("BR-20", "BR-81", "BR-82", "BR-84")]
    assert (
        chosen.input.twist_lines[0].fiber_system == FiberSystem.SPUN and not chosen.input.twist_lines[0].fiber_suggested
    )
    lookup = NormLookupBusiness(initial_tables())
    expected = TwistBusiness().twist_norm(
        TwistLine(fiber_system=FiberSystem.SPUN, count="50D/2 + CB", twist=900), lookup
    )
    assert chosen.result.twist_lines[0].norm == expected.total
    draft = _draft_with(created, SALES_FS1)
    bad = [
        TwistLineDTO(direction="Dọc", count="75 DD", twist=400, quantity_kg=D(1)),
        TwistLineDTO(direction="Ngang", count="150D", twist=30, quantity_kg=D(1)),
    ]
    with as_user(SALES_FS1), pytest.raises(CostsheetValidationError) as error:
        SubmitCostsheetService(today=TODAY).handle(
            CostsheetActionRequest(costsheet_id=draft.id, input=full_input(draft, twist_lines=bad))
        )
    assert BR81.format("75 DD") in error.value.details
    assert "Độ săn 30 không hợp lệ: phải là số nguyên từ 50 đến 3.000 T/M." in error.value.details


def test_ac48_cone_count_with_unknown_spandex() -> None:
    """AC-48 / BR-22: a cone count is converted by BR-81 too; an unknown spandex is a blocking BR-84 warning."""
    seed_master()
    with as_user(SALES_FS1):
        created = CreateCostsheetService(today=TODAY).handle(create_request())
        weave = WeavingInputDTO(cone_count_1="75D + SP 20", cone_qty_1=D(5), cone_count_2="150D", cone_qty_2=D(5))
        calc = CalculateCostsheetService(today=TODAY).handle(_request(created, weaving=weave))
    messages = [w.message for w in calc.warnings if w.blocking]
    assert "Chưa có số cộng thêm cho spandex SP 20. Liên hệ SO bổ sung." in messages
    assert any(s.stage == "Cone 2" and s.norm > 0 for s in calc.result.weaving_stages)


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


def test_ac57_se_lines_suggested_once() -> None:
    """AC-57 (BR-86): Se lines suggested on the first calculation from the yarns ticked Se, never again."""
    seed_master()
    FabricRepository().add(_ef_fabric())
    with as_user(SALES_FS1):
        created = CreateCostsheetService(today=TODAY).handle(create_request(tcfno="EF35320026"))
    lines = created.input.twist_lines
    assert created.input.twist_lines_suggested
    assert [(t.direction, t.count, t.twist, t.fiber_system) for t in lines] == [
        ("Dọc", "20D + CB", 400, FiberSystem.FILAMENT),
        ("Dọc", "75D", 400, FiberSystem.FILAMENT),
    ]
    assert abs(sum(t.quantity_kg for t in lines) - created.result.twist_estimated_kg) < D("0.000001")
    assert all(t.quantity_kg > 0 for t in lines)
    assert not [w for w in created.warnings if w.code in ("BR-20", "BR-21", "BR-81")]
    with as_user(SALES_FS1):
        one_left = CalculateCostsheetService(today=TODAY).handle(_request(created, twist_lines=[lines[1]]))
        none_left = CalculateCostsheetService(today=TODAY).handle(_request(created, twist_lines=[]))
    assert [t.count for t in one_left.input.twist_lines] == ["75D"]
    assert none_left.input.twist_lines == []


def test_br83_suggested_fiber_follows_the_count() -> None:
    """BR-83: a suggested fiber system follows a new count; one chosen by sales is kept."""
    seed_master()
    with as_user(SALES_FS1):
        created = CreateCostsheetService(today=TODAY).handle(create_request())
        suggested = created.input.twist_lines[0]
        assert suggested.fiber_system == FiberSystem.FILAMENT and suggested.fiber_suggested
        moved = suggested.model_copy(update={"count": "30/2"})
        calc = CalculateCostsheetService(today=TODAY).handle(_request(created, twist_lines=[moved]))
        kept = moved.model_copy(update={"fiber_suggested": False})
        calc_kept = CalculateCostsheetService(today=TODAY).handle(_request(created, twist_lines=[kept]))
    assert calc.input.twist_lines[0].fiber_system == FiberSystem.SPUN
    assert calc_kept.input.twist_lines[0].fiber_system == FiberSystem.FILAMENT


# ---- 4.5.13 spandex sheet (UC-06, UC-07, UC-08, UC-37, BR-63) -------------------------------------------------------
def _without_sheet(content: bytes, remove: str) -> bytes:
    book = load_workbook(BytesIO(content))
    del book[remove]
    out = BytesIO()
    book.save(out)
    return out.getvalue()


def _spandex_rows(content: bytes, rows: list[list[object]]) -> bytes:
    book = load_workbook(BytesIO(content))
    sheet = book["Spandex"]
    for row in rows:
        sheet.append(row)
    out = BytesIO()
    book.save(out)
    return out.getvalue()


def test_ac50_norm_file_spandex_sheet() -> None:
    """AC-50: 12-sheet file accepted (spandex kept); duplicate spandex rejected; SP 20 = 10 -> "75D + SP 20" = 85."""
    template = DownloadNormTemplateService(today=TODAY).handle(EmptyRequest())
    assert "Spandex" in load_workbook(BytesIO(template.content)).sheetnames
    old_file = UploadedFileDTO(filename="dm12.xlsx", content=_without_sheet(template.content, "Spandex"))
    duplicate = UploadedFileDTO(filename="dup.xlsx", content=_spandex_rows(template.content, [[40, 18]]))
    with_sp20 = UploadedFileDTO(filename="sp20.xlsx", content=_spandex_rows(template.content, [[20, 10]]))
    with as_user(SO):
        preview = PreviewNormSetService().handle(SaveNormSetRequest(file=old_file, effective_from=date(2027, 1, 1)))
        assert preview.errors == [] and preview.optional_sheet_counts == []
        SaveNormSetService().handle(SaveNormSetRequest(file=old_file, effective_from=date(2027, 1, 1)))
        with pytest.raises(AppError) as error:
            SaveNormSetService().handle(SaveNormSetRequest(file=duplicate, effective_from=date(2027, 2, 1)))
        SaveNormSetService().handle(SaveNormSetRequest(file=with_sp20, effective_from=date(2027, 3, 1)))
    repo = NormSetRepository()
    kept = repo.by_code("DM-20270101-01").tables.spandex
    assert [(s.spandex, s.addition) for s in kept] == [(D(40), D(16)), (D(70), D(22))]
    assert "Sheet Spandex dòng 4: khóa 40 bị trùng." in error.value.details
    tables = repo.by_code("DM-20270301-01").tables
    assert CountBusiness(tables).convert("75D + SP 20").value == D(85)
    view = ViewNormSetService(today=TODAY).handle(ViewNormSetRequest(norm_set_code="DM-20270301-01"))
    assert [t.title for t in view.selected.optional_tables] == ["Spandex cộng thêm"]
    assert len(view.selected.optional_tables[0].rows) == 3


# ---- SO full rights (BR-31, BR-51..BR-53, BR-85) --------------------------------------------------------------------
def _draft_with(created: CostsheetResponse, who: object) -> CostsheetResponse:
    with as_user(who):
        return SaveDraftService(today=TODAY).handle(full_input(created))


def _sheet_of(who: object) -> CostsheetResponse:
    with as_user(who):
        created = CreateCostsheetService(today=TODAY).handle(create_request())
    return _draft_with(created, who)


def test_ac52_so_creates_sends_and_approves_own_costsheet() -> None:
    """AC-52: only SO -> team "SO"; the same person sends and approves."""
    seed_master()
    draft = _sheet_of(SO)
    assert draft.team == "SO"
    with as_user(SO):
        sent = SubmitCostsheetService(today=TODAY).handle(CostsheetActionRequest(costsheet_id=draft.id))
        assert "Người duyệt: Phòng SO hoặc trưởng đơn vị." in sent.message
        assert CostsheetAction.APPROVE in sent.allowed_actions
        approved = ApproveCostsheetService().handle(CostsheetActionRequest(costsheet_id=sent.id))
    assert approved.status == CostsheetStatus.DA_DUYET
    both = user("so2", "SO", "SALES", "FS1")
    with as_user(both):
        assert CreateCostsheetService(today=TODAY).handle(create_request()).team == "FS1"


def test_ac53_so_works_on_sales_costsheets() -> None:
    """AC-53: SO edits, sends, cancels a sales draft and approves / returns a pending one."""
    seed_master()
    draft = _sheet_of(SALES_FS1)
    with as_user(SO):
        opened = GetCostsheetService().handle(GetCostsheetRequest(costsheet_id=draft.id))
        assert opened.editable
        assert {CostsheetAction.SAVE_DRAFT, CostsheetAction.SUBMIT, CostsheetAction.CANCEL} <= set(
            opened.allowed_actions
        )
        saved = SaveDraftService(today=TODAY).handle(full_input(opened, note="SO sửa"))
    assert saved.input.note == "SO sửa" and saved.sales_username == "sales1"
    with as_user(SALES_FS1):
        sent = SubmitCostsheetService(today=TODAY).handle(CostsheetActionRequest(costsheet_id=draft.id))
    with as_user(SO):
        pending = GetCostsheetService().handle(GetCostsheetRequest(costsheet_id=sent.id))
        assert {CostsheetAction.APPROVE, CostsheetAction.RETURN} <= set(pending.allowed_actions)
        approved = ApproveCostsheetService().handle(CostsheetActionRequest(costsheet_id=sent.id))
    assert approved.status == CostsheetStatus.DA_DUYET


def test_ac54_ac55_team_so_hidden_from_sales_and_regressions() -> None:
    """AC-54: team "SO" not seen by sales / team leads, seen by Trưởng đơn vị. AC-55: old rights unchanged."""
    seed_master()
    so_sheet = _sheet_of(SO)
    fs2_sheet = _sheet_of(SALES_FS2)
    for who in (SALES_FS1, SALES_FS2, LEAD_FS1):
        with as_user(who), pytest.raises(BusinessRuleViolation) as hidden:
            GetCostsheetService().handle(GetCostsheetRequest(costsheet_id=so_sheet.id))
        assert hidden.value.message == "Bạn không có quyền xem costsheet này."
        with as_user(who):
            rows = ListCostsheetsService().handle(ListCostsheetsRequest())
        assert so_sheet.costsheet_no not in {r.costsheet_no for r in rows.rows}
    with as_user(HEAD):
        assert GetCostsheetService().handle(GetCostsheetRequest(costsheet_id=so_sheet.id)).team == "SO"
        listed = ListCostsheetsService().handle(ListCostsheetsRequest(team="SO"))
    assert [r.costsheet_no for r in listed.rows] == [so_sheet.costsheet_no]
    with as_user(SALES_FS1), pytest.raises(BusinessRuleViolation):
        GetCostsheetService().handle(GetCostsheetRequest(costsheet_id=fs2_sheet.id))
    fs1 = _sheet_of(SALES_FS1)
    with as_user(SALES_FS1):
        sent = SubmitCostsheetService(today=TODAY).handle(CostsheetActionRequest(costsheet_id=fs1.id))
        assert CostsheetAction.APPROVE not in sent.allowed_actions
    with as_user(LEAD_FS1):
        assert ApproveCostsheetService().handle(CostsheetActionRequest(costsheet_id=sent.id)).status == (
            CostsheetStatus.DA_DUYET
        )


# ---- AC-56 quantity factor display ----------------------------------------------------------------------------------
def test_ac56_quantity_factor_shown_per_stage() -> None:
    """AC-56 (BR-23): trial order -> factor 2 with reason; flagged stages x 2; their sum = weaving total."""
    seed_master()
    with as_user(SALES_FS1):
        trial = CreateCostsheetService(today=TODAY).handle(create_request(order_type=OrderType.TRIAL))
        production = CreateCostsheetService(today=TODAY).handle(create_request())
    r = trial.result
    assert r.quantity_factor == D(2) and r.quantity_factor_reason == "Thí Nghiệm"
    flagged = {s.stage for s in r.weaving_stages if s.applies_quantity_factor}
    assert {"Dệt", "Kiểm"} <= flagged and "Se" not in flagged and "Gia công Dệt" not in flagged
    for stage in r.weaving_stages:
        factor = r.quantity_factor if stage.applies_quantity_factor else D(1)
        assert abs(stage.amount_after_factor - stage.amount * factor) < D("0.000001"), stage.stage
    assert abs(sum(s.amount_after_factor for s in r.weaving_stages) - r.weaving_total) < D("0.000001")
    assert production.result.quantity_factor_reason.endswith(" m mộc")
