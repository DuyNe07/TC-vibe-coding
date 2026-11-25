"""Stored data a (re)calculation needs: fabric, exchange rates, norm / parameter sets, fabric factors, holidays."""

from pydantic import Field

from backend.core.base import BaseValueObject
from backend.features.woven_costing.models.fabric import Fabric
from backend.features.woven_costing.models.master import ExchangeRate, FabricFactor, Holiday
from backend.features.woven_costing.models.norm_set import NormSet
from backend.features.woven_costing.models.parameter_set import ParameterSet


class CostingData(BaseValueObject):
    fabric: Fabric | None = None
    rates: list[ExchangeRate] = Field(default_factory=list)
    norm_sets: list[NormSet] = Field(default_factory=list)
    parameter_sets: list[ParameterSet] = Field(default_factory=list)
    factors: list[FabricFactor] = Field(default_factory=list)
    holidays: list[Holiday] = Field(default_factory=list)
