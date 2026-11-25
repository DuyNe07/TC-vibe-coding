"""BR-81 converted count of a free-text count, BR-82 twist range, BR-83 fiber system suggestion, BR-84 spandex,
and the count / twist read from a yarn name (used by the BR-86 Se line suggestion)."""

import re
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation

from backend.core.base import BaseBusiness, BaseBusinessRule, RuleViolation
from backend.features.woven_costing.business.numbers import same_text
from backend.features.woven_costing.constants import (
    CARBON_ADDITION,
    CARBON_MARK,
    CARBON_WORDS,
    SPANDEX_MARK,
    SPUN_COUNT_FACTOR,
    TWIST_MAX,
    TWIST_MIN,
)
from backend.features.woven_costing.models.checks import Check, CountConversion
from backend.features.woven_costing.models.enums import FiberSystem
from backend.features.woven_costing.models.norm_set import NormTables, seed_spandex
from backend.shared.utils import strip_accents

_NUM = r"\d+(?:[.,]\d+)?"
_SPACES = re.compile(r"\s+")
_FILAMENT_PART = re.compile(rf"^({_NUM})\s*D(?:\s*/\s*([1-9]))?$")
_SPUN_PART = re.compile(rf"^({_NUM})(?:\s*/\s*([1-9]))?$")
_SPANDEX_PART = re.compile(rf"^{SPANDEX_MARK}\s*({_NUM})(?:\s*/\s*[1-9])?$")
# yarn names (BR-86): filament "...<n>D/<f>F/<k>...", spun "<N>/<k>" (a blend "(65/35)" is not a count)
_NAME_FILAMENT = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*D(?![A-Z])(?:\s*/\s*\d+\s*F)?(?:\s*/\s*(\d)(?![\d.]))?")
_NAME_SPUN = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*/\s*(\d)(?![\d.%])")
_TWIST_TPM = re.compile(r"(\d+)\s*T\s*/\s*M")
_FIRST_NUMBER = re.compile(r"\d+")


def _number(text: str) -> Decimal:
    return Decimal(text.replace(",", "."))


def _plain(value: Decimal) -> str:
    """40 -> "40", 20.50 -> "20.5" (as written in a count)."""
    text = f"{value.normalize():f}"
    return text


class CountFormatRule(BaseBusinessRule[Check]):
    """Target text = the count as typed."""

    code = "BR-81"
    message = "Chi số không đúng dạng. Ví dụ đúng: 75D/2 + CB, 30/2, 45 + 75D + SP 70."
    field = "twist_lines"

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f'Chi số "{target.text}" không đúng dạng. Ví dụ đúng: 75D/2 + CB, 30/2, 45 + 75D + SP 70.'


class TwistRangeRule(BaseBusinessRule[Check]):
    """Target text = the twist as typed."""

    code = "BR-82"
    message = "Độ săn không hợp lệ: phải là số nguyên từ 50 đến 3.000 T/M."
    field = "twist_lines"

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"Độ săn {target.text} không hợp lệ: phải là số nguyên từ 50 đến 3.000 T/M."


class SpandexRule(BaseBusinessRule[Check]):
    """Target text = the spandex type (number after "SP")."""

    code = "BR-84"
    message = "Chưa có số cộng thêm cho spandex. Liên hệ SO bổ sung."
    field = "twist_lines"

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"Chưa có số cộng thêm cho spandex SP {target.text}. Liên hệ SO bổ sung."


