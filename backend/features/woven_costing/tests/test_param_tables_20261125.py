"""Extension 2026-11-25: parameters by department, quantity discount table (4.6.1), % B/C table (4.6.2), BR-88,
set effective 25/11/2026 (liquidation prices 0), applied discount editable per costsheet (BR-46). AC-63..AC-69."""

from datetime import date
from decimal import Decimal

import pytest

from backend.core.base import EmptyRequest
from backend.features.woven_costing.business.costing_business import CostingBusiness
from backend.features.woven_costing.business.discount_business import DiscountBusiness
from backend.features.woven_costing.business.dyeing_tcdn_business import DyeingTcdnBusiness
from backend.features.woven_costing.business.master_business import MasterBusiness
from backend.features.woven_costing.business.quantity_business import QuantityBusiness
from backend.features.woven_costing.dto.costsheet_dto import ParameterOverrideDTO
from backend.features.woven_costing.dto.master_dto import BcRowDTO, DiscountRowDTO, SaveParameterSetRequest
from backend.features.woven_costing.exceptions import CostsheetValidationError
from backend.features.woven_costing.models.costing_context import CostingContext
from backend.features.woven_costing.models.costsheet_input import TcdnDyeingInput, TcdnStageInput
from backend.features.woven_costing.models.enums import (
    DiscountCondition,
    DiscountDepartment,
    OrderType,
    ParamGroup,
    SaleForm,
)
from backend.features.woven_costing.models.parameter_set import (
    ParameterSet,
    ParameterValues,
    company_rule_set,
    initial_parameter_set,
    legacy_tables,
)
from backend.features.woven_costing.repositories.norm_repository import ParameterSetRepository
from backend.features.woven_costing.services.calculate_costsheet_service import CalculateCostsheetService
from backend.features.woven_costing.services.create_costsheet_service import CreateCostsheetService
from backend.features.woven_costing.services.list_parameter_sets_service import ListParameterSetsService
from backend.features.woven_costing.services.save_parameter_set_service import SaveParameterSetService
from backend.features.woven_costing.tests.helpers import (
    SALES_FS1,
    SO,
    as_user,
    create_request,
    full_input,
    seed_master,
)
from backend.features.woven_costing.tests.test_ac09_real_costsheets import CASES, R2, _tables

D = Decimal
P = ParameterValues()
NEW_DAY = date(2026, 11, 26)
NEW = company_rule_set(initial_parameter_set()).effective_tables()
OLD = legacy_tables(P)


def _old_sets() -> None:
    """A database holding sets saved before 2026-11-25 (no tables stored), like the local / shared one."""
    repo = ParameterSetRepository()
    repo.add(ParameterSet(effective_from=date(2026, 1, 1), values=P))
    late = P.model_copy(update={"yarn_waste_price": D(0), "sa_rate": D("0.11")})
    repo.add(ParameterSet(effective_from=date(2026, 11, 23), values=late))


def test_ac63_company_steps_for_the_new_set() -> None:
    """AC-63 (BR-23, 4.6.1): steps, no interpolation; reason = the row of the table."""
    q = QuantityBusiness()
    factor = lambda m, kind=OrderType.PRODUCTION: q.quantity_factor(D(m), SaleForm.FINISHED, kind, P, NEW)  # noqa: E731
    assert factor(7500) == D("1.05")
    assert factor(20000) == D(1) and factor(20001) == D("0.95")
    assert factor(50000) == D("0.92") and factor(4000) == D("1.1") and factor(150000) == D("0.9")
    assert factor(7500, OrderType.TRIAL) == D(2)
    pick = DiscountBusiness().weaving(NEW, D(7500), SaleForm.FINISHED, OrderType.PRODUCTION)
    assert pick.reason == "Đại trà 5.000 ≤ SL < 10.000 m mộc"
    missing = DiscountBusiness().weaving(NEW, D(1), SaleForm.FINISHED, OrderType.PRODUCTION)
    assert not missing.found and missing.factor == D(1)


