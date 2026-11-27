"""BR-100 cone table suggestion (2026-11-26, replaces BR-87): which Ngang Se lines are twisted together (one cone) and
which are twisted apart (one cone each)."""

import re
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.woven_costing.business.count_business import CountBusiness
from backend.features.woven_costing.constants import CARBON_MARK, MAX_CONE_LINES, SPANDEX_MARK
from backend.features.woven_costing.models.costsheet import Costsheet
from backend.features.woven_costing.models.costsheet_input import ConeLine, TwistLine, WeavingInput, YarnLine
from backend.features.woven_costing.models.enums import YarnDirection
from backend.shared.utils import strip_accents

ZERO = Decimal(0)
WEFT_TWIST = "Ngang"
CARBON, SPANDEX = "carbon", "spandex"
QTY_TOLERANCE = Decimal("0.0001")  # kg: a suggested quantity sent back through the screen is still "not edited"
CHECK_CONE = "Kiểm tra lại cone: sợi {minor} có thể se chung với {first} hoặc {second}."
_CARBON_NAME = re.compile(r"\bBR1\b|\bWHITE C\b|\bBLACK C\b|CARBON|CACBON|C\.TRANG|C\.DEN|\bC TRANG\b")
_SPANDEX_NAME = re.compile(r"SPANDEX")
_NUMBER = re.compile(r"\d+(?:\.\d+)?")
_OLD_CELLS = {"cone_count_1": "", "cone_qty_1": None, "cone_count_1_suggested": False,
              "cone_qty_1_suggested": False, "cone_count_2": "", "cone_qty_2": None}  # fmt: skip


def _parts(count: str) -> list[str]:
    return [p.strip() for p in CountBusiness().normalize(count).split("+") if p.strip()]


