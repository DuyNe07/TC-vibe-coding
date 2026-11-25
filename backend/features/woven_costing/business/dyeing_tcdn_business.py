"""BR-25 dyeing cost at the TCDN plant (đ/m finished) and the TCDN part of BR-17."""

from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.woven_costing.business.discount_business import DiscountBusiness
from backend.features.woven_costing.business.norm_lookup_business import NormLookupBusiness
from backend.features.woven_costing.business.numbers import ONE, ZERO, div, num, same_text
from backend.features.woven_costing.constants import (
    BLENDED,
    CHEMICAL_BASE_WEIGHT,
    CONTACT_TCDN,
    TCDN_AUX_WORKSHOP,
    TCDN_CHECK_BEFORE_WR,
    TCDN_CHECK_BEFORE_WR_STAGE,
    TCDN_COLORS,
    TCDN_CPB,
    TCDN_MERCERIZING,
    TCDN_PRICED_STAGES,
    TCDN_STANDARD_PREFIX,
    TCDN_SUSE,
    TCDN_WEIGHT_GROUP_LIMIT,
    TCDN_WR,
)
from backend.features.woven_costing.models.cost_items import CostItems
from backend.features.woven_costing.models.costing_context import CostingContext
from backend.features.woven_costing.models.costsheet_input import TcdnStageInput
from backend.features.woven_costing.models.costsheet_result import CostWarning, DyeingLine, DyeingOutcome
from backend.features.woven_costing.models.enums import NO_DYEING_FORMS, ExtraCostType
from backend.features.woven_costing.models.parameter_set import APPLIED_TCDN
from backend.features.woven_costing.models.parameter_tables import DiscountPick

STANDARD = "Nhuộm tiêu chuẩn"
OUTSIDE = "Ngoài QT tiêu chuẩn"
FEATURE = "Tính năng đặc biệt"
EXTRA = "Chi phí phát sinh"
OUTSOURCE = "Gia công ngoài"


def contact_warning(name: str) -> CostWarning:
    """BR-25: a chemical price still missing ("liên hệ TCDN"): calculated as 0, warning only."""
    return CostWarning(code="BR-25", message=f"Thiếu giá hóa chất cho {name}: đang tính 0 ({CONTACT_TCDN}).")


def _missing(name: str) -> CostWarning:
    return CostWarning(
        code="BR-25",
        message=f"Định mức nhuộm {name} không có trong bảng tra. Kiểm tra lại thông tin nhập.",
        blocking=True,
    )