def test_ac64_old_sets_keep_the_excel_formula() -> None:
    """AC-64: a set stored before 2026-11-25 reads as interpolated tables: 7 500 m -> 1,025; AC-09 unchanged."""
    q = QuantityBusiness()
    assert q.quantity_factor(D(7500), SaleForm.FINISHED, OrderType.PRODUCTION, P, OLD) == D("1.025")
    assert q.quantity_factor(D(5000), SaleForm.FINISHED, OrderType.PRODUCTION, P, OLD) == D("1.05")
    assert q.quantity_factor(D(35000), SaleForm.FINISHED, OrderType.PRODUCTION, P, OLD) == D("0.935")
    assert initial_parameter_set().effective_tables() == OLD
    for _, sheet, _, _ in CASES:
        before = CostingBusiness().calculate(CostingContext(costsheet=sheet, tables=_tables(), params=P))
        seed = CostingContext(costsheet=sheet, tables=_tables(), params=P, param_tables=OLD)
        after = CostingBusiness().calculate(seed)
        assert (after.gp_pct, after.op_pct, after.quantity_factor) == (before.gp_pct, before.op_pct,
                                                                       before.quantity_factor)  # fmt: skip


def test_ac65_dyeing_factors_from_the_tables() -> None:
    """AC-65 (BR-25, BR-26): same factors as before with the new set."""
    business = DiscountBusiness()
    assert business.tcdn(NEW, D(50000), dyeing=True).factor == D("0.95")
    assert business.tcdn(NEW, D(120), dyeing=True).factor == D("1.2")
    assert business.tcdn(NEW, D(80), dyeing=False).factor == D("1.5")
    assert business.tcdn(NEW, D(500), dyeing=True).factor == D(1)
    assert business.hcm(NEW, D(900), OrderType.TRIAL).factor == D(2)
    assert business.hcm(NEW, D(200), OrderType.PRODUCTION).factor == D(2)
    assert business.hcm(NEW, D(250), OrderType.PRODUCTION).factor == D(1)
    partial = R2.model_copy(update={"order_meters": D(80), "tcdn_dyeing": TcdnDyeingInput(
        extra_stages=[TcdnStageInput(name="Setting")])})  # fmt: skip
    context = CostingContext(costsheet=partial, tables=_tables(), params=P, param_tables=NEW)
    assert DyeingTcdnBusiness(context).factor() == D("1.5")
    overridden = context.model_copy(update={"applied_overrides": {"discount_tcdn": D("1.3")}})
    assert DyeingTcdnBusiness(overridden).factor() == D("1.3")


def test_ac66_bc_rates_by_sale_form() -> None:
    """AC-66 (BR-16, 4.6.2): SO changes Vải Thành Phẩm to 6% / 3%; Mộc keeps 4% / 0%."""
    rows = [BcRowDTO(sale_form=r.sale_form, greige_bc_rate=r.greige_bc_rate, finished_bc_rate=r.finished_bc_rate)
            for r in NEW.bc_rows]  # fmt: skip
    rows = [r.model_copy(update={"greige_bc_rate": D("0.06"), "finished_bc_rate": D("0.03")})
            if r.sale_form == SaleForm.FINISHED else r for r in rows]  # fmt: skip
    with as_user(SO):
        SaveParameterSetService().handle(SaveParameterSetRequest(effective_from=date(2027, 1, 1), bc_rows=rows))
    saved = ParameterSetRepository().effective_on(date(2027, 1, 1))
    assert saved is not None and saved.tables is not None
    tables = saved.effective_tables()
    assert DiscountBusiness().bc_rates(tables, SaleForm.FINISHED) == (D("0.06"), D("0.03"))
    assert DiscountBusiness().bc_rates(tables, SaleForm.GREIGE) == (D("0.04"), D(0))
    assert not any(r.interpolate for r in tables.discount_rows)  # a new set always uses steps


def test_ac67_br88_refuses_overlaps_and_missing_sale_form() -> None:
    """AC-67 (BR-88): messages of the document."""
    mass, weaving = DiscountCondition.MASS, DiscountDepartment.WEAVING
    rows = [
        DiscountRowDTO(department=weaving, condition=mass, from_qty=D(1000), to_qty=D(8000), factor=D("1.1")),
        DiscountRowDTO(department=weaving, condition=mass, from_qty=D(5000), to_qty=D(10000), factor=D("1.05")),
        DiscountRowDTO(department=weaving, condition=mass, from_qty=D(10000), to_qty=D(20000), factor=D(1)),
    ]
    bc = [BcRowDTO(sale_form=SaleForm.GREIGE, greige_bc_rate=D("0.04"), finished_bc_rate=D(0)),
          BcRowDTO(sale_form=SaleForm.FINISHED, greige_bc_rate=D("0.05"), finished_bc_rate=D("0.04"))]  # fmt: skip
    request = SaveParameterSetRequest(effective_from=date(2027, 1, 1), discount_rows=rows, bc_rows=bc)
    with as_user(SO), pytest.raises(CostsheetValidationError) as refused:
        SaveParameterSetService().handle(request)
    assert refused.value.details == [
        "Bảng discount Dệt – Đại trà: khoảng 5.000–10.000 chồng lên khoảng khác.",
        "Bảng % B/C thiếu hình thức bán Vải Nhuộm.",
    ]
    touching = [rows[0].model_copy(update={"to_qty": D(5000)}), rows[1]]  # [1000; 5000) and [5000; 10000)
    request = request.model_copy(update={"discount_rows": touching, "bc_rows": None})
    with as_user(SO):
        SaveParameterSetService().handle(request)
    both_inclusive = [rows[0].model_copy(update={"to_qty": D(5000), "to_inclusive": True}), rows[1]]
    with as_user(SO), pytest.raises(CostsheetValidationError, match="chồng lên khoảng khác"):
        SaveParameterSetService().handle(
            request.model_copy(update={"effective_from": date(2027, 2, 1), "discount_rows": both_inclusive})
        )


