"""BR-20 Se norm (đ/kg) of one Se line (fiber system by BR-83, converted count by BR-81)."""

from collections.abc import Sequence
from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.woven_costing.business.count_business import CountBusiness
from backend.features.woven_costing.business.norm_lookup_business import NormLookupBusiness
from backend.features.woven_costing.business.numbers import ZERO, div, round_half_up
from backend.features.woven_costing.constants import (
    COUNT_DIVISOR,
    SIXTY,
    STAGE_SINGEING,
    STAGE_TWIST_FILAMENT,
    STAGE_TWIST_SPUN,
)
from backend.features.woven_costing.models.checks import Check
from backend.features.woven_costing.models.cost_items import CostItems
from backend.features.woven_costing.models.costsheet_input import TwistLine
from backend.features.woven_costing.models.enums import FiberSystem

TWO = Decimal(2)
SINGEING_MARK = "CB"
DENIER_MARK = "D"


class CountSystemRule(BaseBusinessRule[Check]):
    """Target text = count, other = fiber system. Since 2026-11-23 (BR-83) the calculation no longer raises this
    error (the fiber system is suggested from the count and sales may choose another one); kept for old callers."""

    code = "BR-20"
    message = "Chi số không khớp hệ sợi. Vui lòng chọn lại."
    field = "twist_lines"

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"Chi số {target.text} không khớp hệ sợi {target.other}. Vui lòng chọn lại."


class TwistBusiness(BaseBusiness[Check]):
    def rules(self) -> Sequence[BaseBusinessRule[Check]]:
        return (CountSystemRule(),)

    def count_matches(self, line: TwistLine) -> Check:
        """Old BR-20 check (Spun with a "D" in the count, or Filament without "D"); not used by the calculation
        any more (BR-83)."""
        has_d = DENIER_MARK in line.count.upper()
        system = line.fiber_system
        ok = not ((system == FiberSystem.SPUN and has_d) or (system == FiberSystem.FILAMENT and not has_d))
        return Check(ok=ok, text=line.count, other=system.value if system else "")

    def twist_norm(self, line: TwistLine, lookup: NormLookupBusiness) -> CostItems | None:
        """BR-20: Se norm per kg of one line; None when a norm is missing (count, stage).

        Yield J = (speed / twist) x spindles x minutes x (converted count / 9 000 000) x 2 (kg/day);
        run time K = minutes / J; N = prep minutes / prep output; T = run rate / rate per minute x K;
        U = prep rate / prep minutes / rate per minute x N; V = T + U; each item = V x rate of the item.
        Labor x NC factor = [hours/day / (prep minutes/60 + prep output x K / 60)] x machines
        / round(Se staff / total spindles x spindles) (as the Excel sheet DM Se 2025).
        Filament count with "CB": + singeing = 1 / (singeing speed x spindles x converted / 9 000 000) x rates."""
        system = line.fiber_system or CountBusiness().suggest_fiber(line.count)
        if system is None or not line.count or not line.twist:
            return None
        filament = system == FiberSystem.FILAMENT
        stage = lookup.minute_rate(STAGE_TWIST_FILAMENT if filament else STAGE_TWIST_SPUN)
        converted = lookup.twist_converted(line.count)
        if stage is None or converted is None:
            return None
        twist = lookup.tables.twist
        params = twist.filament if filament else twist.spun
        yield_kg = (
            div(stage.speed, Decimal(line.twist)) * stage.spindles * stage.minutes * converted / COUNT_DIVISOR * TWO
        )
        run_minutes = div(stage.minutes, yield_kg)
        prep_per_kg = div(params.prep_minutes, params.prep_output)
        per_minute = stage.rates.total
        run_share = div(params.run_rate, per_minute) * run_minutes
        prep_share = div(div(params.prep_rate, params.prep_minutes), per_minute) * prep_per_kg
        minutes = run_share + prep_share
        items = stage.rates.scaled(minutes)
        runs = div(twist.hours_per_day, params.prep_minutes / SIXTY + params.prep_output * run_minutes / SIXTY)
        total_spindles = twist.filament.spindles + twist.spun.spindles
        staff = round_half_up(div(twist.staff_total, total_spindles) * params.spindles)
        labor_factor = div(runs * params.machines, staff)
        items = items.model_copy(update={"labor": items.labor * labor_factor})
        if filament and SINGEING_MARK in line.count.upper():
            items = items.plus(self.singeing(converted, lookup))
        return items

    def singeing(self, converted: Decimal, lookup: NormLookupBusiness) -> CostItems:
        """BR-20 bấm đốt: time = 1 / (speed x spindles x converted / 9 000 000) min/kg, x rates of BẤM ĐỐT - CARBON."""
        stage = lookup.minute_rate(STAGE_SINGEING)
        if stage is None:
            return CostItems()
        minutes = div(Decimal(1), stage.speed * stage.spindles * converted / COUNT_DIVISOR)
        return stage.rates.scaled(minutes) if minutes > ZERO else CostItems()