class DyeingTcdnBusiness(BaseBusiness[CostingContext]):
    def __init__(self, context: CostingContext) -> None:
        self.context = context
        self.lookup = NormLookupBusiness(context.tables)
        self.sheet = context.costsheet
        self.input = context.costsheet.tcdn_dyeing
        specs = context.costsheet.fabric_snapshot.specs
        self.g_per_m = num(specs.greige_g_per_m)
        self.gsm = num(specs.greige_gsm)

    def has_standard(self) -> bool:
        return bool(self.input.dye_material and self.input.color_level)

    def has_extra_cost(self) -> bool:
        extra = self.input.extra_cost
        return extra is not None and extra.items.total > 0

    def stage_loss(self, name: str) -> Decimal:
        row = self.lookup.tcdn_process(name, self.input.dye_material)
        return row.loss_rate if row is not None else ZERO

    def dye_loss(self) -> Decimal:
        """BR-17 (TCDN): extra cost -> extra_cost_loss_rate; else standard loss (when material + colour chosen) +
        losses of the stages outside the standard process (WR included) + losses of the outside processing."""
        if self.sheet.sale_form in NO_DYEING_FORMS:
            return ZERO
        if self.has_extra_cost():
            return num(self.input.extra_cost_loss_rate)
        loss = self.context.params.tcdn_standard_dye_loss if self.has_standard() else ZERO
        names = [s.name for s in self.input.extra_stages if s.name]
        if self.input.wr_chemical:  # fix 2026-11-25: row "Kiểm trước WR" counts, the 1% tenter loss of WR does not
            names.append(TCDN_CHECK_BEFORE_WR_STAGE)
        loss += sum((self.stage_loss(n) for n in names), ZERO)
        return loss + sum((num(o.loss_rate) for o in self.input.outsourcing_lines if o.name or o.amount), ZERO)

    def discount(self) -> DiscountPick:
        """BR-25 (2026-11-25): hệ số TCDN h from the 4.6.1 Nhuộm TCDN rows by order meters ("Nhuộm" when material and
        colour are chosen or the extra cost is Nhuộm, otherwise "Partial")."""
        dyeing = self.has_standard() or self.input.extra_cost_type == ExtraCostType.DYEING
        return DiscountBusiness().tcdn(self.context.discount_tables(), num(self.sheet.order_meters), dyeing)

    def factor(self) -> Decimal:
        """BR-25 hệ số TCDN h (BR-46 override when typed)."""
        overridden = self.context.applied_overrides.get(APPLIED_TCDN)
        return overridden if overridden is not None else self.discount().factor

    def per_weight(self, cost: Decimal) -> Decimal:
        """Chemical prices are for a fabric of 250 g/m: / 250 x g/m greige."""
        return cost / CHEMICAL_BASE_WEIGHT * self.g_per_m

    def standard(self, shrink: Decimal, warnings: list[CostWarning]) -> CostItems | None:
        """BR-25 (a): row "Nhuộm tiêu chuẩn-<NL>-<cấp màu>" (Blended = sum of ratio x colour rows);
        chemical = (special dye price or table) / (1 - co) / 250 x g/m; other items / (1 - co)."""
        material, color = self.input.dye_material, self.input.color_level
        if color == BLENDED:
            ratios = [num(r) for r in self.input.blend_ratios]
            if abs(sum(ratios, ZERO) - ONE) > Decimal("0.0001"):
                return None
            base = CostItems()
            for ratio, level in zip(ratios, TCDN_COLORS, strict=False):
                row = self.lookup.tcdn_process(f"{TCDN_STANDARD_PREFIX}-{material}-{level}")
                if row is not None:
                    base = base.plus(row.items.scaled(ratio))
                elif ratio:
                    warnings.append(_missing(f"{material}-{level}"))
        else:
            row = self.lookup.tcdn_process(f"{TCDN_STANDARD_PREFIX}-{material}-{color}")
            if row is None:
                warnings.append(_missing(f"{TCDN_STANDARD_PREFIX}-{material}-{color}"))
                return None
            base = row.items
        items = base.model_copy(update={"chemical": ZERO}).scaled(div(ONE, ONE - shrink))
        return items.model_copy(update={"chemical": self.standard_chemical(base.chemical, shrink)})

    def standard_chemical(self, table_chemical: Decimal, shrink: Decimal) -> Decimal:
        """BR-25 (a): (special dye price or table) / (1 - co) / 250 x g/m."""
        chemical = num(self.input.special_dye_chemical_price) if self.input.special_dye else table_chemical
        return self.per_weight(div(chemical, ONE - shrink))

    def wr(self, shrink: Decimal, warnings: list[CostWarning]) -> tuple[CostItems, Decimal] | None:
        """BR-25 (b): chemical = HoaChat[WR chemical, group 1 if g/m2 greige <= 150 else 2] / 250 x g/m / (1 - co);
        items = row "WR" / (1 - co) / (1 - loss)."""
        group = "1" if self.gsm <= TCDN_WEIGHT_GROUP_LIMIT else "2"
        chem = self.lookup.tcdn_chemical(self.input.wr_chemical, group)
        row = self.lookup.tcdn_process(TCDN_WR)
        if chem is None or row is None:
            warnings.append(_missing(f"{self.input.wr_chemical} (nhóm {group})"))
            return None
        loss = row.loss_rate
        items = row.items.model_copy(update={"chemical": ZERO}).scaled(div(div(ONE, ONE - shrink), ONE - loss))
        return items.model_copy(update={"chemical": div(self.per_weight(chem.cost), ONE - shrink)}), loss

    def stage_cost(
        self, stage: TcdnStageInput, shrink: Decimal, warnings: list[CostWarning]
    ) -> tuple[CostItems, Decimal] | None:
        return self.extra_stage(stage.name, stage.chemical_price, shrink, warnings)

    def extra_stage(
        self, name: str, price: Decimal | None, shrink: Decimal, warnings: list[CostWarning]
    ) -> tuple[CostItems, Decimal] | None:
        """BR-25 (c): one stage outside the standard process (chemical rule by stage, items / (1 - co) / (1 - t);
        "Phụ trợ" stages are not divided by (1 - co))."""
        material = self.input.dye_material
        row = self.lookup.tcdn_process(name, material)
        if row is None:
            warnings.append(_missing(name))
            return None
        loss = row.loss_rate
        div_co = ONE if row.workshop == TCDN_AUX_WORKSHOP else ONE - shrink
        if same_text(name, TCDN_CPB):
            chem_row = self.lookup.tcdn_chemical(f"{TCDN_CPB} {material}")
            chemical = self.per_weight(chem_row.cost) if chem_row else ZERO
        elif any(name.strip().casefold().startswith(s.casefold()) for s in TCDN_PRICED_STAGES):
            chemical = num(price)
            if price is None:
                warnings.append(contact_warning(name))
        elif name.strip().casefold().startswith(TCDN_SUSE.casefold()):
            chem_row = self.lookup.tcdn_chemical(TCDN_SUSE)
            chemical = self.per_weight(chem_row.cost) if chem_row else ZERO
        elif same_text(name, TCDN_MERCERIZING):
            chem_row = self.lookup.tcdn_chemical(TCDN_MERCERIZING)
            chemical = self.per_weight(chem_row.cost) if chem_row else ZERO
        else:
            chemical = self.per_weight(div(row.items.chemical, div_co))
        scale = div(div(ONE, div_co), ONE - loss)
        items = row.items.model_copy(update={"chemical": ZERO}).scaled(scale)
        return items.model_copy(update={"chemical": div(chemical, ONE - loss)}), loss

    def calculate(self, shrink: Decimal, finished_m_per_kg: Decimal) -> DyeingOutcome:
        """BR-25: every line đ/m = (chemical + items) x h; with an extra cost the total = extra cost + outside
        processing only. Per kg = per m x m/kg TP."""
        if self.sheet.sale_form in NO_DYEING_FORMS:
            return DyeingOutcome()
        h = self.factor()
        warnings: list[CostWarning] = []
        lines: list[DyeingLine] = []

        def add(group: str, name: str, items: CostItems, loss: Decimal = ZERO, note: str = "") -> None:
            per_m = items.total * h
            lines.append(DyeingLine(group=group, name=name, items=items, factor=h, loss_rate=loss, per_m=per_m,
                                    per_kg=per_m * finished_m_per_kg, note=note))  # fmt: skip

        if not self.has_extra_cost():
            if self.has_standard():
                items = self.standard(shrink, warnings)
                name = f"{TCDN_STANDARD_PREFIX}-{self.input.dye_material}-{self.input.color_level}"
                if items is not None:
                    add(STANDARD, name, items, self.context.params.tcdn_standard_dye_loss)
            if self.input.wr_chemical:
                found = self.wr(shrink, warnings)
                if found is not None:
                    add(OUTSIDE, f"WR - {self.input.wr_chemical}", found[0], found[1])
                # fix 2026-11-25: the costsheet file adds "Kiểm trước WR" (Kiểm Trung Gian) whenever WR is chosen
                check = self.stage_cost(TcdnStageInput(name=TCDN_CHECK_BEFORE_WR_STAGE), shrink, warnings)
                if check is not None:
                    add(OUTSIDE, TCDN_CHECK_BEFORE_WR, check[0], check[1])
            for stage in [s for s in self.input.extra_stages if s.name]:
                found = self.stage_cost(stage, shrink, warnings)
                if found is not None:
                    add(OUTSIDE, stage.name, found[0], found[1])
            for feature in [f for f in self.input.special_features if f.name]:
                if feature.amount is None:
                    warnings.append(contact_warning(feature.name))
                add(
                    FEATURE,
                    feature.name,
                    CostItems(chemical=num(feature.amount)),
                    note=CONTACT_TCDN if feature.amount is None else "",
                )
        else:
            extra = self.input.extra_cost
            if extra is not None:
                add(EXTRA, extra.name or EXTRA, extra.items, num(self.input.extra_cost_loss_rate))
        for line in [o for o in self.input.outsourcing_lines if o.name or o.amount]:
            add(OUTSOURCE, line.name, CostItems(material=num(line.amount)), num(line.loss_rate))
        per_m = sum((line.per_m for line in lines), ZERO)
        items = CostItems()
        for line in lines:
            items = items.plus(line.items.scaled(h))
        return DyeingOutcome(
            lines=lines, per_m=per_m, per_kg=per_m * finished_m_per_kg, items_per_m=items, factor=h, warnings=warnings
        )