class ConeBusiness(BaseBusiness[Costsheet]):
    def __init__(self) -> None:
        self.counts = CountBusiness()

    # ---- BR-100 a: sợi phụ / sợi chính ------------------------------------------------------------------------------
    def minor_kind(self, yarn_name: str) -> str:
        """BR-100 a: carbon (BR1, WHITE C, BLACK C, CARBON, CACBON, C.TRANG, C.DEN, C TRANG) or spandex by name."""
        upper = strip_accents(yarn_name or "").upper()
        if _SPANDEX_NAME.search(upper):
            return SPANDEX
        return CARBON if _CARBON_NAME.search(upper) else ""

    def _yarn_twist(self, line: YarnLine) -> int | None:
        return self.counts.twist_from_text(line.twist_tpm) or self.counts.twist_in_name(line.source_yarn_name)

    def line_kind(self, count: str, twist: int | None, yarn_lines: list[YarnLine]) -> str:
        """BR-100 a: a Ngang Se line is minor when every Ngang yarn line ticked Se with the same count and twist has a
        carbon / spandex name, or when its count is only "CB" / "SP m"; otherwise it is a main yarn ("")."""
        key = self.counts.normalize(count)
        kinds = [
            self.minor_kind(f"{y.yarn_name} {y.source_yarn_name}")
            for y in yarn_lines
            if y.direction == YarnDirection.WEFT and y.is_twisted
            and self.counts.normalize(self.counts.count_from_yarn_name(y.yarn_name or y.source_yarn_name)) == key
            and self._yarn_twist(y) == twist
        ]  # fmt: skip
        if kinds and all(kinds):
            return SPANDEX if SPANDEX in kinds else CARBON
        parts = _parts(count)
        if parts and all(p == CARBON_MARK for p in parts):
            return CARBON
        if parts and all(p.startswith(SPANDEX_MARK) for p in parts):
            return SPANDEX
        return ""

    def weft_groups(self, twist_lines: list[TwistLine]) -> list[tuple[str, int | None, Decimal]]:
        """BR-100 b: Ngang Se lines with the same count and twist are one line (quantities added), in table order."""
        groups: dict[tuple[str, int | None], tuple[str, int | None, Decimal]] = {}
        for line in twist_lines:
            if line.direction != WEFT_TWIST or not (line.count or line.quantity_kg):
                continue
            key = (self.counts.normalize(line.count), line.twist)
            count, twist, qty = groups.get(key, (line.count.strip(), line.twist, ZERO))
            groups[key] = (count, twist, qty + (line.quantity_kg or ZERO))
        return list(groups.values())

    # ---- BR-100 c, d, e, f -----------------------------------------------------------------------------------------
    def _converted(self, count: str) -> Decimal | None:
        value = self.counts.formula(count).value
        return value if value and value > 0 else None

    def _distance(self, minor: tuple[str, int | None, Decimal], main: tuple[str, int | None, Decimal]) -> Decimal:
        """BR-100 c: 2 yarns twisted together have the same length -> minor kg ≈ main kg × minor count ÷ main count."""
        minor_count, main_count = self._converted(minor[0]), self._converted(main[0])
        if minor_count is None or main_count is None:
            return Decimal(10**9) - main[2]  # unreadable count: the biggest main yarn
        return abs(main[2] * minor_count / main_count - minor[2])

    def minor_part(self, count: str, kind: str) -> str:
        """BR-100 d: the part a minor yarn adds to the cone count: "CB" (carbon with CB), "SP m" (spandex), the count."""
        parts = _parts(count)
        if kind == CARBON and CARBON_MARK in parts:
            return CARBON_MARK
        if kind == SPANDEX:
            number = _NUMBER.search(count)
            return f"{SPANDEX_MARK} {number.group(0)}" if number else count.strip()
        return count.strip()

    def _label(self, count: str, twist: int | None) -> str:
        return f"{count} ({twist} T/M)" if twist is not None else count

    def suggest_lines(
        self, twist_lines: list[TwistLine], yarn_lines: list[YarnLine]
    ) -> tuple[list[ConeLine], list[str]]:
        """BR-100: one cone per main yarn, each minor yarn (carbon, spandex) joined to the main yarn of the same twist
        whose length matches best (no main yarn: its own cone). Returns (suggested lines, BR-100 f warnings)."""
        groups = self.weft_groups(twist_lines)
        kinds = [self.line_kind(count, twist, yarn_lines) for count, twist, _ in groups]
        mains = [g for g, kind in zip(groups, kinds, strict=True) if not kind]
        joined: dict[int, list[tuple[tuple[str, int | None, Decimal], str]]] = {i: [] for i in range(len(mains))}
        alone: list[tuple[str, int | None, Decimal]] = []
        warnings: list[str] = []
        for group, kind in zip(groups, kinds, strict=True):
            if not kind:
                continue
            same = [i for i, m in enumerate(mains) if m[1] == group[1]]
            candidates = sorted(same or range(len(mains)), key=lambda i: self._distance(group, mains[i]))
            if not candidates:
                alone.append(group)
                continue
            joined[candidates[0]].append((group, kind))
            if len(same) >= 2:
                ranked = [i for i in candidates if i in same]
                warnings.append(
                    CHECK_CONE.format(minor=group[0], first=mains[ranked[0]][0], second=mains[ranked[1]][0])
                )
        lines: list[ConeLine] = []
        for i, main in enumerate(mains):
            count = main[0]
            for minor, kind in joined[i]:
                part = self.minor_part(minor[0], kind)
                if part not in _parts(count):
                    count = f"{count} + {part}"
            members = [main, *(minor for minor, _ in joined[i])]
            lines.append(self._line(count, members))
        lines += [self._line(group[0], [group]) for group in alone]
        return lines[:MAX_CONE_LINES], warnings

    def _line(self, count: str, members: list[tuple[str, int | None, Decimal]]) -> ConeLine:
        return ConeLine(
            count=count,
            quantity_kg=sum((m[2] for m in members), ZERO),
            members=" + ".join(self._label(m[0], m[1]) for m in members),
            suggested=True,
            suggestion_key=f"cone|{self.counts.normalize(count)}",
        )

    # ---- BR-100 g, h -----------------------------------------------------------------------------------------------
    def still_suggestion(self, line: ConeLine, offered: ConeLine | None) -> bool:
        """BR-100 g: a line is still the app suggestion when it says so and no cell differs from what was suggested.
        A converted BR-87 suggestion (no suggestion key) is replaced by the new suggestion."""
        if not line.suggested:
            return False
        if not line.suggestion_key:
            return True
        if offered is None:
            return False
        same_qty = abs((line.quantity_kg or ZERO) - (offered.quantity_kg or ZERO)) <= QTY_TOLERANCE
        return same_qty and self.counts.normalize(line.count) == self.counts.normalize(offered.count)

    def merge_lines(
        self, lines: list[ConeLine], offered: list[ConeLine], skips: list[str], fresh: list[ConeLine]
    ) -> tuple[list[ConeLine], list[str]]:
        """BR-100 g: lines still suggested are replaced by the fresh suggestion of the same key (or dropped); lines
        typed / edited by sales are kept; a suggestion sales deleted or edited is not made again (``skips``); a fresh
        suggestion with the count of a kept line is not added; new suggestions are appended. Returns (lines, skips)."""
        by_key = {o.suggestion_key: o for o in offered if o.suggestion_key}
        present = {line.suggestion_key for line in lines if line.suggestion_key}
        skipped = set(skips) | (set(by_key) - present)
        still = [self.still_suggestion(line, by_key.get(line.suggestion_key)) for line in lines]
        skipped |= {line.suggestion_key for line, s in zip(lines, still, strict=True) if not s and line.suggestion_key}
        kept_counts = {self.counts.normalize(line.count) for line, s in zip(lines, still, strict=True) if not s}
        fresh_by_key = {
            f.suggestion_key: f
            for f in fresh
            if f.suggestion_key not in skipped and self.counts.normalize(f.count) not in kept_counts
        }
        merged: list[ConeLine] = []
        for line, is_suggestion in zip(lines, still, strict=True):
            if not is_suggestion:
                merged.append(line.model_copy(update={"suggested": False}) if line.suggested else line)
            elif line.suggestion_key in fresh_by_key:
                merged.append(fresh_by_key.pop(line.suggestion_key))
        merged += list(fresh_by_key.values())
        return merged[:MAX_CONE_LINES], sorted(skipped)

    def suggest_cone(self, sheet: Costsheet) -> WeavingInput:
        """BR-100 (2026-11-26): the cone table of the costsheet after a calculation. Stored cones are converted
        (``Costsheet.cone_rows``); on a live costsheet the suggested lines follow the Ngang Se lines; a costsheet
        stored before with cones typed by sales keeps its lines as they are."""
        weaving = sheet.weaving
        rows, live = sheet.cone_rows, sheet.cone_live
        update: dict[str, object] = {**_OLD_CELLS, "cone_lines_converted": True, "cone_lines_live": live}
        if not live:
            return weaving.model_copy(update=update | {"cone_lines": rows, "cone_suggestions": []})
        fresh, _ = self.suggest_lines(sheet.twist_lines, sheet.yarn_lines)
        lines, skips = self.merge_lines(rows, weaving.cone_suggestions, weaving.cone_suggestion_skips, fresh)
        offered = [line for line in lines if line.suggested]
        return weaving.model_copy(
            update=update | {"cone_lines": lines, "cone_suggestions": offered, "cone_suggestion_skips": skips}
        )

    def check_warnings(self, sheet: Costsheet) -> list[str]:
        """BR-100 f: "Kiểm tra lại cone…" while the cone table holds app suggestions."""
        if not any(row.suggested for row in sheet.cone_rows):
            return []
        return self.suggest_lines(sheet.twist_lines, sheet.yarn_lines)[1]
