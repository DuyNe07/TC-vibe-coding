"""BR-76 đọc thành phần từ tên, BR-77 gợi ý sợi Trùng / Gần giống, BR-78 lý do khi vẫn gửi yêu cầu trùng
(bổ sung 2026-11-10)."""

import re
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.yarn_costing.business.name_business import YarnNameBusiness, collapse_spaces
from backend.features.yarn_costing.models.blend import BlendSuggestion as Suggestion
from backend.features.yarn_costing.models.blend import ParsedBlend, keyword_label
from backend.features.yarn_costing.models.customer_name import CustomerYarnName
from backend.features.yarn_costing.models.enums import YarnStatus
from backend.features.yarn_costing.models.yarn import Yarn
from backend.shared.utils.text import strip_accents

COTTON, PE, VISCOSE, NYLON = "COTTON", "PE", "VISCOSE", "NYLON"
KW_COMBED, KW_CARDED, KW_RECYCLE = "CHAI KY", "CHAI THO", "RECYCLE"
# BR-76: group codes with a fixed fiber order and the keyword they carry
FAMILIES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "CVC": ((COTTON, PE), ()),
    "CVCD": ((COTTON, PE), (KW_CARDED,)),
    "TC": ((PE, COTTON), ()),
    "PC": ((PE, COTTON), ()),
    "TR": ((PE, VISCOSE), ()),
    "CM": ((COTTON,), (KW_COMBED,)),
    "CD": ((COTTON,), (KW_CARDED,)),
}
FIBER_ALIASES = {
    "POLY": PE,
    "POLYESTER": PE,
    "PES": PE,
    "PE": PE,
    "CO": COTTON,
    "COTTON": COTTON,
    "VIS": VISCOSE,
    "VISCOSE": VISCOSE,
    "RAYON": VISCOSE,
    "NY": NYLON,
    "NYLON": NYLON,
}
KEYWORD_PATTERNS = (
    ("MVS", r"\bMVS\b"),
    ("SIRO", r"\bSIRO\b"),
    ("COMPACT", r"\bCOMPACT\b"),
    ("BCI", r"\bBCI\b"),
    ("SUPIMA", r"\bSUPIMA\b"),
    (KW_RECYCLE, r"\bRECYCLED?\b|\bRE-(?:PE|PES|POLY|POLYESTER)\b"),
    ("HIGH TWIST", r"\bHIGH TWIST\b"),
)
RATIO_GROUP = re.compile(r"\(\s*(\d+(?:[.,]\d+)?(?:\s*/\s*\d+(?:[.,]\d+)?)+)\s*\)")
FILAMENT = re.compile(r"\b(FDY|DTY)\b")
SUGGESTED_STATUSES = (YarnStatus.DA_TINH_GIA, YarnStatus.CO_MA_KE_TOAN)
MAX_SUGGESTIONS = 20
HUNDRED = Decimal(100)
TOLERANCE = Decimal("0.01")


def fold(text: str) -> str:
    """Upper case, no accents, single spaces."""
    return collapse_spaces(strip_accents(str(text or ""))).upper()


class DuplicateReasonRule(BaseBusinessRule[tuple[list[Yarn], str]]):
    """BR-78: target = (Trùng yarns of the chosen factory, reason)."""

    code = "BR-78"
    message = "Vui lòng nhập lý do gửi yêu cầu mới."
    field = "duplicate_reason"

    def is_satisfied_by(self, target: tuple[list[Yarn], str]) -> bool:
        same, reason = target
        return not same or bool(reason.strip())

    def describe_violation(self, target: tuple[list[Yarn], str]) -> str:
        same, _ = target
        factory = same[0].factory_code.value
        codes = ", ".join(y.yarn_code for y in same[:3])
        return (
            f'Đã có sợi trùng ở xưởng {factory}: {codes}. Vui lòng chọn "Dùng sợi này" hoặc nhập lý do gửi yêu cầu mới.'
        )


