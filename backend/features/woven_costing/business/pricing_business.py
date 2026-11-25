"""BR-27 total cost and COGS, BR-28 profit and thresholds, BR-29 F&I by price type."""

from collections.abc import Sequence
from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.woven_costing.business.numbers import ONE, ZERO, div, num
from backend.features.woven_costing.models.checks import Check
from backend.features.woven_costing.models.costsheet_input import PriceInput
from backend.features.woven_costing.models.costsheet_result import CostWarning
from backend.features.woven_costing.models.enums import Currency, PriceType
from backend.features.woven_costing.models.parameter_set import ParameterValues

FREIGHT_REQUIRED = (PriceType.CIF, PriceType.CIP, PriceType.CPT)
FREIGHT_HIDDEN = (PriceType.FOB, PriceType.EXW, PriceType.FCA)


class FreightRule(BaseBusinessRule[Check]):
    """Target text = price type; ok = F&I filled when required."""

    code = "BR-29"
    message = "Loại giá cần nhập chi phí vận chuyển (và bảo hiểm)."
    field = "freight_insurance"

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"Loại giá {target.text} cần nhập chi phí vận chuyển (và bảo hiểm)."


class PricingBusiness(BaseBusiness[Check]):
    def rules(self) -> Sequence[BaseBusinessRule[Check]]:
        return (FreightRule(),)

    def freight_check(self, price_type: PriceType | None, freight: Decimal) -> Check:
        """BR-29: CIF, CIP, CPT need F&I > 0."""
        ok = price_type not in FREIGHT_REQUIRED or freight > 0
        return Check(ok=ok, text=price_type.value if price_type else "")

    def effective_freight(self, price_type: PriceType | None, freight: Decimal) -> Decimal:
        """BR-29: FOB, EXW, FCA -> F&I = 0 (the field is hidden)."""
        return ZERO if price_type in FREIGHT_HIDDEN else freight

    def bc_liquidation(
        self, greige_m: Decimal, finished_needed: Decimal, order_m: Decimal, p: ParameterValues
    ) -> Decimal:
        """BR-27: (greige m - finished needed) x B/C price + (finished needed - order m) x B/C price."""
        return (greige_m - finished_needed) * p.bc_fabric_price + (finished_needed - order_m) * p.bc_fabric_price

    def sell_price_vnd(self, price: PriceInput, rate: Decimal) -> Decimal:
        """BR-28: sell price x exchange rate when typed in USD."""
        value = num(price.sell_price_input)
        return value * rate if price.sell_price_currency == Currency.USD else value

    def cogs_extra(self, price: PriceInput) -> Decimal:
        return sum((num(line.amount) for line in price.cogs_extra_lines), ZERO)

    def profit(
        self, sell: Decimal, cogs: Decimal, price: PriceInput, freight: Decimal, p: ParameterValues
    ) -> dict[str, Decimal]:
        """BR-28: GP = sell - COGS, GP% = GP / sell, S&A = COGS x S&A rate,
        OP = GP - S&A - commission - F&I - interest, OP% = OP / sell, price with VAT = sell x (1 + VAT)."""
        gp = sell - cogs
        sa = cogs * p.sa_rate
        op = gp - sa - price.commission - freight - price.interest_cost
        return {
            "gp": gp,
            "gp_pct": div(gp, sell),
            "sa": sa,
            "op": op,
            "op_pct": div(op, sell),
            "price_with_vat": sell * (ONE + p.vat_rate),
        }

    def threshold_warnings(self, gp_pct: Decimal, op_pct: Decimal, p: ParameterValues) -> list[CostWarning]:
        """BR-28: warning (not blocking) when GP% < gp_threshold or OP% < op_threshold."""
        warnings = []
        if gp_pct < p.gp_threshold:
            msg = f"GP% ({gp_pct * 100:.2f}%) thấp hơn ngưỡng {p.gp_threshold * 100:.2f}%."
            warnings.append(CostWarning(code="BR-28", message=msg))
        if op_pct < p.op_threshold:
            msg = f"OP% ({op_pct * 100:.2f}%) thấp hơn ngưỡng {p.op_threshold * 100:.2f}%."
            warnings.append(CostWarning(code="BR-28", message=msg))
        return warnings
