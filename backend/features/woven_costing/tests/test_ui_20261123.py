"""UI change of Screen 2 (2026-11-23): "Chuỗi nhu cầu" rows and the tab (section) of every warning."""

from decimal import Decimal

from backend.features.woven_costing.builders.costsheet_response_builder import CostsheetResponseBuilder
from backend.features.woven_costing.builders.demand_chain_builder import warning_section
from backend.features.woven_costing.business.costing_business import CostingBusiness
from backend.features.woven_costing.dto.costsheet_dto import CostsheetResponse, DemandStepDTO
from backend.features.woven_costing.models.costing_context import CostingContext
from backend.features.woven_costing.models.costsheet import Costsheet
from backend.features.woven_costing.models.costsheet_input import PriceInput
from backend.features.woven_costing.models.costsheet_view import CostsheetView
from backend.features.woven_costing.models.enums import SaleForm, WarningSection
from backend.features.woven_costing.models.norm_set import initial_tables
from backend.features.woven_costing.models.parameter_set import ParameterValues
from backend.features.woven_costing.services.create_costsheet_service import CreateCostsheetService
from backend.features.woven_costing.tests.helpers import SALES_FS1, TODAY, as_user, create_request, seed_master
from backend.features.woven_costing.tests.test_ac09_real_costsheets import R1, R2

D = Decimal
TOLERANCE = D("0.000001")


def _response(sheet: Costsheet) -> CostsheetResponse:
    context = CostingContext(costsheet=sheet, tables=initial_tables(), params=ParameterValues())
    calculated = sheet.model_copy(update={"result": CostingBusiness().calculate(context)})
    return CostsheetResponseBuilder(calculated, CostsheetView()).build()


def _steps(response: CostsheetResponse) -> dict[str, DemandStepDTO]:
    return {s.step: s for s in response.result.demand_chain}


def _assert_reconciles(response: CostsheetResponse) -> None:
    r, chain = response.result, response.result.demand_chain
    costs = sum((s.cost for s in chain if s.cost is not None and not s.is_total), D(0))
    total = chain[-1]
    assert total.is_total
    assert abs(costs - r.total_cost) <= TOLERANCE
    assert total.cost == r.total_cost
    assert abs(total.cost / response.input.order_meters - r.unit_cost_vnd) <= TOLERANCE
    assert total.cost_per_m == r.unit_cost_vnd
    for step in chain:
        if step.cost is not None and not step.is_total:
            assert abs(step.cost_per_m - step.cost / response.input.order_meters) <= TOLERANCE


def test_demand_chain_finished_fabric() -> None:
    """Vải Thành Phẩm (TCDN): TP -> TP nhuộm -> Nhuộm -> mộc -> Dệt -> Sợi -> B/C -> total."""
    response = _response(R2)
    r = response.result
    assert [s.step for s in r.demand_chain] == [
        "Thành phẩm giao khách", "Thành phẩm nhuộm ra", "Chi phí Nhuộm", "Vải mộc", "Chi phí Dệt", "Sợi",
        "Chi phí Sợi", "Thanh lý B/C (trừ)", "Tổng chi phí / Đơn giá",
    ]  # fmt: skip
    steps = _steps(response)
    assert steps["Thành phẩm giao khách"].meters == D(10000)
    assert steps["Thành phẩm nhuộm ra"].meters == r.finished_meters_needed
    assert steps["Thành phẩm nhuộm ra"].kg == r.finished_kg
    assert steps["Chi phí Nhuộm"].cost == r.dyeing_total
    assert steps["Vải mộc"].meters == r.greige_meters
    assert steps["Vải mộc"].kg == r.greige_kg
    assert "Độ co" in steps["Vải mộc"].losses and "B/C mộc" in steps["Vải mộc"].losses
    assert steps["Chi phí Dệt"].cost == r.weaving_total
    assert steps["Sợi"].kg > 0
    assert steps["Chi phí Sợi"].cost == r.yarn_total
    assert steps["Thanh lý B/C (trừ)"].cost == -r.bc_liquidation < 0
    _assert_reconciles(response)


def test_demand_chain_greige_has_no_dyeing_rows() -> None:
    """Mộc: no finished-dyed and no Nhuộm rows; the sold meters are greige."""
    response = _response(R1)
    names = [s.step for s in response.result.demand_chain]
    assert "Thành phẩm nhuộm ra" not in names
    assert "Chi phí Nhuộm" not in names
    assert names[0] == "Thành phẩm giao khách" and "Vải mộc" in names and "Chi phí Sợi" in names
    _assert_reconciles(response)


def test_demand_chain_dyed_fabric_buys_greige() -> None:
    """Vải Nhuộm: no Dệt / Sợi rows; "Mua mộc ngoài" = greige price x greige meters."""
    sheet = R2.model_copy(update={"sale_form": SaleForm.DYED, "greige_buy_price": D(30000)})
    response = _response(sheet)
    steps = _steps(response)
    assert "Chi phí Dệt" not in steps and "Sợi" not in steps and "Chi phí Sợi" not in steps
    assert steps["Mua mộc ngoài"].cost == D(30000) * response.result.greige_meters
    assert "B/C mộc" not in steps["Vải mộc"].losses
    assert "Chi phí Nhuộm" in steps
    _assert_reconciles(response)


def test_demand_chain_empty_when_not_calculated() -> None:
    sheet = R2.model_copy(update={"order_meters": None})
    assert _response(sheet).result.demand_chain == []


def test_warning_sections_by_code_and_words() -> None:
    assert warning_section("BR-05", "Tỷ lệ sợi không đúng") == WarningSection.YARN
    assert warning_section("BR-44", "Giá sợi đã hết hiệu lực") == WarningSection.YARN
    assert warning_section("BR-21", "Tổng sản lượng Se") == WarningSection.WEAVING
    assert warning_section("BR-84", "Chưa có số cộng thêm cho spandex") == WarningSection.WEAVING
    assert warning_section("BR-25", "Thiếu giá hóa chất") == WarningSection.DYEING
    assert warning_section("BR-28", "GP% thấp") == WarningSection.PRICE
    assert warning_section("BR-42", "Chưa nhập giá bán.") == WarningSection.PRICE
    assert warning_section("BR-14", "Độ co không lớn hơn 5%") == WarningSection.FABRIC
    assert warning_section("BR-10", "Mã vải thiếu g/m") == WarningSection.FABRIC
    assert warning_section("BR-99", "Định mức Cone không có") == WarningSection.WEAVING
    assert warning_section("BR-99", "Điều gì đó") == WarningSection.OTHER


def test_response_warnings_carry_their_section() -> None:
    """No sell price -> BR-42 shown in the Giá bán & lợi nhuận tab."""
    response = _response(R2.model_copy(update={"price": PriceInput()}))
    sections = {w.code: w.section for w in response.warnings}
    assert sections["BR-42"] == WarningSection.PRICE


def test_new_costsheet_from_service_has_chain() -> None:
    seed_master()
    with as_user(SALES_FS1):
        sheet = CreateCostsheetService(today=TODAY).handle(create_request())
    assert sheet.result.calculated
    _assert_reconciles(sheet)
    assert all(w.section in WarningSection for w in sheet.warnings)
