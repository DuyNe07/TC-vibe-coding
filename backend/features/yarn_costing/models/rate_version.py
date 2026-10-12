"""4.5 Bảng định mức chi phí/phút (Rate version) + 4.5.1 Dòng định mức."""

from datetime import date
from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseEntity, BaseValueObject
from backend.features.yarn_costing.models.enums import FactoryCode


class RateLine(BaseValueObject):
    rate_code: str = Field(min_length=1, max_length=20)
    labor: Decimal = Field(ge=0)
    depreciation: Decimal = Field(ge=0)
    electricity: Decimal = Field(ge=0)
    materials: Decimal = Field(ge=0)
    overhead: Decimal = Field(ge=0)
    note: str = Field(default="", max_length=200)

    @property
    def total_rate(self) -> Decimal:
        return self.labor + self.depreciation + self.electricity + self.materials + self.overhead

    @property
    def components(self) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
        return (self.labor, self.depreciation, self.electricity, self.materials, self.overhead)


class RateVersion(BaseEntity):
    version_code: str = Field(min_length=1, max_length=30)
    factory_code: FactoryCode
    effective_date: date
    reason: str = Field(min_length=1, max_length=500)
    created_by: str = ""
    lines: list[RateLine] = Field(default_factory=list)

    def line_for(self, rate_code: str) -> RateLine | None:
        return next((line for line in self.lines if line.rate_code == rate_code), None)
