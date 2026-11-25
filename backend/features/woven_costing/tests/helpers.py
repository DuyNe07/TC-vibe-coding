"""Shared test data: users with app roles, a fabric, rates, a customer and in-memory Excel files."""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import Any

from openpyxl import Workbook

from backend.core.base import UploadedFileDTO
from backend.core.current_user import CurrentUser, get_current_user, set_current_user
from backend.features.woven_costing.dto.costsheet_dto import (
    CostsheetInputRequest,
    CostsheetResponse,
    CreateCostsheetRequest,
    HcmDyeingInputDTO,
    PriceInputDTO,
    WeavingInputDTO,
    YarnLineInputDTO,
)
from backend.features.woven_costing.models.enums import (
    Currency,
    CustomerTeam,
    DyePlant,
    FabricSource,
    Market,
    OrderType,
    PriceType,
    SaleForm,
    YarnDirection,
    YarnKind,
)
from backend.features.woven_costing.models.fabric import Fabric, FabricSpecs, FabricYarn
from backend.features.woven_costing.models.master import Customer, ExchangeRate
from backend.features.woven_costing.repositories.fabric_repository import FabricRepository
from backend.features.woven_costing.repositories.master_repository import CustomerRepository, ExchangeRateRepository

D = Decimal
KEY = "woven_costing"
TODAY = date(2026, 11, 20)
FABRIC = "EM35790026"
SELL = D("2.6")


def user(name: str, *roles: str) -> CurrentUser:
    return CurrentUser(username=name, full_name=name.title(), permissions=frozenset(f"{KEY}/@{r}" for r in roles))


@contextmanager
def as_user(current: CurrentUser | None) -> Iterator[None]:
    previous = get_current_user()
    set_current_user(current)
    try:
        yield
    finally:
        set_current_user(previous)


SALES_FS1 = user("sales1", "SALES", "FS1")
SALES_FS2 = user("sales2", "SALES", "FS2")
LEAD_FS1 = user("lead1", "TRUONG_TEAM", "FS1")
LEAD_FS2 = user("lead2", "TRUONG_TEAM", "FS2")
HEAD = user("head", "TRUONG_DON_VI")
SO = user("so1", "SO")


def make_fabric(code: str = FABRIC, source: FabricSource = FabricSource.PEACE, name: str = "TC34/1 + DTY75D") -> Fabric:
    yarns = [
        FabricYarn(direction=YarnDirection.WARP, seq=1, yarn_name="TC 34/1 (65/35)", raw_yarn_name="TC 34/1 (65/35)",
                   rate=D("63.67"), raw_rate=D(100), yarn_kind=YarnKind.SINGLE),
        FabricYarn(direction=YarnDirection.WARP, seq=2, yarn_name="DTY75D/36F/1HIM 400T/M",
                   raw_yarn_name="DTY75D/36F/1HIM", rate=D("0.83"), raw_rate=D(100), twist_tpm="400T/M"),
        FabricYarn(direction=YarnDirection.WEFT, seq=1, yarn_name="DTY 150D/48F/1 SIM",
                   raw_yarn_name="DTY 150D/48F/1 SIM", rate=D("35.5"), raw_rate=D(100)),
    ]  # fmt: skip
    specs = FabricSpecs(
        greige_width_cm=D(175), greige_weft_density=D(252), greige_warp_density=D(431), greige_g_per_m=D(217),
        greige_gsm=D(124), finished_width_cm=D(154), finished_weft_density=D(280), finished_warp_density=D(470),
        finished_g_per_m=D(230), finished_gsm=D(150),
    )  # fmt: skip
    return Fabric(tcfno=code, fabric_name=name, specs=specs, source=source, yarns=yarns)


def seed_master(rate_months: tuple[tuple[int, int], ...] = ((11, 2026),)) -> None:
    FabricRepository().add(make_fabric())
    CustomerRepository().add(Customer(customer_code="ICHI", name="Ichimura Sangyo", team=CustomerTeam.FS1))
    for month, year in rate_months:
        ExchangeRateRepository().add(ExchangeRate(month=month, year=year, rate=D(26000)))


def create_request(**changes: Any) -> CreateCostsheetRequest:
    values = {
        "dye_plant": DyePlant.HCM, "customer_name": "Ichimura Sangyo", "market": Market.EXPORT,
        "order_type": OrderType.PRODUCTION, "sale_form": SaleForm.FINISHED, "costing_date": TODAY, "tcfno": FABRIC,
        "order_meters": D(10000), "price_type": PriceType.FOB,
    }  # fmt: skip
    return CreateCostsheetRequest(**(values | changes))


def full_input(sheet: CostsheetResponse, sell: Decimal = SELL, **changes: Any) -> CostsheetInputRequest:
    """Every cell needed to send for approval (prices typed today, HCM standard dyeing)."""
    data = sheet.input.model_dump()
    data["yarn_lines"] = [
        YarnLineInputDTO(direction=y.direction, seq=y.seq, price_currency=Currency.USD, price_input=D("3"),
                         waste_rate=D("0.02"), is_twisted=False, is_sized=y.is_sized)
        for y in sheet.yarn_lines
    ]  # fmt: skip
    data["twist_lines"] = []
    data["weaving"] = WeavingInputDTO(size_material="TC", warping_band="Không")
    data["hcm_dyeing"] = HcmDyeingInputDTO(dye_material="TC/CVC/TR thường", color_level="Đậm", dye_loss_rate=D("0.024"))
    data["price"] = PriceInputDTO(sell_price_currency=Currency.USD, sell_price_input=sell)
    data["shrinkage_reason"] = "Mộc khách gửi đã ổn định"
    data |= changes
    return CostsheetInputRequest(costsheet_id=sheet.id, **data)


def xlsx(
    rows: list[list[Any]], name: str = "file.xlsx", sheets: dict[str, list[list[Any]]] | None = None
) -> UploadedFileDTO:
    workbook = Workbook()
    if sheets:
        workbook.remove(workbook.active)
        for title, data in sheets.items():
            ws = workbook.create_sheet(title)
            for row in data:
                ws.append(row)
    else:
        for row in rows:
            workbook.active.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return UploadedFileDTO(filename=name, content=buffer.getvalue())
