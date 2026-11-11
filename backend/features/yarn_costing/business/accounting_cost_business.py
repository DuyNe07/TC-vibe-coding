"""BR-80 đọc file Z, BR-82 ghép với giá app, BR-83 cảnh báo đối chiếu (bổ sung 2026-11-10)."""

import calendar
import re
from collections.abc import Sequence
from datetime import date
from decimal import Decimal, InvalidOperation

from backend.core.base import BaseBusiness
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.accounting_cost import AccountingAmounts, AccountingCostLine
from backend.features.yarn_costing.models.enums import FactoryCode, LineType
from backend.features.yarn_costing.models.price_history import PriceHistory
from backend.features.yarn_costing.models.yarn import CostBreakdown, PriceLine, Yarn
from backend.shared.utils.text import strip_accents

SHEET_PATTERN = re.compile(r"^Z\s*SOI\s*T\s*(\d{1,2})\s*[.\-/]\s*(\d{2})\b")
MSG_QUANTITY = "Số lượng phải lớn hơn 0."
MSG_NOT_NUMBER = "Cột {column} không phải số."
MSG_DUPLICATE = "Mã '{code}' bị trùng trong sheet."
MSG_BAD_MONTH = "Không đọc được tháng từ tên sheet '{sheet}'."
MSG_LEVEL = "Mức cảnh báo phải là số lớn hơn 0."
WARN_SMALL = "⚠ Sản lượng nhỏ"
WARN_GAP = "🔴 Lệch nhiều"
CURRENT_PRICE = "giá hiện tại"
CORE_LENGTH = 18  # BR-82 (sửa 2026-11-10): mã kế toán bỏ hậu tố D / E / FCD / FCE / P
CORE_NOTE = "ghép theo 18 ký tự đầu"
LINE_ORDER = {LineType.THUONG: 0, LineType.THI_NGHIEM: 1, LineType.CHIET_KHAU: 2, LineType.PHU_PHI: 3}
HUNDRED = Decimal(100)


