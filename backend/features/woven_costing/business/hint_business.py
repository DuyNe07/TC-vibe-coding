"""BR-05 yarn ratio, BR-06 Se hint, BR-07..BR-09 Hồ hint: building the yarn lines of a costsheet; BR-86 Se lines
suggested from the yarn lines ticked Se, BR-83 fiber system suggestion of the Se lines (cone: cone_business, BR-100)."""

import re
from collections.abc import Sequence
from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.woven_costing.business.count_business import CountBusiness
from backend.features.woven_costing.constants import (
    FILAMENT_WORDS,
    RATIO_TOLERANCE,
    SIZE_FILAMENT_WORDS,
    SIZE_NAME_WORDS,
    SPUN_SIZE_COUNT,
)
from backend.features.woven_costing.models.costsheet import FabricSnapshot
from backend.features.woven_costing.models.costsheet_input import TwistLine, YarnLine
from backend.features.woven_costing.models.enums import YarnDirection, YarnKind
from backend.features.woven_costing.models.fabric import FabricYarn
from backend.shared.utils import strip_accents

ONE = Decimal(1)
ZERO = Decimal(0)
TWIST_DIRECTION = {YarnDirection.WARP: "Dọc", YarnDirection.WEFT: "Ngang"}
WEFT_TWIST = "Ngang"
QTY_TOLERANCE = Decimal("0.0001")  # kg: a suggested quantity sent back through the screen is still "not edited"
REASON_NAME = "Tên vải có HO"
REASON_SPUN_COUNT = "Sợi spun chi số ≥ 50"
REASON_SPUN_PLAIN = "Sợi spun không se"
REASON_FILAMENT = "Filament SIM/NIM"
_HO = re.compile(r"(?<![A-Z])HO(?![A-Z])")
_FILAMENT_COUNT = re.compile(r"\d\s*D(?![A-Z])|\d\s*D/")
_SPUN_COUNT = re.compile(r"(\d+(?:\.\d+)?)\s*/")


class YarnRatioRule(BaseBusinessRule[Decimal]):
    """Target = total ratio of every yarn line (0..1)."""

    code = "BR-05"
    message = "Tỷ lệ sợi không đúng. Vui lòng kiểm tra lại mã vải với SO / PD."
    field = "yarn_lines"

    def is_satisfied_by(self, target: Decimal) -> bool:
        return abs(target - ONE) <= RATIO_TOLERANCE

    def describe_violation(self, target: Decimal) -> str:
        return f"Tỷ lệ sợi không đúng (tổng = {target * 100:.2f}%). Vui lòng kiểm tra lại mã vải với SO / PD."