class CountBusiness(BaseBusiness[Check]):
    def __init__(self, tables: NormTables | None = None) -> None:
        self.tables = tables

    def rules(self) -> Sequence[BaseBusinessRule[Check]]:
        return (CountFormatRule(),)

    # ---- BR-81 / BR-84 ---------------------------------------------------------------------------------------------
    def normalize(self, count: str) -> str:
        """Count without extra spaces, upper case."""
        return _SPACES.sub(" ", count or "").strip().upper()

    def _listed(self, count: str) -> Decimal | None:
        """4.5.6: a count of the list keeps the number of the list (BR-81, AC-49)."""
        if self.tables is None:
            return None
        wanted = self.normalize(count)
        found = next((c for c in self.tables.yarn_counts if same_text(self.normalize(c.count), wanted)), None)
        return found.converted if found else None

    def _spandex(self, kind: Decimal) -> Decimal | None:
        table = self.tables.spandex if self.tables is not None else seed_spandex()
        found = next((s for s in table if s.spandex == kind), None)
        return found.addition if found else None

    def _bad_format(self, count: str) -> CountConversion:
        violation = CountFormatRule().evaluate(Check(ok=False, text=count.strip()))
        message = violation.message if violation else CountFormatRule.message
        return CountConversion(count=count, error_code=CountFormatRule.code, error=message)

    def formula(self, count: str) -> CountConversion:
        """BR-81 formula: sum of the parts split by "+": "nD" / "nD/k" = n x k; "N" / "N/k" = 5316 / (N / k);
        "CB" = 20; "SP m" = addition of spandex m (4.5.13, BR-84). Any other part -> BR-81 error."""
        parts = [p.strip() for p in self.normalize(count).split("+")]
        if not parts or any(not p for p in parts):
            return self._bad_format(count)
        total = Decimal(0)
        try:
            for part in parts:
                if part == CARBON_MARK:
                    total += CARBON_ADDITION
                    continue
                if found := _FILAMENT_PART.match(part):
                    total += _number(found.group(1)) * Decimal(found.group(2) or 1)
                    continue
                if found := _SPANDEX_PART.match(part):
                    kind = _number(found.group(1))
                    addition = self._spandex(kind)
                    if addition is None:
                        violation = SpandexRule().evaluate(Check(ok=False, text=_plain(kind)))
                        return CountConversion(count=count, error_code=SpandexRule.code,
                                               error=violation.message if violation else SpandexRule.message)  # fmt: skip
                    total += addition
                    continue
                if found := _SPUN_PART.match(part):
                    spun = _number(found.group(1))
                    if spun == 0:
                        return self._bad_format(count)
                    total += SPUN_COUNT_FACTOR / (spun / Decimal(found.group(2) or 1))
                    continue
                return self._bad_format(count)
        except InvalidOperation:
            return self._bad_format(count)
        return CountConversion(count=count, value=total)

    def convert(self, count: str) -> CountConversion:
        """BR-81: the number of the list 4.5.6 when the count is listed, otherwise the formula."""
        listed = self._listed(count)
        if listed is not None:
            return CountConversion(count=count, value=listed)
        return self.formula(count)

    # ---- BR-82 -----------------------------------------------------------------------------------------------------
    def twist_violation(self, twist: int | None) -> RuleViolation | None:
        """BR-82: integer 50..3000 T/M (an empty twist is not checked here)."""
        if twist is None:
            return None
        return TwistRangeRule().evaluate(Check(ok=TWIST_MIN <= twist <= TWIST_MAX, text=str(twist)))

    # ---- BR-83 -----------------------------------------------------------------------------------------------------
    def suggest_fiber(self, count: str) -> FiberSystem | None:
        """BR-83: "D" in the count (after removing "SP m" and "CB") -> Filament, otherwise Spun; empty -> None."""
        parts = [p.strip() for p in self.normalize(count).split("+") if p.strip()]
        kept = [p for p in parts if p != CARBON_MARK and not p.startswith(SPANDEX_MARK)]
        if not parts:
            return None
        return FiberSystem.FILAMENT if any("D" in p for p in kept) else FiberSystem.SPUN

    # ---- BR-86 -----------------------------------------------------------------------------------------------------
    def count_from_yarn_name(self, name: str) -> str:
        """BR-86: count read from a yarn name. Filament "<n>D/<f>F/<k>" -> "nD" (+ "/k" when k >= 2), spun "<N>/<k>"
        -> "N/k" ("N" when k = 1), parts joined by " + " in name order; a carbon yarn (CACBON, CARBON, C.TRANG,
        C.DEN, C TRANG) adds " + CB". "" when no count is found."""
        upper = strip_accents(name or "").upper()
        found: list[tuple[int, int, str]] = []
        for match in _NAME_FILAMENT.finditer(upper):
            k = int(match.group(2) or 1)
            found.append((match.start(), match.end(), f"{match.group(1)}D" + (f"/{k}" if k >= 2 else "")))
        for match in _NAME_SPUN.finditer(upper):
            if any(start < match.end() and match.start() < end for start, end, _ in found):
                continue
            k = int(match.group(2))
            if k == 0:
                continue
            found.append((match.start(), match.end(), match.group(1) + (f"/{k}" if k >= 2 else "")))
        parts = [text for _, _, text in sorted(found)]
        if not parts:
            return ""
        if any(word in upper for word in CARBON_WORDS):
            parts.append(CARBON_MARK)
        return " + ".join(parts)

    def twist_from_text(self, text: str) -> int | None:
        """BR-86: the number before "T/M" ("400T/M" -> 400); a plain number is taken as is."""
        upper = (text or "").upper()
        found = _TWIST_TPM.search(upper) or _FIRST_NUMBER.search(upper)
        return int(found.group(1) if found.groups() else found.group(0)) if found else None

    def twist_in_name(self, name: str) -> int | None:
        """BR-86: the "<n>T/M" written in a yarn name (DTY75D/36F/1HIM 400T/M -> 400)."""
        found = _TWIST_TPM.search((name or "").upper())
        return int(found.group(1)) if found else None