def number(value: object) -> Decimal | None:
    """Excel cell → Decimal (empty = None, text that is not a number = raises InvalidOperation)."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        raise InvalidOperation
    if isinstance(value, int | float | Decimal):
        return Decimal(str(value))
    return Decimal(str(value).strip().replace(" ", "").replace(",", ""))


class AccountingCostBusiness(BaseBusiness[AccountingCostLine]):
    # ---- BR-80 ----
    def sheet_period(self, sheet_name: str) -> str | None:
        """'Z SỢI T09.26' → '2026-09'; None when the name is not a Z sheet; '' when the month is invalid."""
        match = SHEET_PATTERN.match(strip_accents(sheet_name).upper().strip())
        if not match:
            return None
        month, year = int(match.group(1)), 2000 + int(match.group(2))
        return f"{year:04d}-{month:02d}" if 1 <= month <= 12 else ""

    def read_rows(
        self, rows: Sequence[tuple[int, dict[str, object]]], month_id: str, period: str
    ) -> tuple[list[AccountingCostLine], list[tuple[int, str, str]]]:
        """Rows keyed by the 4.21.1 field names (code, name, quantity, vlc, labor, depreciation, power, materials,
        overhead, total) → (valid lines, rejected (excel row, code, reason)). Rows whose code does not start with S1 / S4
        (totals) are skipped silently."""
        lines: list[tuple[int, AccountingCostLine]] = []
        rejected: list[tuple[int, str, str]] = []
        labels = {
            "quantity": "SỐ LƯỢNG",
            "vlc": "VLC",
            "labor": "NHÂN CÔNG + BẢO TRÌ",
            "depreciation": "KHẤU HAO",
            "power": "ĐỘNG LỰC",
            "materials": "VẬT TƯ, NHIÊN LIỆU, CCDC, VẬT LIỆU PHỤ",
            "overhead": "CHI PHÍ QUẢN LÝ",
            "total": "CỘNG",
        }
        for excel_row, cells in rows:
            code = str(cells.get("code") or "").strip().upper()
            if code[:2] not in ("S1", "S4"):
                continue
            values: dict[str, Decimal] = {}
            problem = ""
            for key, label in labels.items():
                try:
                    value = number(cells.get(key))
                except (InvalidOperation, ValueError):
                    problem = MSG_NOT_NUMBER.format(column=label)
                    break
                values[key] = value if value is not None else Decimal(0)
            if not problem and values["quantity"] <= 0:
                problem = MSG_QUANTITY
            if not problem and number(cells.get("total")) is None:
                problem = MSG_NOT_NUMBER.format(column="CỘNG")
            if problem:
                rejected.append((excel_row, code, problem))
                continue
            line = AccountingCostLine(
                month_id=month_id,
                period=period,
                factory_code=FactoryCode(code[:2]),
                accounting_code=code,
                product_name=" ".join(str(cells.get("name") or "").split()),
                quantity=values["quantity"],
                material_amount=values["vlc"],
                amounts=AccountingAmounts(
                    labor=values["labor"],
                    depreciation=values["depreciation"],
                    power=values["power"],
                    materials=values["materials"],
                    overhead=values["overhead"],
                ),
                total_amount=values["total"],
            )
            lines.append((excel_row, line))
        counts: dict[str, int] = {}
        for _, line in lines:
            counts[line.accounting_code] = counts.get(line.accounting_code, 0) + 1
        valid = []
        for excel_row, line in lines:
            if counts[line.accounting_code] > 1:
                rejected.append((excel_row, line.accounting_code, MSG_DUPLICATE.format(code=line.accounting_code)))
            else:
                valid.append(line)
        rejected.sort()
        return valid, rejected

    # ---- BR-82 ----
    def month_end(self, period: str) -> date:
        year, month = (int(p) for p in period.split("-"))
        return date(year, month, calendar.monthrange(year, month)[1])

    def lines_by_code(self, yarns: Sequence[Yarn]) -> dict[str, list[tuple[Yarn, PriceLine]]]:
        found: dict[str, list[tuple[Yarn, PriceLine]]] = {}
        for yarn in yarns:
            for line in yarn.lines:
                if line.accounting_code:
                    found.setdefault(line.accounting_code.strip().upper(), []).append((yarn, line))
            regular = yarn.regular_line  # BR-108: mã kế toán gộp từ mã trùng tên đã loại → dòng Thường của mã giữ
            if regular is not None:
                for code in yarn.merged_accounting_codes:
                    found.setdefault(code.strip().upper(), []).append((yarn, regular))
        for pairs in found.values():
            pairs.sort(key=lambda p: (LINE_ORDER[p[1].line_type], p[1].line_code))
        return found

    def match(
        self, code: str, by_code: dict[str, list[tuple[Yarn, PriceLine]]]
    ) -> tuple[list[tuple[Yarn, PriceLine]], bool]:
        """BR-82: exact code first; else the price lines whose code has the same first 18 characters
        (returns (pairs, matched by core))."""
        code = code.strip().upper()
        if code in by_code:
            return by_code[code], False
        core = code[:CORE_LENGTH]
        pairs = [p for key, found in by_code.items() if key[:CORE_LENGTH] == core for p in found]
        pairs.sort(key=lambda p: (LINE_ORDER[p[1].line_type], p[1].line_code))
        return pairs, bool(pairs)

    def price_at(
        self, line: PriceLine, history: Sequence[PriceHistory], end: date
    ) -> tuple[CostBreakdown, date | None]:
        """Newest history price with effective_date ≤ end; none → current price (date None = 'giá hiện tại')."""
        entries = [h for h in history if h.effective_date is not None and h.effective_date <= end and h.new.total > 0]
        if not entries:
            return line.cost, None
        latest = max(entries, key=lambda h: (h.effective_date, h.changed_at))
        return latest.new, latest.effective_date

    def gap_percent(self, app_total: Decimal, accounting: Decimal) -> Decimal | None:
        return (app_total - accounting) / accounting * HUNDRED if accounting > 0 else None

    # ---- BR-83 ----
    def ensure_levels(self, small_kg: Decimal, gap_percent: Decimal) -> None:
        if small_kg <= 0 or gap_percent <= 0:
            raise YarnValidationError(MSG_LEVEL)

    def warnings(self, quantity: Decimal, gap: Decimal | None, small_kg: Decimal, gap_level: Decimal) -> list[str]:
        result = []
        if quantity < small_kg:
            result.append(WARN_SMALL)
        if gap is not None and abs(gap) > gap_level:
            result.append(WARN_GAP)
        return result
