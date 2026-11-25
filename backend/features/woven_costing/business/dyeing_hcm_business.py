"""BR-26 dyeing cost at the HCM plant (đ/kg finished, then đ/m) and the HCM part of BR-17."""

from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.woven_costing.business.discount_business import DiscountBusiness
from backend.features.woven_costing.business.norm_lookup_business import NormLookupBusiness
from backend.features.woven_costing.business.numbers import ONE, ZERO, div, num
from backend.features.woven_costing.constants import BLENDED, HCM_COLORS
from backend.features.woven_costing.models.checks import Check
from backend.features.woven_costing.models.cost_items import CostItems
from backend.features.woven_costing.models.costing_context import CostingContext
from backend.features.woven_costing.models.costsheet_result import CostWarning, DyeingLine, DyeingOutcome
from backend.features.woven_costing.models.enums import NO_DYEING_FORMS
from backend.features.woven_costing.models.parameter_set import APPLIED_HCM
from backend.features.woven_costing.models.parameter_tables import DiscountPick

STANDARD = "Nhuộm tiêu chuẩn"
STAGE = "Công đoạn đặc biệt"
FEATURE = "Tính năng đặc biệt"
SPECIAL = "Chi phí đặc biệt"
EXTRA = "Chi phí phát sinh"
OUTSOURCE = "Gia công"


class HcmFeatureNormRule(BaseBusinessRule[Check]):
    """Target text = feature, other = fabric type; ok = a norm exists."""

    code = "BR-26"
    message = "Tính năng không có định mức cho nguyên liệu đã chọn."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"Tính năng {target.text} không có định mức cho nguyên liệu {target.other}."


