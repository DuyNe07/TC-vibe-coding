"""BR-22 weaving department costs (Se, Mắc Hồ, Mắc phân băng, Cone, Dệt, Kiểm, gia công) and the BR-23 total."""

from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.woven_costing.business.count_business import CountBusiness
from backend.features.woven_costing.business.norm_lookup_business import NormLookupBusiness
from backend.features.woven_costing.business.numbers import ONE, ZERO, div, num, round_half_up, round_up
from backend.features.woven_costing.business.twist_business import TwistBusiness
from backend.features.woven_costing.constants import (
    COUNT_DIVISOR,
    STAGE_CHECK_DYE,
    STAGE_CHECK_GREIGE,
    STAGE_CONE,
    STAGE_WARPING,
    TEN,
)
from backend.features.woven_costing.models.cost_items import CostItems
from backend.features.woven_costing.models.costing_context import CostingContext
from backend.features.woven_costing.models.costsheet_result import (
    CostWarning,
    StageCost,
    TwistLineResult,
    WeavingOutcome,
)
from backend.features.woven_costing.models.enums import NO_DYEING_FORMS, NO_WEAVING_FORMS, FactorStage, YarnDirection

MISSING_NORM = "Định mức {stage} không có trong bảng tra. Kiểm tra lại thông tin nhập."
YES = "Có"
WEFT_TWIST = "Ngang"
_GROUPS_HIGH = ("NYLON", "ATY", "FDY/ITY")


def _missing(stage: str) -> CostWarning:
    return CostWarning(code="BR-22", message=MISSING_NORM.format(stage=stage), blocking=True)


