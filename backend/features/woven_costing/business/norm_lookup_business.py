"""Lookups in the norm tables (4.5) and BR-24 fabric factors. Names are compared without case, as Excel MATCH."""

from datetime import date
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.woven_costing.business.count_business import CountBusiness
from backend.features.woven_costing.business.numbers import same_text
from backend.features.woven_costing.constants import TCDN_CPB
from backend.features.woven_costing.models.cost_items import CostItems
from backend.features.woven_costing.models.enums import CostItem, FactorStage
from backend.features.woven_costing.models.master import FabricFactor
from backend.features.woven_costing.models.norm_set import (
    HcmFeatureNorm,
    HcmStageNorm,
    HcmStandardNorm,
    MinuteRate,
    NormTables,
    SizeNorm,
    TcdnChemical,
    TcdnProcess,
    WeaveNorm,
    YarnCount,
)

ITEM_FIELDS = {
    CostItem.LABOR: "labor",
    CostItem.DEPRECIATION: "depreciation",
    CostItem.POWER: "power",
    CostItem.MATERIAL: "material",
    CostItem.FUEL: "fuel",
    CostItem.CHEMICAL: "chemical",
    CostItem.OVERHEAD: "overhead",
}


class NormLookupBusiness(BaseBusiness[NormTables]):
    def __init__(self, tables: NormTables) -> None:
        self.tables = tables

    def minute_rate(self, stage: str) -> MinuteRate | None:
        return next((r for r in self.tables.minute_rates if same_text(r.stage, stage)), None)

    def size_norm(self, material: str, group: str) -> SizeNorm | None:
        return next(
            (n for n in self.tables.size_norms if same_text(n.material, material) and same_text(n.group, group)), None
        )

    def weave_norm(self, density: int) -> WeaveNorm | None:
        return next((n for n in self.tables.weave_norms if n.density == density), None)

    def yarn_count(self, count: str) -> YarnCount | None:
        return next((c for c in self.tables.yarn_counts if same_text(c.count, count)), None)

    def hcm_standard(self, fabric_type: str, color: str) -> HcmStandardNorm | None:
        return next(
            (
                n
                for n in self.tables.hcm_standard
                if same_text(n.fabric_type, fabric_type) and same_text(n.color, color)
            ),
            None,
        )

    def hcm_stage(self, name: str) -> HcmStageNorm | None:
        return next((n for n in self.tables.hcm_stages if same_text(n.name, name)), None)

    def hcm_feature(self, feature: str, fabric_type: str) -> HcmFeatureNorm | None:
        """BR-26 (c): [tính năng, loại vải], otherwise [tính năng, rỗng]."""
        rows = [n for n in self.tables.hcm_features if same_text(n.feature, feature)]
        exact = next((n for n in rows if fabric_type and same_text(n.fabric_type, fabric_type)), None)
        return exact or next((n for n in rows if not n.fabric_type.strip()), None)

    def tcdn_process(self, code: str, material: str = "") -> TcdnProcess | None:
        """Process row by code; the CPB rows are one per dyeing material."""
        rows = [p for p in self.tables.tcdn_processes if same_text(p.code, code)]
        if same_text(code, TCDN_CPB):
            return next((p for p in rows if same_text(p.material, material)), None)
        return rows[0] if rows else None

    def tcdn_chemical(self, key: str, weight_group: str = "") -> TcdnChemical | None:
        return next(
            (
                c
                for c in self.tables.tcdn_chemicals
                if same_text(c.key, key) and same_text(c.weight_group or "", weight_group)
            ),
            None,
        )

    def list_values(self, category: str) -> list[str]:
        return [item.value for item in self.tables.lists if same_text(item.category, category)]

    def apply_factors(
        self, items: CostItems, stage: FactorStage, tcfno: str, on: date, factors: list[FabricFactor]
    ) -> CostItems:
        """BR-24: for every active factor line of this fabric and stage, effective on the costing date:
        norm of the cost item = norm x multiplier + addition (before the quantity factor)."""
        values = items.as_dict()
        for factor in factors:
            if factor.active and factor.tcfno == tcfno and factor.stage == stage and factor.effective_from <= on:
                field = ITEM_FIELDS[factor.cost_item]
                values[field] = values[field] * factor.multiplier + factor.addition
        return CostItems(**values)

    def twist_converted(self, count: str) -> Decimal | None:
        """BR-81 converted count (number of the list 4.5.6, otherwise the formula); None when not valid."""
        return CountBusiness(self.tables).convert(count).value
