"""4.4 Tỷ giá, 4.7 Hệ số theo mã hàng, 4.8 Ngày lễ, 4.9 Khách hàng."""

import datetime as dt
from decimal import Decimal
from typing import Final

from pydantic import Field

from backend.core.base import BaseEntity
from backend.features.woven_costing.models.enums import CostItem, CustomerTeam, FactorStage


class ExchangeRate(BaseEntity):
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2020, le=2100)
    rate: Decimal = Field(gt=0)
    updated_by: str = ""


class FabricFactor(BaseEntity):
    tcfno: str = Field(min_length=10, max_length=10)
    stage: FactorStage
    cost_item: CostItem
    multiplier: Decimal = Field(default=Decimal(1), gt=0)
    addition: Decimal = Decimal(0)
    effective_from: dt.date
    active: bool = True
    note: str = Field(default="", max_length=300)


class Holiday(BaseEntity):
    date: dt.date
    name: str = Field(min_length=1, max_length=100)


class Customer(BaseEntity):
    customer_code: str = Field(min_length=2, max_length=8, pattern=r"^[A-Z0-9]+$")
    name: str = Field(min_length=2, max_length=200)
    team: CustomerTeam
    created_by: str = ""
    active: bool = True


# 4.7 initial data: (tcfno, stage, cost item, multiplier, addition)
_SEED_FACTORS: Final = (
    (FactorStage.SIZING, CostItem.CHEMICAL, "1.5", "0"),
    (FactorStage.WEAVING, CostItem.LABOR, "1.25", "0"),
    (FactorStage.WEAVING, CostItem.MATERIAL, "1.12", "231"),
)
SEED_FACTOR_CODES: Final = ("ES17020213", "ES17020413")


def initial_fabric_factors() -> list[FabricFactor]:
    """4.7 initial data: ES17020213 and ES17020413, 3 lines each, effective 2026-01-01."""
    return [
        FabricFactor(
            tcfno=code,
            stage=stage,
            cost_item=item,
            multiplier=Decimal(mul),
            addition=Decimal(add),
            effective_from=dt.date(2026, 1, 1),
            note="Dữ liệu ban đầu từ file Excel",
        )  # fmt: skip
        for code in SEED_FACTOR_CODES
        for stage, item, mul, add in _SEED_FACTORS
    ]
