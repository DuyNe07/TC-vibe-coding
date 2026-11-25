"""Extension 2026-11-25: 2 job sale forms - Gia công dệt (BR-89) and Gia công nhuộm (BR-90); AC-70..AC-75."""

from decimal import Decimal

from backend.features.woven_costing.builders.parameter_builders import parameter_set_detail
from backend.features.woven_costing.business.costing_business import CostingBusiness
from backend.features.woven_costing.business.discount_business import DiscountBusiness
from backend.features.woven_costing.business.submission_business import SubmissionBusiness
from backend.features.woven_costing.models.costing_context import CostingContext
from backend.features.woven_costing.models.costsheet_result import CostsheetResult
from backend.features.woven_costing.models.enums import OrderType, SaleForm
from backend.features.woven_costing.models.norm_set import initial_tables
from backend.features.woven_costing.models.parameter_set import ParameterValues, initial_parameter_set, legacy_tables
from backend.features.woven_costing.models.parameter_tables import BcRow, ParameterTables
from backend.features.woven_costing.tests.test_ac09_real_costsheets import R1, R2, R3
from backend.features.woven_costing.tests.test_ui_20261123 import _assert_reconciles, _response, _steps

D = Decimal
P = ParameterValues()


def _calc(sheet, **changes) -> CostsheetResult:  # type: ignore[no-untyped-def]
    context = CostingContext(costsheet=sheet.model_copy(update=changes), tables=initial_tables(), params=P)
    return CostingBusiness().calculate(context)


def test_ac70_weaving_job_keeps_weaving_drops_yarn_and_dyeing() -> None:
    """BR-89: same greige meters and weaving cost as Mộc; yarn kg kept, yarn cost 0; no dyeing, no B/C liquidation."""
    greige = _calc(R1)
    job = _calc(R1, sale_form=SaleForm.WEAVING_JOB)
    assert greige.bc_liquidation > 0  # the Mộc costsheet does liquidate B/C
    assert job.greige_meters == greige.greige_meters
    assert job.weaving_total == greige.weaving_total > 0
    assert job.quantity_factor == greige.quantity_factor
    assert [line.yarn_kg for line in job.yarn_lines] == [line.yarn_kg for line in greige.yarn_lines]
    assert all(line.amount == 0 for line in job.yarn_lines) and job.yarn_total == 0
    assert job.dyeing_total == 0 and job.bc_liquidation == 0 and job.shrinkage == 0
    assert job.total_cost == job.weaving_total


def test_ac70_weaving_job_submits_without_yarn_price() -> None:
    lines = [line.model_copy(update={"price_input": D(0)}) for line in R1.yarn_lines]
    sub = SubmissionBusiness()
    assert any("giá sợi" in m for m in sub.missing_data(R1.model_copy(update={"yarn_lines": lines})))
    job = R1.model_copy(update={"yarn_lines": lines, "sale_form": SaleForm.WEAVING_JOB})
    assert not any("giá sợi" in m for m in sub.missing_data(job))
    assert sub.missing_dyeing(job) == []


def test_ac71_dyeing_job_keeps_dyeing_only() -> None:
    """BR-90: same dyeing cost and greige meters as Vải Nhuộm; no greige purchase, weaving, yarn or B/C liquidation."""
    for sheet in (R3, R2):
        dyed = _calc(sheet, sale_form=SaleForm.DYED, greige_buy_price=D(21000))
        job = _calc(sheet, sale_form=SaleForm.DYEING_JOB, greige_buy_price=None)
        assert job.dyeing_total == dyed.dyeing_total > 0
        assert job.greige_meters == dyed.greige_meters
        assert job.weaving_total == 0 and job.quantity_factor == 0
        assert job.bc_liquidation == 0
        assert job.total_cost == job.dyeing_total