def test_ac68_set_of_25_11_created_and_old_sets_unchanged() -> None:
    """AC-68: the set effective 25/11/2026 is created once from the latest set before it (liquidation prices 0,
    company Dệt steps); the old sets keep their numbers; values grouped by department."""
    _old_sets()
    listed = ListParameterSetsService().handle(EmptyRequest())
    again = ListParameterSetsService().handle(EmptyRequest())
    assert [s.effective_from for s in again.sets] == [date(2026, 11, 25), date(2026, 11, 23), date(2026, 1, 1)]
    new, late, first = listed.details
    value = lambda detail, code: next(v.default_value for v in detail.values if v.code == code)  # noqa: E731
    assert value(new, "yarn_waste_price") == 0 and value(new, "bc_fabric_price") == 0
    assert value(new, "sa_rate") == D("0.11")  # copied from the set of 23/11/2026
    assert value(first, "yarn_waste_price") == D(15000) and value(first, "bc_fabric_price") == D(5000)
    assert first.from_old_values and late.from_old_values and not new.from_old_values
    steps = [r for r in new.discount_rows if r.department == DiscountDepartment.WEAVING]
    assert [r.factor for r in steps] == [D("1.1"), D("1.05"), D(1), D("0.95"), D("0.92"), D("0.9"), D(2)]
    assert not any(r.interpolate for r in steps) and steps[0].reason == "Đại trà 1 < SL < 5.000 m mộc"
    assert any(r.interpolate for r in first.discount_rows)
    assert {v.group for v in new.values} == set(ParamGroup) - {ParamGroup.HCM}
    stored = {s.effective_from: s for s in ParameterSetRepository().list_all()}
    assert stored[date(2026, 1, 1)].tables is None and stored[date(2026, 1, 1)].values == P


def test_ac69_applied_discount_editable_on_the_costsheet() -> None:
    """AC-69 (BR-46, block G): applied Dệt factor with its reason; sales changes it -> weaving cost follows;
    GP threshold stays SO only; old single-value overrides keep working."""
    seed_master()
    _old_sets()
    with as_user(SALES_FS1):
        created = CreateCostsheetService(today=NEW_DAY).handle(create_request(costing_date=NEW_DAY))
        calc = CalculateCostsheetService(today=NEW_DAY).handle(full_input(created))
    assert calc.parameter_set_date == date(2026, 11, 25)
    row = next(p for p in calc.parameters if p.code == "discount_weaving")
    assert row.group == ParamGroup.WEAVING and row.label == "Hệ số discount đang áp dụng" and row.reason
    assert row.default_value == row.used_value == calc.result.quantity_factor
    assert {p.code for p in calc.parameters} >= {"discount_hcm", "greige_bc_rate", "finished_bc_rate"}
    overrides = [ParameterOverrideDTO(code="discount_weaving", used_value=D("0.5")),
                 ParameterOverrideDTO(code="gp_threshold", used_value=D("0.01"))]  # fmt: skip
    with as_user(SALES_FS1):
        changed = CalculateCostsheetService(today=NEW_DAY).handle(full_input(created, parameter_overrides=overrides))
    edited = next(p for p in changed.parameters if p.code == "discount_weaving")
    assert edited.used_value == D("0.5") and edited.default_value == row.default_value
    assert changed.result.quantity_factor == D("0.5") and changed.result.weaving_total < calc.result.weaving_total
    gp = next(p for p in changed.parameters if p.code == "gp_threshold")
    assert gp.used_value == gp.default_value == D("0.15")
    values, kept = MasterBusiness().apply_overrides(P, {"qf_at_5000": D("1.06")})
    assert len(kept) == 1 and QuantityBusiness().quantity_factor(D(5000), None, None, values) == D("1.06")
