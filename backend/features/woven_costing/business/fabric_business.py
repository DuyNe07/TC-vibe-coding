"""BR-02 TCFNO cleaning, BR-03 fabric exists, BR-04 yarn normalisation, BR-47 fabric override, BR-72 manual yarns."""

import re
from collections.abc import Sequence
from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.woven_costing.models.checks import Check
from backend.features.woven_costing.models.costsheet import FabricSnapshot
from backend.features.woven_costing.models.enums import FabricSource, YarnDirection, YarnKind
from backend.features.woven_costing.models.fabric import Fabric, FabricYarn
from backend.features.woven_costing.models.fabric_import import YarnRecord
from backend.shared.utils import normalize_key

_CODE = re.compile(r"^[A-Z0-9]{10}$")
_TWIST = re.compile(r"(\d+(?:[.,]\d+)?)\s*T/M", re.IGNORECASE)
HUNDRED = Decimal(100)
WARP_WORDS = ("warp", "soi doc")
WEFT_WORDS = ("weft", "soi ngang")


class TcfnoFormatRule(BaseBusinessRule[Check]):
    """Target text = code as typed / read; ok = valid 10-character code after cleaning."""

    code = "BR-02"
    message = "Mã vải không hợp lệ: cần đủ 10 ký tự chữ và số."
    field = "tcfno"

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f'Mã vải "{target.text}" không hợp lệ: cần đủ 10 ký tự chữ và số.'


class FabricExistsRule(BaseBusinessRule[Check]):
    code = "BR-03"
    message = "Mã vải chưa có trong dữ liệu gốc. Liên hệ SO hoặc PD nhập nhanh mã này."
    field = "tcfno"

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"Mã vải {target.text} chưa có trong dữ liệu gốc. Liên hệ SO hoặc PD nhập nhanh mã này."


class ManualYarnsRule(BaseBusinessRule[list[FabricYarn]]):
    code = "BR-72"
    message = "Cần ít nhất 1 sợi dọc và 1 sợi ngang."
    field = "yarns"

    def is_satisfied_by(self, target: list[FabricYarn]) -> bool:
        directions = {y.direction for y in target}
        return YarnDirection.WARP in directions and YarnDirection.WEFT in directions


class FabricOverrideRule(BaseBusinessRule[Check]):
    """Target text = tcfno; ok = the fabric source is "Nhập tay"."""

    code = "BR-47"
    message = "Mã vải lấy từ dữ liệu gốc Peace / WFX, không được sửa thông số."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"Mã vải {target.text} lấy từ dữ liệu gốc Peace / WFX, không được sửa thông số."


class FabricBusiness(BaseBusiness[Check]):
    def rules(self) -> Sequence[BaseBusinessRule[Check]]:
        return (TcfnoFormatRule(),)

    def clean_code(self, raw: str) -> tuple[str, str]:
        """BR-02: no spaces, no dots, upper case, first "G" removed only when the code is longer than 10 characters
        (Peace "GEF29500023SN04"; changed 2026-11-25: a 10-character code such as GC12345678 keeps its G);
        tcfno = 10 first characters, rest = SY item."""
        text = re.sub(r"\s+", "", str(raw or "")).upper().replace(".", "")
        if text.startswith("G") and len(text) > 10:
            text = text[1:]
        return text[:10], text[10:]

    def code_check(self, raw: str) -> Check:
        code, _ = self.clean_code(raw)
        return Check(ok=bool(_CODE.match(code)), text=str(raw or "").strip())

    def ensure_code(self, raw: str) -> str:
        """BR-02 check; returns the cleaned code."""
        TcfnoFormatRule().check(self.code_check(raw))
        return self.clean_code(raw)[0]

    def ensure_exists(self, fabric: Fabric | None, tcfno: str) -> Fabric:
        """BR-03."""
        FabricExistsRule().check(Check(ok=fabric is not None, text=tcfno))
        assert fabric is not None  # guarded by the rule above
        return fabric

    def ensure_manual_yarns(self, yarns: list[FabricYarn]) -> None:
        """BR-72."""
        ManualYarnsRule().check(yarns)

    def ensure_override_allowed(self, snapshot: FabricSnapshot, source: FabricSource) -> None:
        """BR-47: only fabrics whose source is "Nhập tay"."""
        FabricOverrideRule().check(Check(ok=source == FabricSource.MANUAL, text=snapshot.tcfno))

    def direction(self, raw: str) -> YarnDirection | None:
        """4.2: Warp / WARP / Soi doc / Sợi dọc -> WARP; the same for WEFT."""
        key = normalize_key(raw)
        if any(word in key for word in WARP_WORDS):
            return YarnDirection.WARP
        if any(word in key for word in WEFT_WORDS):
            return YarnDirection.WEFT
        return None

    def yarn_kind(self, raw: str) -> YarnKind | None:
        key = normalize_key(raw)
        if key == "soi don":
            return YarnKind.SINGLE
        if key == "soi se":
            return YarnKind.TWISTED
        return None

    def twist_of(self, yarn_name: str, tpm: str = "") -> str:
        """BR-04: WFX TPM when not 0, else the number before "T/M" in the yarn name (800T/M)."""
        tpm_text = str(tpm or "").strip()
        if tpm_text and tpm_text not in ("0", "0.0"):
            return f"{tpm_text}T/M"
        found = _TWIST.search(yarn_name or "")
        return f"{found.group(1)}T/M" if found else ""

    def normalize_yarns(self, records: list[YarnRecord]) -> list[FabricYarn]:
        """BR-04 for the yarn rows of one code: defaults of the raw yarn, twist, and seq 1, 2.. per direction."""
        counters: dict[YarnDirection, int] = {}
        yarns = []
        for record in records:
            direction = self.direction(record.direction)
            if direction is None:
                continue
            counters[direction] = counters.get(direction, 0) + 1
            raw_code = record.raw_yarn_code.strip()
            raw_rate = record.raw_rate if record.raw_rate not in (None, Decimal(0)) else HUNDRED
            yarns.append(
                FabricYarn(
                    direction=direction,
                    seq=counters[direction],
                    full_yarn_name=record.full_yarn_name.strip(),
                    yarn_code=record.yarn_code.strip(),
                    yarn_name=record.yarn_name.strip(),
                    rate=min(max(record.rate, Decimal(0)), HUNDRED),
                    yarn_kind=self.yarn_kind(record.yarn_kind),
                    raw_yarn_code=record.yarn_code.strip() if raw_code in ("", "0") else raw_code,
                    raw_yarn_name=record.raw_yarn_name.strip() or record.yarn_name.strip(),
                    raw_rate=raw_rate,
                    twist_tpm=self.twist_of(record.yarn_name, record.tpm),
                )
            )
        return yarns

    def snapshot(self, fabric: Fabric) -> FabricSnapshot:
        """Snapshot of 4.1 + 4.2 taken by a costsheet."""
        return FabricSnapshot(
            tcfno=fabric.tcfno, fabric_name=fabric.fabric_name, source=fabric.source, specs=fabric.specs,
            yarns=list(fabric.yarns),
        )  # fmt: skip
