"""4.7 Hồi phế (Recovery rate)."""

from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseEntity
from backend.features.yarn_costing.models.enums import FactoryCode, RecoveryType


class RecoveryRate(BaseEntity):
    factory_code: FactoryCode
    recovery_type: RecoveryType
    rate: Decimal = Field(ge=0, lt=1)