def test_ac71_dyeing_job_submits_without_greige_price() -> None:
    sub = SubmissionBusiness()
    dyed = R3.model_copy(update={"sale_form": SaleForm.DYED, "greige_buy_price": None})
    assert "giá vải mộc mua ngoài" in sub.missing_data(dyed)
    job = R3.model_copy(update={"sale_form": SaleForm.DYEING_JOB, "greige_buy_price": None})
    assert "giá vải mộc mua ngoài" not in sub.missing_data(job)


def test_ac72_job_order_type_does_not_change_the_calculation() -> None:
    """BR-91: the order type stays free; the calculation follows the sale form only."""
    as_job = _calc(R1, sale_form=SaleForm.WEAVING_JOB, order_type=OrderType.OUTSOURCE)
    as_production = _calc(R1, sale_form=SaleForm.WEAVING_JOB, order_type=OrderType.PRODUCTION)
    assert as_job.total_cost == as_production.total_cost
    assert as_job.yarn_total == 0


def test_ac73_bc_rows_fall_back_and_can_be_set() -> None:
    """BR-16 / BR-88: a set without job rows reads Mộc / Vải Nhuộm rows; a typed job row is used; job rows optional."""
    discount = DiscountBusiness()
    old = legacy_tables(P)
    assert discount.bc_rates(old, SaleForm.WEAVING_JOB) == discount.bc_rates(old, SaleForm.GREIGE) == (D("0.04"), D(0))
    assert discount.bc_rates(old, SaleForm.DYEING_JOB) == discount.bc_rates(old, SaleForm.DYED)
    assert discount.table_errors(old) == []
    typed = ParameterTables(
        discount_rows=old.discount_rows,
        bc_rows=[*old.bc_rows, BcRow(sale_form=SaleForm.WEAVING_JOB, greige_bc_rate=D("0.03"), finished_bc_rate=D(0))],
    )
    assert discount.bc_rates(typed, SaleForm.WEAVING_JOB) == (D("0.03"), D(0))
    assert discount.table_errors(typed) == []
    missing_dyed = ParameterTables(discount_rows=old.discount_rows, bc_rows=old.bc_rows[:2])
    assert any("Vải Nhuộm" in e for e in discount.table_errors(missing_dyed))
    forms = [r.sale_form for r in parameter_set_detail(initial_parameter_set()).bc_rows]
    assert forms == [SaleForm.GREIGE, SaleForm.FINISHED, SaleForm.DYED, SaleForm.WEAVING_JOB, SaleForm.DYEING_JOB]


def test_ac74_demand_chain_of_job_orders() -> None:
    weaving = _response(R1.model_copy(update={"sale_form": SaleForm.WEAVING_JOB}))
    steps = _steps(weaving)
    assert "Sợi khách giao" in steps and steps["Sợi khách giao"].kg and steps["Chi phí Sợi"].cost == 0
    assert "Chi phí Nhuộm" not in steps and "Thanh lý B/C (trừ)" not in steps
    _assert_reconciles(weaving)
    dyeing = _response(R2.model_copy(update={"sale_form": SaleForm.DYEING_JOB}))
    steps = _steps(dyeing)
    assert steps["Mộc khách giao"].cost == 0 and steps["Mộc khách giao"].meters == dyeing.result.greige_meters
    assert "Chi phí Dệt" not in steps and "Sợi" not in steps and "Mua mộc ngoài" not in steps
    assert "Thanh lý B/C (trừ)" not in steps
    _assert_reconciles(dyeing)
    assert dyeing.result.quantity_factor_reason == "Gia công nhuộm: không áp dụng"


def test_ac75_regression_old_sale_forms() -> None:
    """The 3 old sale forms keep their formula (the 4 real costsheets of AC-09 are checked in their own test)."""
    greige = _calc(R1)
    assert greige.total_cost == greige.yarn_total + greige.weaving_total + greige.dyeing_total - greige.bc_liquidation
    dyed = _calc(R3, sale_form=SaleForm.DYED, greige_buy_price=D(21000))
    assert dyed.total_cost == D(21000) * dyed.greige_meters + dyed.dyeing_total - dyed.bc_liquidation
    assert dyed.bc_liquidation != 0
