"""UC-16 calculation: BR-10..BR-29 put together, BR-14 shrinkage check, BR-17 dyeing loss, BR-80 warnings."""

from collections.abc import Sequence
from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.woven_costing.business.discount_business import DiscountBusiness
from backend.features.woven_costing.business.dyeing_hcm_business import DyeingHcmBusiness
from backend.features.woven_costing.business.dyeing_tcdn_business import DyeingTcdnBusiness
from backend.features.woven_costing.business.hint_business import HintBusiness
from backend.features.woven_costing.business.numbers import ONE, ZERO, div, num
from backend.features.woven_costing.business.pricing_business import PricingBusiness
from backend.features.woven_costing.business.quantity_business import QuantityBusiness
from backend.features.woven_costing.business.weaving_business import WeavingBusiness
from backend.features.woven_costing.business.yarn_cost_business import YarnCostBusiness
from backend.features.woven_costing.models.checks import Check, TwistQuantity
from backend.features.woven_costing.models.costing_context import CostingContext
from backend.features.woven_costing.models.costsheet import Costsheet
from backend.features.woven_costing.models.costsheet_result import (
    AppliedParameter,
    CostItemRow,
    CostsheetResult,
    CostWarning,
    DyeingOutcome,
)
from backend.features.woven_costing.models.enums import (
    JOB_FORMS,
    NO_DYEING_FORMS,
    DyePlant,
    SaleForm,
    ShrinkageException,
    YarnDirection,
)
from backend.features.woven_costing.models.parameter_set import (
    APPLIED_FINISHED_BC,
    APPLIED_GREIGE_BC,
    APPLIED_HCM,
    APPLIED_TCDN,
    APPLIED_WEAVING,
    ParameterValues,
)
from backend.features.woven_costing.models.parameter_tables import DiscountPick


class ShrinkageReasonRule(BaseBusinessRule[Check]):
    """Target text = shrinkage in %; ok = shrinkage above the minimum, or an exception / a reason is given."""

    code = "BR-14"
    message = "Độ co không lớn hơn 5%. Vui lòng chọn lý do ngoại lệ hoặc ghi lý do."
    field = "shrinkage_reason"

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"Độ co {target.text}% không lớn hơn {target.other}%. Vui lòng chọn lý do ngoại lệ hoặc ghi lý do."


