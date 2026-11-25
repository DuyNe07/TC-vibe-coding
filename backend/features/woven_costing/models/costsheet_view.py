"""Stored data shown with one costsheet on Screen 2: versions, history, default parameters, fabric source."""

from pydantic import Field

from backend.core.base import BaseValueObject
from backend.features.woven_costing.models.costsheet import Costsheet, CostsheetHistory
from backend.features.woven_costing.models.enums import FabricSource
from backend.features.woven_costing.models.parameter_set import ParameterValues


class CostsheetView(BaseValueObject):
    versions: list[Costsheet] = Field(default_factory=list)
    history: list[CostsheetHistory] = Field(default_factory=list)
    defaults: ParameterValues = Field(default_factory=ParameterValues)
    fabric_source: FabricSource | None = None
