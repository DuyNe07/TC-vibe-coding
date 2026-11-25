"""Everything one calculation needs (BR-10..BR-29): the costsheet, the norm tables, parameters and fabric factors."""

from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseValueObject
from backend.features.woven_costing.models.costsheet import Costsheet
from backend.features.woven_costing.models.master import FabricFactor
from backend.features.woven_costing.models.norm_set import NormTables
from backend.features.woven_costing.models.parameter_set import ParameterValues, legacy_tables
from backend.features.woven_costing.models.parameter_tables import ParameterTables


class CostingContext(BaseValueObject):
    costsheet: Costsheet
    tables: NormTables
    params: ParameterValues
    factors: list[FabricFactor] = Field(default_factory=list)
    # 4.6.1 / 4.6.2 tables of the parameter set (None = built from ``params``, as for sets stored before 2026-11-25)
    param_tables: ParameterTables | None = None
    # BR-46 (2026-11-25): applied discount factors / % B/C overridden on this costsheet (code -> value)
    applied_overrides: dict[str, Decimal] = Field(default_factory=dict)

    def discount_tables(self) -> ParameterTables:
        return self.param_tables if self.param_tables is not None else legacy_tables(self.params)
