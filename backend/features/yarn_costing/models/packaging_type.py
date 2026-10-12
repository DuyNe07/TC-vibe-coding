"""4.6 Loại đóng gói (Packaging type)."""

from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseEntity
from backend.features.yarn_costing.models.enums import FactoryCode


class PackagingType(BaseEntity):
    factory_code: FactoryCode
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=200)
    weight_kg: Decimal | None = None
    man_days: Decimal | None = None
    minutes_per_kg: Decimal = Field(gt=0)
    active: bool = True
    is_default: bool = False