class HintBusiness(BaseBusiness[Decimal]):
    def rules(self) -> Sequence[BaseBusinessRule[Decimal]]:
        return (YarnRatioRule(),)

    def twist_suggested(self, yarn: FabricYarn) -> bool:
        """BR-06: a yarn with a twist (T/M) is suggested as Se."""
        return bool(yarn.twist_tpm.strip())

    def name_needs_size(self, fabric_name: str) -> bool:
        """BR-07: the fabric name has HO as a separate word, or SIMHO / HOSOI."""
        upper = strip_accents(fabric_name).upper()
        return bool(_HO.search(upper)) or any(word in upper for word in SIZE_NAME_WORDS)

    def is_filament(self, names: str) -> bool:
        """BR-08: filament when a number is followed by D (75D, 150D/48F) or the name has DTY, FDY, ATY, POY, NYLON."""
        return bool(_FILAMENT_COUNT.search(names)) or any(word in names for word in FILAMENT_WORDS)

    def spun_count(self, raw_yarn_name: str) -> Decimal | None:
        """BR-08: count = number before the first "/" of the raw yarn name (TC 50/1 -> 50)."""
        found = _SPUN_COUNT.search(raw_yarn_name.upper())
        return Decimal(found.group(1)) if found else None

    def warp_size_reasons(self, warp_yarns: list[FabricYarn]) -> list[str]:
        """BR-08 (a) spun count >= 50, (b) spun single yarn without twist, (c) filament SIM / NIM."""
        reasons: list[str] = []
        for yarn in warp_yarns:
            names = f"{yarn.yarn_name} {yarn.raw_yarn_name}".upper()
            if self.is_filament(names):
                if any(word in names for word in SIZE_FILAMENT_WORDS):
                    reasons.append(REASON_FILAMENT)
                continue
            count = self.spun_count(yarn.raw_yarn_name or yarn.yarn_name)
            if count is not None and count >= SPUN_SIZE_COUNT:
                reasons.append(REASON_SPUN_COUNT)
            if yarn.yarn_kind != YarnKind.TWISTED and not yarn.twist_tpm.strip():
                reasons.append(REASON_SPUN_PLAIN)
        return list(dict.fromkeys(reasons))

    def size_reason(self, snapshot: FabricSnapshot) -> str:
        """BR-07 + BR-08: why the app suggests Hồ ("" = no suggestion)."""
        reasons = [REASON_NAME] if self.name_needs_size(snapshot.fabric_name) else []
        warp = [y for y in snapshot.yarns if y.direction == YarnDirection.WARP]
        reasons += self.warp_size_reasons(warp)
        return "; ".join(dict.fromkeys(reasons))

    def build_yarn_lines(self, snapshot: FabricSnapshot, previous: list[YarnLine] | None = None) -> list[YarnLine]:
        """BR-05 ratio = rate x raw_rate / 10000, BR-06 Se hint, BR-09 Hồ on every warp line when suggested.

        Lines of ``previous`` with the same direction, sequence and yarn keep what sales typed (price, ticks)."""
        reason = self.size_reason(snapshot)
        kept = {(line.direction, line.seq, line.yarn_name): line for line in previous or []}
        lines = []
        for yarn in snapshot.yarns:
            name = yarn.raw_yarn_name or yarn.yarn_name
            base = YarnLine(
                direction=yarn.direction,
                seq=yarn.seq,
                yarn_name=name,
                source_yarn_name=yarn.yarn_name,
                yarn_kind=yarn.yarn_kind,
                twist_tpm=yarn.twist_tpm,
                ratio=yarn.ratio,
                is_twisted=self.twist_suggested(yarn),
                is_sized=bool(reason) and yarn.direction == YarnDirection.WARP,
                size_suggest_reason=reason if yarn.direction == YarnDirection.WARP else "",
            )
            old = kept.get((yarn.direction, yarn.seq, name))
            if old is not None:
                base = base.model_copy(
                    update={
                        "price_currency": old.price_currency,
                        "price_input": old.price_input,
                        "price_entered_on": old.price_entered_on,
                        "waste_rate": old.waste_rate,
                        "is_twisted": old.is_twisted,
                        "is_sized": old.is_sized and yarn.direction == YarnDirection.WARP,
                    }
                )
            lines.append(base)
        return lines

    def ratio_total(self, lines: list[YarnLine]) -> Decimal:
        return sum((line.ratio for line in lines), Decimal(0))

    def suggest_twist_lines(self, lines: list[YarnLine], estimates: dict[tuple[str, int], Decimal]) -> list[TwistLine]:
        """BR-86: one Se line per (direction, count, twist) of the yarn lines ticked Se. Direction Dọc / Ngang, twist =
        number before "T/M", count read from the yarn name ("" when not readable), fiber system by BR-83, quantity =
        estimated Se output (BR-19) of the yarn lines of the group (``estimates`` by (direction, seq))."""
        counts = CountBusiness()
        groups: dict[tuple[str, str, int | None], Decimal] = {}
        for line in lines:
            if not line.is_twisted:
                continue
            count = counts.count_from_yarn_name(line.yarn_name or line.source_yarn_name)
            twist = counts.twist_from_text(line.twist_tpm) or counts.twist_in_name(line.source_yarn_name)
            key = (TWIST_DIRECTION[line.direction], count, twist)
            groups[key] = groups.get(key, Decimal(0)) + estimates.get((line.direction.value, line.seq), Decimal(0))
        return [
            TwistLine(
                direction=direction,
                count=count,
                twist=twist,
                quantity_kg=quantity,
                fiber_system=counts.suggest_fiber(count),
                fiber_suggested=bool(count),
                suggested=True,
                suggestion_key=self.twist_key(direction, count, twist),
            )  # fmt: skip
            for (direction, count, twist), quantity in groups.items()
        ]

    def twist_key(self, direction: str, count: str, twist: int | None) -> str:
        """BR-86: one suggestion = one (direction, count, twist) group."""
        return f"{direction}|{count}|{'' if twist is None else twist}"

    def still_suggestion(self, line: TwistLine, offered: TwistLine | None) -> bool:
        """BR-86: a line is still the app suggestion when it says so and no cell differs from what was suggested."""
        if not line.suggested or offered is None:
            return False
        same_qty = abs((line.quantity_kg or ZERO) - (offered.quantity_kg or ZERO)) <= QTY_TOLERANCE
        return (
            same_qty
            and line.direction == offered.direction
            and line.count == offered.count
            and line.twist == offered.twist
            and line.fiber_system == offered.fiber_system
        )

    def merge_twist_lines(
        self, lines: list[TwistLine], offered: list[TwistLine], skips: list[str], fresh: list[TwistLine]
    ) -> tuple[list[TwistLine], list[str]]:
        """BR-86 (2026-11-23): lines still suggested are replaced by the ``fresh`` suggestion of the same group (or
        dropped when the group is gone); lines typed / edited by sales are kept; a suggestion sales deleted (offered
        last time, missing now) or edited is never suggested again (``skips``); new groups are appended.
        Returns (lines, skips)."""
        by_key = {o.suggestion_key: o for o in offered if o.suggestion_key}
        present = {line.suggestion_key for line in lines if line.suggestion_key}
        skipped = set(skips) | (set(by_key) - present)
        still = [self.still_suggestion(line, by_key.get(line.suggestion_key)) for line in lines]
        skipped |= {line.suggestion_key for line, s in zip(lines, still, strict=True) if not s and line.suggestion_key}
        fresh_by_key = {f.suggestion_key: f for f in fresh if f.suggestion_key not in skipped}
        merged: list[TwistLine] = []
        for line, is_suggestion in zip(lines, still, strict=True):
            if not is_suggestion:
                merged.append(line.model_copy(update={"suggested": False}) if line.suggested else line)
            elif line.suggestion_key in fresh_by_key:
                merged.append(fresh_by_key.pop(line.suggestion_key))
        merged += list(fresh_by_key.values())
        return merged, sorted(skipped)

    def fill_fiber_systems(self, lines: list[TwistLine]) -> list[TwistLine]:
        """BR-83: an empty fiber system, or one that is still the app suggestion, follows the count."""
        counts = CountBusiness()
        filled = []
        for line in lines:
            if line.fiber_system is None or line.fiber_suggested:
                suggested = counts.suggest_fiber(line.count)
                line = line.model_copy(
                    update={"fiber_system": suggested or line.fiber_system, "fiber_suggested": suggested is not None}
                )
            filled.append(line)
        return filled
