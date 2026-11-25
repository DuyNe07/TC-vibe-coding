"""Fix 2026-11-25 (Prompt 03): WR on TCDN, like the costsheet file "Tinh Gia Det - TCDN" (rows 91 and 104, E41).

- choosing a WR chemical adds the row "Kiểm trước WR" (stage Kiểm Trung Gian, row 104), its loss counted in the
  dyeing loss;
- the 1% loss of WR (tenter) is NOT added to the dyeing loss (already inside the 4% standard loss);
- the WR items stay divided by (1 - co) and (1 - 1%) (confirmed by the user: WR runs on the tenter).
"""

from decimal import Decimal

from backend.features.woven_costing.business.dyeing_job_business import DyeingJobBusiness
from backend.features.woven_costing.business.dyeing_tcdn_business import DyeingTcdnBusiness
from backend.features.woven_costing.models.costing_context import CostingContext
from backend.features.woven_costing.models.costsheet_input import TcdnDyeingInput
from backend.features.woven_costing.models.dyeing_job import DyeingJob, DyeingJobLine
from backend.features.woven_costing.models.enums import DyePlant
from backend.features.woven_costing.models.norm_set import initial_tables
from backend.features.woven_costing.models.parameter_set import ParameterValues, legacy_tables
from backend.features.woven_costing.tests.helpers import TODAY
from backend.features.woven_costing.tests.test_ac09_real_costsheets import R2

D = Decimal
P = ParameterValues()
CHECK = "Kiểm trước WR"


def _business(**dyeing: object) -> DyeingTcdnBusiness:
    sheet = R2.model_copy(update={"tcdn_dyeing": R2.tcdn_dyeing.model_copy(update=dyeing)})
    return DyeingTcdnBusiness(CostingContext(costsheet=sheet, tables=initial_tables(), params=P))


def test_wr_adds_the_check_before_wr_row() -> None:
    without = _business()
    with_wr = _business(wr_chemical="W/R (C6)")
    lines = {line.name: line for line in with_wr.calculate(D("0.02"), D(4)).lines}
    assert CHECK in lines and "WR - W/R (C6)" in lines
    assert CHECK not in {line.name for line in without.calculate(D("0.02"), D(4)).lines}
    alone = with_wr.extra_stage("Kiểm Trung Gian", None, D("0.02"), [])
    assert alone is not None
    assert lines[CHECK].items == alone[0]


def test_wr_loss_not_added_but_check_loss_is() -> None:
    base = _business().dye_loss()
    wr = _business(wr_chemical="W/R (C6)")
    check_loss = wr.stage_loss("Kiểm Trung Gian")
    assert wr.dye_loss() == base + check_loss
    assert wr.stage_loss("WR") == D("0.01")  # the tenter loss stays out of the dyeing loss


def test_wr_items_still_divided_by_tenter_loss() -> None:
    found = _business(wr_chemical="W/R (C6)").wr(D("0.02"), [])
    assert found is not None
    items, loss = found
    assert loss == D("0.01")
    assert abs(items.labor - D("59.5347143109245") / D("0.98") / D("0.99")) <= D("0.000001")


def test_dyeing_job_line_with_wr_has_the_check_row() -> None:
    line = DyeingJobLine(item_code="X", g_per_m=D(245), g_per_m2=D(167), shrinkage=D("0.01"), quantity_m=D(1000),
                         job_price_vnd=D(1), tcdn_dyeing=TcdnDyeingInput(dye_material="Poly", wr_chemical="D.W/R"))  # fmt: skip
    job = DyeingJob(job_no="GC-X-2026-00001", costing_date=TODAY, dye_plant=DyePlant.TCDN, lines=[line])
    result = DyeingJobBusiness().calculate(job, initial_tables(), P, legacy_tables(P)).lines[0]
    assert CHECK in {c.name for c in result.cost_lines}
