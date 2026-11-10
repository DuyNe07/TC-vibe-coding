"""BR-76 Thành phần đọc từ tên (bổ sung 2026-11-10): count + fibers with percent + keywords."""

from decimal import Decimal

from backend.core.base import BaseValueObject
from backend.features.yarn_costing.models.yarn import Yarn

FIBER_LABELS = {"COTTON": "Cotton", "PE": "PE", "VISCOSE": "Viscose", "NYLON": "Nylon"}
KEYWORD_LABELS = {"CHAI KY": "CHẢI KỸ", "CHAI THO": "CHẢI THÔ"}


def percent_label(value: Decimal) -> str:
    text = f"{value.normalize():f}"
    return text.replace(".", ",") + "%"


class ParsedBlend(BaseValueObject):
    readable: bool = False
    count: Decimal | None = None
    fibers: tuple[tuple[str, Decimal], ...] = ()  # sorted (fiber, percent)
    keywords: tuple[str, ...] = ()  # sorted keys (CHAI KY / CHAI THO without accents)

    def same_blend(self, other: "ParsedBlend") -> bool:
        return self.readable and other.readable and self.count == other.count and self.fibers == other.fibers

    @property
    def text(self) -> str:
        """'20/1 · Cotton 50% + PE 50% · từ khoá MVS' (screen line "App đọc được")."""
        if not self.readable or self.count is None:
            return ""
        parts = " + ".join(f"{fiber_label(f)} {percent_label(p)}" for f, p in self.fibers)
        text = f"{self.count.normalize():f}/1 · {parts}"
        if self.keywords:
            text += " · từ khoá " + ", ".join(keyword_label(k) for k in self.keywords)
        return text


def fiber_label(fiber: str) -> str:
    """Known fibers by their usual name; others title-cased unless they carry a spec ("FDY 50D/36F/1")."""
    if fiber in FIBER_LABELS:
        return FIBER_LABELS[fiber]
    return fiber if any(ch.isdigit() for ch in fiber) else fiber.title()


def keyword_label(key: str) -> str:
    return KEYWORD_LABELS.get(key, key)


class BlendSuggestion(BaseValueObject):
    """One BR-77 match: ``kind`` = 'trung' (Trùng) or 'gan' (Gần giống); ``note`` = Khác ở đâu / trùng tên theo khách."""

    yarn: Yarn
    kind: str
    note: str = ""