class BlendBusiness(BaseBusiness[ParsedBlend]):
    def __init__(self) -> None:
        self.names = YarnNameBusiness()

    # ---- BR-76 ----
    def _ratios(self, text: str) -> list[Decimal] | None:
        for match in RATIO_GROUP.finditer(text):
            try:
                values = [Decimal(v.strip().replace(",", ".")) for v in match.group(1).split("/")]
            except InvalidOperation:
                continue
            if abs(sum(values) - HUNDRED) <= TOLERANCE:
                return values
        return None

    def _fiber_group(self, text: str) -> list[str]:
        """CORE: first bracket group with letters, split on '/' keeping filament specs ("FDY 50D/36F/1") whole."""
        group = next((m for m in re.findall(r"\(([^()]*)\)", text) if re.search(r"[A-Z]", m)), "")
        tokens: list[str] = []
        for token in (t.strip() for t in group.split("/")):
            if tokens and token[:1].isdigit() and FILAMENT.search(tokens[-1]):
                tokens[-1] = f"{tokens[-1]}/{token}"
            elif token:
                tokens.append(token)
        return tokens

    def _fiber(self, token: str, keywords: set[str]) -> str:
        token = collapse_spaces(token)
        if token.startswith("RE-"):
            keywords.add(KW_RECYCLE)
            token = token[3:]
        if FILAMENT.search(token):
            return token
        return FIBER_ALIASES.get(token, token)

    def parse(self, name: str) -> ParsedBlend:
        """BR-76: count (BR-02), fibers with percent, keywords; unreadable when fibers and ratios do not pair up."""
        parsed = self.names.analyze(name)
        if not parsed.valid or parsed.count is None:
            return ParsedBlend()
        text = fold(name)
        position = text.find(f"{parsed.count_text}/1")
        prefix = text[:position].strip() if position >= 0 else fold(parsed.yarn_group)
        prefix = re.sub(r"^SOI\b\s*", "", prefix)  # "Sợi 20/1 ..." = no group code
        rest = text[position:] if position >= 0 else text
        keywords = {key for key, pattern in KEYWORD_PATTERNS if re.search(pattern, text)}
        if prefix in FAMILIES:
            fibers, extra = FAMILIES[prefix]
            tokens = list(fibers)
            keywords.update(extra)
        elif prefix in ("", "CORE"):
            tokens = [self._fiber(t, keywords) for t in self._fiber_group(rest)]
        else:
            tokens = [self._fiber(t, keywords) for t in prefix.split("/") if t.strip()]
        ratios = self._ratios(rest)
        if ratios is None:
            ratios = [HUNDRED] if len(tokens) == 1 else []
        if not tokens or len(tokens) != len(ratios):
            return ParsedBlend(readable=False, count=parsed.count)
        merged: dict[str, Decimal] = {}
        for fiber, ratio in zip(tokens, ratios, strict=True):
            merged[fiber] = merged.get(fiber, Decimal(0)) + ratio
        return ParsedBlend(
            readable=True,
            count=parsed.count,
            fibers=tuple(sorted((f, r.quantize(TOLERANCE)) for f, r in merged.items())),
            keywords=tuple(sorted(keywords)),
        )

    # ---- BR-77 ----
    def keyword_difference(self, typed: ParsedBlend, other: ParsedBlend) -> str:
        """'thêm X' = the yarn has it, the typed name has not; 'không có X' = the opposite."""
        extra = [f"thêm {keyword_label(k)}" for k in other.keywords if k not in typed.keywords]
        missing = [f"không có {keyword_label(k)}" for k in typed.keywords if k not in other.keywords]
        return ", ".join(extra + missing)

    def suggest(
        self,
        name: str,
        yarns: Sequence[Yarn],
        customer_names: Sequence[CustomerYarnName],
        factory_code: str | None = None,
    ) -> tuple[ParsedBlend, list[Suggestion], list[Suggestion]]:
        """BR-77 on base yarns Đã tính giá / Có mã kế toán of both factories → (parsed, Trùng, Gần giống)."""
        typed = self.parse(name)
        wanted = self.names.comparable_name(name)
        aliases: dict[str, list[CustomerYarnName]] = {}
        for alias in customer_names:
            aliases.setdefault(alias.base_code, []).append(alias)
        same: list[Suggestion] = []
        near: list[Suggestion] = []
        for yarn in yarns:
            if not yarn.is_base or yarn.status not in SUGGESTED_STATUSES:
                continue
            alias_hit = next(
                (
                    a
                    for a in aliases.get(yarn.base_code, [])
                    if self.names.comparable_name(a.customer_yarn_name) == wanted
                ),
                None,
            )
            if wanted and self.names.comparable_name(yarn.yarn_name) == wanted:
                same.append(Suggestion(yarn=yarn, kind="trung"))
                continue
            if wanted and alias_hit is not None:
                same.append(Suggestion(yarn=yarn, kind="trung", note=f"trùng tên theo khách {alias_hit.customer_name}"))
                continue
            other = self.parse(yarn.yarn_name)
            if not typed.same_blend(other):
                continue
            if typed.keywords == other.keywords:
                same.append(Suggestion(yarn=yarn, kind="trung"))
            else:
                near.append(Suggestion(yarn=yarn, kind="gan", note=self.keyword_difference(typed, other)))

        def order(s: Suggestion) -> tuple[int, str, int, str]:
            match = re.fullmatch(r"S\d-(\d+)", s.yarn.base_code)
            number = int(match.group(1)) if match else 10**9
            return (
                0 if s.yarn.factory_code.value == factory_code else 1,
                s.yarn.factory_code.value,
                number,
                s.yarn.base_code,
            )

        return typed, sorted(same, key=order)[:MAX_SUGGESTIONS], sorted(near, key=order)[:MAX_SUGGESTIONS]

    # ---- BR-78 ----
    def ensure_duplicate_reason(self, same_in_factory: list[Yarn], reason: str) -> None:
        DuplicateReasonRule().check((same_in_factory, reason))