class CostingBusiness(BaseBusiness[Check]):
    def rules(self) -> Sequence[BaseBusinessRule[Check]]:
        return (ShrinkageReasonRule(),)

    def is_low_shrinkage(self, sheet: Costsheet, shrinkage: Decimal, p: ParameterValues) -> bool:
        """BR-14: not Mộc and (shrinkage <= min_shrinkage or an exception chosen) -> highlighted for the approver."""
        if sheet.sale_form is None or sheet.sale_form in NO_DYEING_FORMS:
            return False
        return shrinkage <= p.min_shrinkage or sheet.shrinkage_exception != ShrinkageException.NONE

    def shrinkage_check(self, sheet: Costsheet, shrinkage: Decimal, p: ParameterValues) -> Check:
        """BR-14: low shrinkage needs an exception (not "Không") or a written reason."""
        needs_reason = self.with_dyeing(sheet) and shrinkage <= p.min_shrinkage
        given = sheet.shrinkage_exception != ShrinkageException.NONE or bool(sheet.shrinkage_reason.strip())
        return Check(ok=not needs_reason or given, text=f"{shrinkage * 100:.2f}", other=f"{p.min_shrinkage * 100:.0f}")

    def with_dyeing(self, sheet: Costsheet) -> bool:
        """Sale form chosen and not Mộc / Gia công dệt (BR-14, BR-46, BR-89)."""
        return sheet.sale_form is not None and sheet.sale_form not in NO_DYEING_FORMS

    def dyeing(self, context: CostingContext) -> DyeingHcmBusiness | DyeingTcdnBusiness:
        if context.costsheet.dye_plant == DyePlant.TCDN:
            return DyeingTcdnBusiness(context)
        return DyeingHcmBusiness(context)

    def applied_parameters(
        self,
        context: CostingContext,
        dyeing: DyeingHcmBusiness | DyeingTcdnBusiness,
        weave: DiscountPick,
        factor: Decimal,
        finished_kg: Decimal,
    ) -> list[AppliedParameter]:
        """BR-46 (2026-11-25): discount factor applied per department (Dệt, the dyeing plant of the costsheet) with
        the row of the table it comes from."""
        rows = []
        if weave.applies:
            rows.append(AppliedParameter(code=APPLIED_WEAVING, default_value=weave.factor, used_value=factor,
                                         reason=weave.reason))  # fmt: skip
        if self.with_dyeing(context.costsheet):
            if isinstance(dyeing, DyeingTcdnBusiness):
                pick, used, code = dyeing.discount(), dyeing.factor(), APPLIED_TCDN
            else:
                pick, used, code = dyeing.discount(finished_kg), dyeing.small_lot_factor(finished_kg), APPLIED_HCM
            rows.append(AppliedParameter(code=code, default_value=pick.factor, used_value=used, reason=pick.reason))
        return rows

    def applied_bc(
        self, sheet: Costsheet, defaults: tuple[Decimal, Decimal], used: tuple[Decimal, Decimal]
    ) -> list[AppliedParameter]:
        """BR-16 / BR-46: % B/C mộc and TP of the sale form of the costsheet."""
        reason = f"Hình thức bán {(sheet.sale_form or SaleForm.FINISHED).value}"
        return [
            AppliedParameter(code=APPLIED_GREIGE_BC, default_value=defaults[0], used_value=used[0], reason=reason),
            AppliedParameter(code=APPLIED_FINISHED_BC, default_value=defaults[1], used_value=used[1], reason=reason),
        ]

    def calculate(self, context: CostingContext) -> CostsheetResult:
        """BR-10..BR-29 for one costsheet. Never raises on missing inputs: they give warnings (BR-80)."""
        sheet, p = context.costsheet, context.params
        rate = sheet.exchange_rate
        qty, yarns, pricing = QuantityBusiness(), YarnCostBusiness(), PricingBusiness()
        specs = sheet.fabric_snapshot.specs
        warnings: list[CostWarning] = []
        ratio_total = HintBusiness().ratio_total(sheet.yarn_lines)
        for violation in HintBusiness().collect_violations(ratio_total):
            warnings.append(CostWarning(code=violation.rule_code, message=violation.message, blocking=True))
        missing = qty.missing_specs(specs, sheet.sale_form)
        order_m = num(sheet.order_meters)
        if missing:
            text = ", ".join(missing)
            msg = f"Mã vải {sheet.tcfno} thiếu {text}. Liên hệ SO / PD bổ sung."
            warnings.append(CostWarning(code="BR-10", message=msg, blocking=True))
        if order_m <= 0 or missing or rate <= 0:
            return CostsheetResult(calculated=False, exchange_rate=rate, yarn_ratio_total=ratio_total, warnings=warnings,
                                   gp_threshold=p.gp_threshold, op_threshold=p.op_threshold)  # fmt: skip
        m_kg_greige = qty.meters_per_kg(specs.greige_g_per_m)
        m_kg_finished = qty.meters_per_kg(specs.finished_g_per_m)
        shrink = qty.shrinkage(sheet)
        tables, over = context.discount_tables(), context.applied_overrides
        bc_default = DiscountBusiness().bc_rates(tables, sheet.sale_form)
        greige_bc = over.get(APPLIED_GREIGE_BC, bc_default[0])
        finished_bc = over.get(APPLIED_FINISHED_BC, bc_default[1])
        dyeing = self.dyeing(context)
        dye_loss = dyeing.dye_loss()
        finished_needed = qty.finished_meters_needed(order_m, finished_bc)
        greige_m = qty.greige_meters(finished_needed, dye_loss, shrink, greige_bc, sheet.sale_form)
        greige_kg = div(greige_m, m_kg_greige)
        finished_kg = div(finished_needed, m_kg_finished)
        weave = DiscountBusiness().weaving(tables, greige_m, sheet.sale_form, sheet.order_type)
        factor = over.get(APPLIED_WEAVING, weave.factor) if weave.applies else weave.factor
        if not weave.found:
            meters = f"{greige_m:,.0f}".replace(",", ".")
            message = f"Không có hệ số sản lượng cho {meters} m mộc trong bảng discount Dệt. Liên hệ SO."
            warnings.append(CostWarning(code="BR-23", message=message))
        width = num(specs.greige_width_cm)
        lines = [yarns.line_cost(line, greige_kg, width, rate, p) for line in sheet.yarn_lines]
        if sheet.sale_form == SaleForm.WEAVING_JOB:  # BR-89: the customer gives the yarn -> kg kept, no cost
            lines = [line.model_copy(update={"amount": ZERO}) for line in lines]
        yarn_total = sum((line.amount for line in lines), ZERO)
        twist_estimated = sum((line.twist_estimate_kg for line in lines), ZERO)
        twist_entered = sum((num(t.quantity_kg) for t in sheet.twist_lines), ZERO)
        if twist_estimated > 0 or twist_entered > 0:
            target = TwistQuantity(entered=twist_entered, estimated=twist_estimated)
            for violation in yarns.collect_violations(target):
                warnings.append(CostWarning(code=violation.rule_code, message=violation.message, blocking=True))
        weaving = WeavingBusiness(context).calculate(greige_m, greige_bc, factor)
        warnings += weaving.warnings
        if isinstance(dyeing, DyeingTcdnBusiness):
            dye: DyeingOutcome = dyeing.calculate(shrink, m_kg_finished)
        else:
            dye = dyeing.calculate(finished_kg, m_kg_finished)
        warnings += dye.warnings
        dyeing_total = finished_needed * dye.per_m
        bc_liq = ZERO if sheet.sale_form in JOB_FORMS else pricing.bc_liquidation(greige_m, finished_needed, order_m, p)
        if sheet.sale_form == SaleForm.DYED:
            total = num(sheet.greige_buy_price) * greige_m + dyeing_total - bc_liq
        elif sheet.sale_form == SaleForm.DYEING_JOB:  # BR-90: the customer gives the greige
            total = dyeing_total
        elif sheet.sale_form == SaleForm.WEAVING_JOB:  # BR-89
            total = weaving.total
        else:
            total = yarn_total + weaving.total + dyeing_total - bc_liq
        unit = div(total, order_m)
        cogs_extra = pricing.cogs_extra(sheet.price)
        cogs = unit + cogs_extra
        sell = pricing.sell_price_vnd(sheet.price, rate)
        freight = pricing.effective_freight(sheet.price_type, sheet.price.freight_insurance)
        profit = pricing.profit(sell, cogs, sheet.price, freight, p)
        if sell > 0:
            warnings += pricing.threshold_warnings(profit["gp_pct"], profit["op_pct"], p)
        else:
            warnings.append(CostWarning(code="BR-42", message="Chưa nhập giá bán."))
        check = self.shrinkage_check(sheet, shrink, p)
        for violation in self.collect_violations(check):
            warnings.append(CostWarning(code=violation.rule_code, message=violation.message, blocking=True))
        base = greige_m * (ONE - greige_bc)
        applied = self.applied_parameters(context, dyeing, weave, factor, finished_kg)
        applied += self.applied_bc(sheet, bc_default, (greige_bc, finished_bc))
        return CostsheetResult(
            applied_parameters=applied,
            calculated=True,
            exchange_rate=rate,
            greige_meters=greige_m,
            finished_meters_needed=finished_needed,
            greige_kg=greige_kg,
            finished_kg=finished_kg,
            greige_m_per_kg=m_kg_greige,
            finished_m_per_kg=m_kg_finished,
            quantity_factor=factor,
            shrinkage=shrink,
            low_shrinkage=self.is_low_shrinkage(sheet, shrink, p),
            dye_loss_rate=dye_loss,
            greige_bc_rate=greige_bc,
            finished_bc_rate=finished_bc,
            yarn_ratio_total=ratio_total,
            yarn_total=yarn_total,
            twist_estimated_kg=twist_estimated,
            twist_entered_kg=twist_entered,
            warp_ends_total=weaving.warp_ends_total,
            size_band=weaving.size_band,
            warping_meters=weaving.warping_meters,
            weft_density_group=weaving.weft_density_group,
            weaving_total=weaving.total,
            weaving_cm_price=div(weaving.total, base),
            tcdn_factor=dye.factor if sheet.dye_plant == DyePlant.TCDN else ZERO,
            dyeing_per_kg=dye.per_kg,
            dyeing_per_m=dye.per_m,
            dyeing_total=dyeing_total,
            bc_liquidation=bc_liq,
            total_cost=total,
            unit_cost_vnd=unit,
            cogs_extra_total=cogs_extra,
            cogs_vnd=cogs,
            sell_price_vnd=sell,
            commission=sheet.price.commission,
            freight_insurance=freight,
            interest_cost=sheet.price.interest_cost,
            gp_threshold=p.gp_threshold,
            op_threshold=p.op_threshold,
            gp_below=sell > 0 and profit["gp_pct"] < p.gp_threshold,
            op_below=sell > 0 and profit["op_pct"] < p.op_threshold,
            yarn_lines=lines,
            twist_lines=weaving.twist_lines,
            weaving_stages=weaving.stages,
            cost_items=[
                CostItemRow(stage="Se", items=weaving.twist_items_per_m),
                CostItemRow(stage="Dệt", items=weaving.weaving_items_per_m),
                CostItemRow(stage="Nhuộm", items=dye.items_per_m),
            ],
            dyeing_lines=dye.lines,
            warnings=warnings,
            **profit,
        )

    def warp_lines_sized(self, sheet: Costsheet) -> bool:
        return any(y.is_sized for y in sheet.yarn_lines if y.direction == YarnDirection.WARP)