class DyeingHcmBusiness(BaseBusiness[CostingContext]):
    def __init__(self, context: CostingContext) -> None:
        self.context = context
        self.lookup = NormLookupBusiness(context.tables)
        self.sheet = context.costsheet
        self.input = context.costsheet.hcm_dyeing

    def has_standard(self) -> bool:
        return bool(self.input.dye_material and self.input.color_level)

    def has_extra_cost(self) -> bool:
        extra = self.input.extra_cost
        return extra is not None and extra.items.total > 0

    def dye_loss(self) -> Decimal:
        """BR-17 (HCM): extra cost -> dye_loss_rate; else dye_loss_rate + losses of the special stages. Mộc -> 0."""
        if self.sheet.sale_form in NO_DYEING_FORMS:
            return ZERO
        base = num(self.input.dye_loss_rate)
        if self.has_extra_cost():
            return base
        stages = [self.lookup.hcm_stage(name) for name in self.input.special_stages if name]
        return base + sum((s.loss_rate for s in stages if s is not None), ZERO)

    def discount(self, finished_kg: Decimal) -> DiscountPick:
        """BR-26 (2026-11-25): factor of the 4.6.1 Nhuộm HCM rows (Thí nghiệm, or Đại trà by kg TP)."""
        return DiscountBusiness().hcm(self.context.discount_tables(), finished_kg, self.sheet.order_type)

    def small_lot_factor(self, finished_kg: Decimal) -> Decimal:
        """BR-26: factor of HCTN and Tiền lương (x2 for Thí Nghiệm or a small lot); BR-46 override when typed."""
        overridden = self.context.applied_overrides.get(APPLIED_HCM)
        return overridden if overridden is not None else self.discount(finished_kg).factor

    def adjusted(self, items: CostItems, factor: Decimal) -> CostItems:
        """BR-26: HCTN and Tiền lương x factor; every item / width type (1, 2, 3)."""
        width = Decimal(self.input.width_type or 1)
        doubled = items.model_copy(update={"chemical": items.chemical * factor, "labor": items.labor * factor})
        return doubled.scaled(ONE / width)

    def standard_items(self, warnings: list[CostWarning]) -> CostItems | None:
        """BR-26 (a): NhuomHCM_TieuChuan[loại vải, cấp màu]; Blended = sum(ratio x row of each colour)."""
        material, color = self.input.dye_material, self.input.color_level
        if color == BLENDED:
            ratios = [num(r) for r in self.input.blend_ratios]
            if abs(sum(ratios, ZERO) - ONE) > Decimal("0.0001"):
                return None
            total = CostItems()
            for ratio, level in zip(ratios, HCM_COLORS, strict=False):
                row = self.lookup.hcm_standard(material, level)
                if ratio and row is None:
                    warnings.append(_missing(f"{material} - {level}"))
                elif row is not None:
                    total = total.plus(row.items.scaled(ratio))
            return total
        row = self.lookup.hcm_standard(material, color)
        if row is None:
            warnings.append(_missing(f"{material} - {color}"))
            return None
        return row.items

    def calculate(self, finished_kg: Decimal, finished_m_per_kg: Decimal) -> DyeingOutcome:
        """BR-26: lines (a) tiêu chuẩn, (b) công đoạn đặc biệt, (c) tính năng, (d) chi phí đặc biệt,
        (e) chi phí phát sinh (then total = phát sinh + gia công only), (f) gia công. đ/m = đ/kg / m/kg TP."""
        if self.sheet.sale_form in NO_DYEING_FORMS:
            return DyeingOutcome()
        warnings: list[CostWarning] = []
        factor = self.small_lot_factor(finished_kg)
        lines: list[DyeingLine] = []

        def add(group: str, name: str, items: CostItems, loss: Decimal = ZERO, note: str = "") -> None:
            per_kg = items.total
            lines.append(DyeingLine(group=group, name=name, items=items, factor=factor, loss_rate=loss, per_kg=per_kg,
                                    per_m=div(per_kg, finished_m_per_kg), note=note))  # fmt: skip

        if not self.has_extra_cost():
            if self.has_standard():
                items = self.standard_items(warnings)
                name = f"{STANDARD} - {self.input.dye_material} - {self.input.color_level}"
                if items is not None:
                    add(STANDARD, name, self.adjusted(items, factor), num(self.input.dye_loss_rate))
            for stage_name in [s for s in self.input.special_stages if s]:
                stage = self.lookup.hcm_stage(stage_name)
                if stage is None:
                    warnings.append(_missing(stage_name))
                    continue
                add(STAGE, stage_name, self.adjusted(stage.items, factor), stage.loss_rate)
            rule = HcmFeatureNormRule()
            for feature in [f for f in self.input.special_features if f]:
                norm = self.lookup.hcm_feature(feature, self.input.dye_material)
                check = Check(ok=norm is not None, text=feature, other=self.input.dye_material)
                if norm is None:
                    warnings.append(CostWarning(code=rule.code, message=rule.describe_violation(check), blocking=True))
                    continue
                add(FEATURE, feature, self.adjusted(norm.items, factor), note=norm.chemical_note)
            for cost in [c for c in self.input.special_costs if c.name or c.amount]:
                add(SPECIAL, cost.name, CostItems(chemical=num(cost.amount)))
        else:
            extra = self.input.extra_cost
            if extra is not None:
                add(EXTRA, extra.name or EXTRA, extra.items, num(self.input.dye_loss_rate))
        for line in [o for o in self.input.outsourcing_lines if o.name or o.amount]:
            add(OUTSOURCE, line.name, CostItems(material=num(line.amount)))
        per_kg = sum((line.per_kg for line in lines), ZERO)
        items = CostItems()
        for line in lines:
            items = items.plus(line.items)
        return DyeingOutcome(
            lines=lines,
            per_kg=per_kg,
            per_m=div(per_kg, finished_m_per_kg),
            items_per_m=items.scaled(div(ONE, finished_m_per_kg)),
            factor=factor,
            warnings=warnings,
        )


def _missing(name: str) -> CostWarning:
    return CostWarning(
        code="BR-26",
        message=f"Định mức nhuộm {name} không có trong bảng tra. Kiểm tra lại thông tin nhập.",
        blocking=True,
    )
