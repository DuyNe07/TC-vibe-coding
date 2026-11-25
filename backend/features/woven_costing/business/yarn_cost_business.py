"""BR-11 warp loss, BR-12 weft loss, BR-19 yarn cost and estimated Se output, BR-21 Se quantity check, BR-45 USD."""

from collections.abc import Sequence
from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.woven_costing.business.numbers import ONE, ZERO, div, num
from backend.features.woven_costing.constants import TWIST_TOLERANCE, WEFT_WIDTH_HIGH, WEFT_WIDTH_LOW, WEFT_WIDTH_MID
from backend.features.woven_costing.models.checks import TwistQuantity
from backend.features.woven_costing.models.costsheet_input import YarnLine
from backend.features.woven_costing.models.costsheet_result import YarnLineResult
from backend.features.woven_costing.models.enums import Currency, YarnDirection
from backend.features.woven_costing.models.parameter_set import ParameterValues


class TwistQuantityRule(BaseBusinessRule[TwistQuantity]):
    code = "BR-21"
    message = "Tổng sản lượng Se nhập khác sản lượng Se ước tính. Vui lòng kiểm tra lại."
    field = "twist_lines"

    def is_satisfied_by(self, target: TwistQuantity) -> bool:
        return abs(target.entered - target.estimated) <= TWIST_TOLERANCE

    def describe_violation(self, target: TwistQuantity) -> str:
        return (
            f"Tổng sản lượng Se nhập ({target.entered:.2f} kg) khác sản lượng Se ước tính "
            f"({target.estimated:.2f} kg). Vui lòng kiểm tra lại."
        )


class YarnCostBusiness(BaseBusiness[TwistQuantity]):
    def rules(self) -> Sequence[BaseBusinessRule[TwistQuantity]]:
        return (TwistQuantityRule(),)

    def price_vnd(self, line: YarnLine, rate: Decimal) -> Decimal:
        """BR-45: price typed in USD x exchange rate of the costsheet."""
        price = num(line.price_input)
        return price * rate if line.price_currency == Currency.USD else price

    def warp_loss(self, line: YarnLine, p: ParameterValues) -> Decimal:
        """BR-11: base + twist x (Se) + size x (Hồ). Example 0.82% + 1% + 2.06% = 3.88%."""
        twist = p.warp_loss_twist if line.is_twisted else ZERO
        size = p.warp_loss_size if line.is_sized else ZERO
        return p.warp_loss_base + twist + size

    def weft_loss(self, width: Decimal, twisted: bool, p: ParameterValues) -> Decimal:
        """BR-12: linear interpolation of the weft loss by greige width (130 / 175 / 215 cm) and Se."""
        if twisted:
            low, mid, high = p.weft_loss_twist_130, p.weft_loss_twist_175, p.weft_loss_twist_215
        else:
            low, mid, high = p.weft_loss_plain_130, p.weft_loss_plain_175, p.weft_loss_plain_215
        if width == WEFT_WIDTH_MID:
            return mid
        if width < WEFT_WIDTH_MID:
            return low - (low - mid) / (WEFT_WIDTH_MID - WEFT_WIDTH_LOW) * (width - WEFT_WIDTH_LOW)
        return mid - (mid - high) / (WEFT_WIDTH_HIGH - WEFT_WIDTH_MID) * (width - WEFT_WIDTH_MID)

    def line_loss(self, line: YarnLine, width: Decimal, p: ParameterValues) -> Decimal:
        if line.direction == YarnDirection.WARP:
            return self.warp_loss(line, p)
        return self.weft_loss(width, line.is_twisted, p)

    def line_cost(
        self, line: YarnLine, greige_kg: Decimal, width: Decimal, rate: Decimal, p: ParameterValues
    ) -> YarnLineResult:
        """BR-19: yarn kg = kg greige x ratio / (1 - loss) / (1 - waste);
        amount = yarn kg x price - kg greige x ratio x waste x waste price;
        Se output (Se lines) = ratio x kg greige / (1 - (loss + waste - offset))."""
        loss = self.line_loss(line, width, p)
        waste = line.waste_rate
        yarn_kg = div(div(greige_kg * line.ratio, ONE - loss), ONE - waste)
        amount = yarn_kg * self.price_vnd(line, rate) - greige_kg * line.ratio * waste * p.yarn_waste_price
        twist = div(line.ratio * greige_kg, ONE - (loss + waste - p.twist_loss_offset)) if line.is_twisted else ZERO
        return YarnLineResult(
            direction=line.direction,
            seq=line.seq,
            loss_rate=loss,
            yarn_kg=yarn_kg,
            amount=amount,
            twist_estimate_kg=twist,
        )