class WeavingBusiness(BaseBusiness[CostingContext]):
    def __init__(self, context: CostingContext) -> None:
        self.context = context
        self.lookup = NormLookupBusiness(context.tables)
        self.sheet = context.costsheet
        self.params = context.params

    def _factor(self, items: CostItems, stage: FactorStage) -> CostItems:
        return self.lookup.apply_factors(items, stage, self.sheet.tcfno, self.sheet.costing_date, self.context.factors)

    def warp_ends(self) -> Decimal:
        """BR-22: tổng canh = warp density greige / 10 x greige width."""
        specs = self.sheet.fabric_snapshot.specs
        return num(specs.greige_warp_density) / TEN * num(specs.greige_width_cm)

    def size_band(self, material: str, ends: Decimal) -> str:
        """4.5.4 warp-end group of the size material."""
        upper = material.strip().upper()
        if upper in _GROUPS_HIGH:
            bands = ((12000, ">12000"), (11000, "11000:12000"), (10000, "10000:11000"), (9000, "9000:10000"))
            return next((label for limit, label in bands if ends > limit), "<9000")
        if upper == "DTY":
            bands = ((11000, ">11000"), (9000, "9000:11000"), (7000, "7000:9000"), (5000, "5000:7000"))
            return next((label for limit, label in bands if ends > limit), "<5000")
        if ends < 5000:
            return "<5000"
        return ">7000" if ends > 7000 else "5000:7000"

    def warping_meters(self, greige_meters: Decimal) -> Decimal:
        """BR-22: greige meters / (1 - warping extra loss) / (1 - warping loss of the fabric)."""
        loss = self.sheet.fabric_snapshot.specs.warping_loss_rate
        return div(div(greige_meters, ONE - self.params.warping_extra_loss), ONE - loss)

    def twist_lines(self, warnings: list[CostWarning]) -> list[TwistLineResult]:
        """BR-20 norms of every Se line (4.13); BR-81 / BR-82 / BR-84 errors are blocking warnings (BR-80)."""
        twist = TwistBusiness()
        counts = CountBusiness(self.context.tables)
        results = []
        for line in self.sheet.twist_lines:
            if not line.count and not line.quantity_kg:
                continue
            errors = self.count_errors(line.count) if line.count else []
            twist_error = counts.twist_violation(line.twist)
            if twist_error is not None:
                errors.append(CostWarning(code=twist_error.rule_code, message=twist_error.message, blocking=True))
            norm = CostItems()
            if not errors:
                found = twist.twist_norm(line, self.lookup)
                if found is None:
                    errors.append(CostWarning(code="BR-20", message=MISSING_NORM.format(stage=f"Se {line.count}"),
                                              blocking=True))  # fmt: skip
                else:
                    norm = self._factor(found, FactorStage.TWIST)
            warnings.extend(errors)
            error = " ".join(e.message for e in errors)
            qty = num(line.quantity_kg)
            results.append(
                TwistLineResult(
                    direction=line.direction,
                    count=line.count,
                    quantity_kg=qty,
                    norm=norm,
                    amount=qty * norm.total,
                    error=error,
                )  # fmt: skip
            )
        return results

    def count_errors(self, count: str) -> list[CostWarning]:
        """BR-81 / BR-84: a count that cannot be converted gives one blocking warning (BR-80)."""
        converted = CountBusiness(self.context.tables).convert(count)
        if converted.ok:
            return []
        return [CostWarning(code=converted.error_code, message=converted.error, blocking=True)]

    def cone_norm(self, count: str) -> CostItems | None:
        """BR-22: Cone item = CONE rate x 9 000 000 / (speed x spindles x converted count) per kg."""
        stage = self.lookup.minute_rate(STAGE_CONE)
        converted = self.lookup.twist_converted(count)
        if stage is None or converted is None:
            return None
        return stage.rates.scaled(div(COUNT_DIVISOR, stage.speed * stage.spindles * converted))

    def warping_norm(self, ends: Decimal) -> CostItems | None:
        """BR-22 Mắc phân băng: beats = roundup(ends x standard beats / standard ends); time = beats /
        (MAC speed x reel); item = MAC rate x time x twist factor (1.97 when a warp yarn is ticked Se)."""
        stage = self.lookup.minute_rate(STAGE_WARPING)
        check = self.lookup.tables.warp_check
        if stage is None:
            return None
        beats = round_up(div(ends * check.standard_beats, check.standard_ends))
        minutes = div(beats, stage.speed * stage.reel)
        twisted = any(y.is_twisted for y in self.sheet.yarn_lines if y.direction == YarnDirection.WARP)
        return stage.rates.scaled(minutes * (check.twist_factor if twisted else ONE))

    def check_norm(self) -> CostItems | None:
        """BR-22 Kiểm: rate of KIEM HANG_1 (Mộc) or KIEM HANG_2 / checking speed (m/minute)."""
        greige = self.sheet.sale_form in NO_DYEING_FORMS
        stage = self.lookup.minute_rate(STAGE_CHECK_GREIGE if greige else STAGE_CHECK_DYE)
        check = self.lookup.tables.warp_check
        speed = check.check_speed_greige if greige else check.check_speed_dye
        if stage is None or speed == 0:
            return None
        return stage.rates.scaled(ONE / speed)

    def calculate(self, greige_meters: Decimal, greige_bc: Decimal, quantity_factor: Decimal) -> WeavingOutcome:
        """BR-22 + BR-23: Chi phí ngành Dệt = Se + gia công Se, Hồ, Dệt, khác + (Mắc Hồ + Mắc phân băng + Cone +
        Dệt + Kiểm) x hệ số số lượng. Vải Nhuộm: everything is 0."""
        warnings: list[CostWarning] = []
        twist_lines = self.twist_lines(warnings)
        if self.sheet.sale_form in NO_WEAVING_FORMS:  # Vải Nhuộm, Gia công nhuộm (BR-90)
            return WeavingOutcome(twist_lines=twist_lines, warnings=warnings)
        weave = self.sheet.weaving
        length = greige_meters
        warping = self.warping_meters(length)
        ends = self.warp_ends()
        stages: list[StageCost] = []
        per_unit = {}  # stage -> (items, quantity, factor) for the per-meter breakdown

        def add(
            name: str, qty: Decimal, unit: str, items: CostItems | None, factor: Decimal, price: Decimal = ZERO
        ) -> None:
            norm = items.total if items is not None else price
            stages.append(StageCost(stage=name, quantity=qty, unit=unit, norm=norm, factor_applied=factor,
                                    amount=qty * norm * factor))  # fmt: skip
            if items is not None:
                per_unit[name] = (items, qty, factor)

        twist_qty = sum((t.quantity_kg for t in twist_lines), ZERO)
        twist_amount = sum((t.amount for t in twist_lines), ZERO)
        stages.append(StageCost(stage="Se", quantity=twist_qty, unit="kg", norm=div(twist_amount, twist_qty),
                                amount=twist_amount))  # fmt: skip
        add("Gia công Se", num(weave.twist_outsourcing_qty), "kg", None, ONE, num(weave.twist_outsourcing_price))
        band = ""
        if weave.size_material:
            band = self.size_band(weave.size_material, ends)
            norm = self.lookup.size_norm(weave.size_material, band)
            if norm is None:
                warnings.append(_missing(f"Mắc Hồ {weave.size_material} {band}"))
            else:
                items = self._factor(norm.items, FactorStage.SIZING)
                items = items.model_copy(update={"chemical": items.chemical * self.params.size_chemical_factor})
                add("Mắc Hồ", warping, "m", items, quantity_factor)
        add("Gia công Hồ", warping, "m", None, ONE, num(weave.size_outsourcing_price))
        if weave.warping_band == YES:
            items = self.warping_norm(ends)
            if items is None:
                warnings.append(_missing("Mắc phân băng"))
            else:
                add("Mắc phân băng", warping, "m", self._factor(items, FactorStage.WARPING), quantity_factor)
        weft_twist = sum((num(t.quantity_kg) for t in self.sheet.twist_lines if t.direction == WEFT_TWIST), ZERO)
        cones = (
            ("Cone 1", weave.cone_count_1, weave.cone_qty_1 if weave.cone_qty_1 is not None else weft_twist),
            ("Cone 2", weave.cone_count_2, weave.cone_qty_2),
        )
        for name, count, qty in cones:
            if count and num(qty) > 0:
                count_errors = self.count_errors(count)
                items = None if count_errors else self.cone_norm(count)
                if count_errors:
                    warnings.extend(count_errors)
                elif items is None:
                    warnings.append(_missing(f"Cone {count}"))
                else:
                    add(name, num(qty), "kg", self._factor(items, FactorStage.CONE), quantity_factor)
            elif num(qty) > 0:
                msg = f"{name}: có {num(qty):.2f} kg sợi cone, vui lòng nhập chi số sợi cone."
                if name == "Cone 1" and (weave.cone_qty_1 is None or weave.cone_qty_1_suggested):
                    # BR-87: the quantity is the Ngang Se total but those lines have several counts (or none)
                    msg = (
                        f"Cone 1: SL gợi ý {num(qty):.2f} kg (= tổng SL Se ngang) nhưng các dòng Se ngang không có "
                        "đúng 1 chi số, vui lòng nhập chi số sợi cone 1."
                    )
                warnings.append(CostWarning(code="BR-22", message=msg, blocking=True))
        density = int(round_half_up(num(self.sheet.fabric_snapshot.specs.greige_weft_density) / TEN))
        weave_norm = self.lookup.weave_norm(density)
        if weave_norm is None:
            warnings.append(_missing(f"Dệt (mật độ ngang {density})"))
        else:
            add("Dệt", length, "m", self._factor(weave_norm.items, FactorStage.WEAVING), quantity_factor)
        check = self.check_norm()
        if check is None:
            warnings.append(_missing("Kiểm"))
        else:
            add("Kiểm", length, "m", self._factor(check, FactorStage.CHECKING), quantity_factor)
        add("Gia công Dệt", length, "m", None, ONE, num(weave.weaving_outsourcing_price))
        add("Gia công khác", length, "m", None, ONE, num(weave.other_outsourcing_price))
        if any(y.is_sized for y in self.sheet.yarn_lines) and not weave.size_material and not weave.warping_band:
            msg = "Đã tick Hồ nhưng chưa chọn nguyên liệu hồ hoặc Mắc phân băng (Có / Không)."
            warnings.append(CostWarning(code="BR-80", message=msg, blocking=True))
        base = length * (ONE - greige_bc)
        twist_items = CostItems()
        for line in twist_lines:
            twist_items = twist_items.plus(line.norm.scaled(line.quantity_kg))
        weaving_items = CostItems()
        for items, qty, factor in per_unit.values():
            weaving_items = weaving_items.plus(items.scaled(qty * factor))
        return WeavingOutcome(
            twist_lines=twist_lines,
            stages=stages,
            total=sum((s.amount for s in stages), ZERO),
            twist_items_per_m=twist_items.scaled(div(ONE, base)),
            weaving_items_per_m=weaving_items.scaled(div(ONE, base)),
            warp_ends_total=ends,
            size_band=band,
            warping_meters=warping,
            weft_density_group=density,
            warnings=warnings,
        )
