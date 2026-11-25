"""BR-50 customers: normalised unique names, unique codes, generated codes, similar names."""

import re
from collections.abc import Sequence
from difflib import SequenceMatcher

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.woven_costing.constants import (
    CUSTOMER_CODE_LENGTH,
    FORECAST_MARKER,
    MAX_SIMILAR,
    SIMILARITY_THRESHOLD,
)
from backend.features.woven_costing.models.checks import Check
from backend.features.woven_costing.models.customer_import import CustomerImportLine, CustomerRecord
from backend.features.woven_costing.models.enums import CustomerImportResult
from backend.features.woven_costing.models.master import Customer
from backend.shared.utils import strip_accents

TEAMS = ("FS1", "FS2")

_CODE = re.compile(r"^[A-Z0-9]{2,8}$")


class CustomerNameRule(BaseBusinessRule[Check]):
    """Target text = name typed; ok = no customer with the same normalised name."""

    code = "BR-50"
    message = "Khách hàng đã có."
    field = "name"

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"Khách hàng {target.text} đã có."


class CustomerCodeRule(BaseBusinessRule[Check]):
    """Target text = code, other = name of the customer that already uses it ("" = bad format)."""

    code = "BR-50"
    message = "Mã khách hàng phải có 2-8 ký tự chữ in hoa / số."
    field = "customer_code"

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        if target.other:
            return f"Mã khách hàng {target.text} đã dùng cho {target.other}."
        return f"Mã khách hàng {target.text} không hợp lệ: cần 2-8 ký tự chữ in hoa / số."


class CustomerBusiness(BaseBusiness[Check]):
    def rules(self) -> Sequence[BaseBusinessRule[Check]]:
        return (CustomerNameRule(),)

    def normalize(self, name: str) -> str:
        """BR-50: no accents, upper case, only letters / digits, single spaces."""
        text = re.sub(r"[^A-Z0-9]+", " ", strip_accents(name or "").upper())
        return " ".join(text.split())

    def clean_name(self, name: str) -> str:
        return " ".join((name or "").split())

    def find_same(self, name: str, customers: list[Customer], excluding_id: str = "") -> Customer | None:
        key = self.normalize(name)
        return next((c for c in customers if c.id != excluding_id and self.normalize(c.name) == key), None)

    def ensure_name_free(self, name: str, customers: list[Customer], excluding_id: str = "") -> None:
        same = self.find_same(name, customers, excluding_id)
        CustomerNameRule().check(Check(ok=same is None, text=same.name if same else name))

    def ensure_code(self, code: str, customers: list[Customer], excluding_id: str = "") -> None:
        if not _CODE.match(code):
            CustomerCodeRule().check(Check(ok=False, text=code))
        used = next((c for c in customers if c.customer_code == code and c.id != excluding_id), None)
        CustomerCodeRule().check(Check(ok=used is None, text=code, other=used.name if used else ""))

    def suggest_code(self, name: str, taken: set[str]) -> str:
        """BR-50: 4 first letters / digits of the normalised name (spaces removed); taken -> add 2, 3, ..."""
        base = self.normalize(name).replace(" ", "")[:CUSTOMER_CODE_LENGTH] or "KH"
        if len(base) < 2:
            base = (base + "KH")[:2]
        if base not in taken:
            return base
        number = 2
        while f"{base}{number}"[:8] in taken:
            number += 1
        return f"{base}{number}"[:8]

    def plan_import(self, records: list[CustomerRecord], existing: list[Customer]) -> list[CustomerImportLine]:
        """UC-12 steps 1-3: rows of team FS1 / FS2, without "TEAM FORECAST", normalised names without duplicates,
        code from the file (when valid and free) or generated (BR-50)."""
        seen = {self.normalize(c.name) for c in existing}
        taken = {c.customer_code for c in existing}
        lines = []
        for record in records:
            team = record.team.strip().upper()
            name = self.clean_name(record.name)
            if team not in TEAMS or not name or FORECAST_MARKER in name.upper():
                continue
            key = self.normalize(name)
            code = record.customer_code.strip().upper()
            if key in seen:
                lines.append(CustomerImportLine(name=name, customer_code=code, team=team,
                                                result=CustomerImportResult.DUPLICATE))  # fmt: skip
                continue
            if not _CODE.match(code) or code in taken:
                code = self.suggest_code(name, taken)
            seen.add(key)
            taken.add(code)
            lines.append(
                CustomerImportLine(name=name, customer_code=code, team=team, result=CustomerImportResult.ADDED)
            )
        return lines

    def similar(self, name: str, customers: list[Customer]) -> list[Customer]:
        """BR-50: names with similarity >= 60% or containing each other after normalisation, at most 10."""
        key = self.normalize(name)
        if not key:
            return []
        scored = []
        for customer in customers:
            other = self.normalize(customer.name)
            ratio = SequenceMatcher(None, key, other).ratio()
            if ratio >= SIMILARITY_THRESHOLD or key in other or other in key:
                scored.append((ratio, customer))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [c for _, c in scored[:MAX_SIMILAR]]
