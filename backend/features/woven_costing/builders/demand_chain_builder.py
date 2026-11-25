"""Stored calculation result -> "Chuỗi nhu cầu" rows and the Screen 2 tab of each warning (UI change 2026-11-23).

Only reshapes values the calculation (BR-18, BR-19, BR-22, BR-25..BR-27) already stored: no new business rule.
"""

from collections.abc import Iterable
from decimal import Decimal

from backend.core.base import BaseBuilder
from backend.features.woven_costing.dto.costsheet_dto import DemandStepDTO
from backend.features.woven_costing.models.costsheet import Costsheet
from backend.features.woven_costing.models.enums import (
    JOB_FORMS,
    NO_DYEING_FORMS,
    NO_WEAVING_FORMS,
    SaleForm,
    WarningSection,
)

ZERO = Decimal(0)
HUNDRED = Decimal(100)

S = WarningSection
# Section 8 "Đổi giao diện Màn hình 2" item 6: which tab shows the warning of each BR code at its top
WARNING_SECTIONS: dict[str, WarningSection] = {
    "BR-05": S.YARN, "BR-19": S.YARN, "BR-44": S.YARN, "BR-45": S.YARN,
    "BR-20": S.WEAVING, "BR-21": S.WEAVING, "BR-22": S.WEAVING, "BR-23": S.WEAVING, "BR-24": S.WEAVING,
    "BR-80": S.WEAVING, "BR-81": S.WEAVING, "BR-82": S.WEAVING, "BR-83": S.WEAVING, "BR-84": S.WEAVING,
    "BR-86": S.WEAVING,
    "BR-17": S.DYEING, "BR-25": S.DYEING, "BR-26": S.DYEING, "BR-43": S.DYEING,
    "BR-28": S.PRICE, "BR-29": S.PRICE, "BR-42": S.PRICE,
    "BR-03": S.FABRIC, "BR-10": S.FABRIC, "BR-13": S.FABRIC, "BR-14": S.FABRIC, "BR-47": S.FABRIC,
}  # fmt: skip
# Fallback by the words of the message (checked in this order) for a code not in the table
WARNING_KEYWORDS: tuple[tuple[WarningSection, tuple[str, ...]], ...] = (
    (S.WEAVING, ("dòng se", "chi số", "độ săn", "spandex", "hồ", "mắc", "cone", "dệt")),
    (S.YARN, ("sợi",)),
    (S.DYEING, ("nhuộm", "tcdn")),
    (S.PRICE, ("gp%", "op%", "f&i", "giá bán", "vận chuyển")),
    (S.FABRIC, ("độ co", "thông số", "mã vải")),
)


def warning_section(code: str, message: str) -> WarningSection:
    """Tab of a warning: by its BR code, otherwise by the words of its message, otherwise "Khác"."""
    if code in WARNING_SECTIONS:
        return WARNING_SECTIONS[code]
    text = message.lower()
    for section, words in WARNING_KEYWORDS:
        if any(word in text for word in words):
            return section
    return S.OTHER


def _pct(rate: Decimal) -> str:
    """0.024 -> "2,40%" (Vietnamese decimal comma)."""
    return f"{rate * HUNDRED:.2f}".replace(".", ",") + "%"


def _range(rates: Iterable[Decimal]) -> str:
    values = sorted(set(rates))
    if not values:
        return _pct(ZERO)
    if values[0] == values[-1]:
        return _pct(values[0])
    return f"{_pct(values[0])} - {_pct(values[-1])}"


def _money(value: Decimal) -> str:
    return f"{value:,.0f}".replace(",", ".")


def _div(value: Decimal, rate: Decimal) -> Decimal | None:
    return value / rate if rate else None


class DemandChainBuilder(BaseBuilder[list[DemandStepDTO]]):
    """Rows from the finished meters sold back to the yarn, each cost row also per order meter; the cost rows (B/C
    liquidation negative) add up to the total cost and total / order meters = unit cost."""

    def __init__(self, sheet: Costsheet) -> None:
        self.sheet = sheet
        self.result = sheet.result
        self.order_m = sheet.order_meters or ZERO

    def cost_row(self, step: str, cost: Decimal, losses: str = "", meters: Decimal | None = None) -> DemandStepDTO:
        return DemandStepDTO(step=step, meters=meters, losses=losses, cost=cost, cost_per_m=_div(cost, self.order_m))

    def build(self) -> list[DemandStepDTO]:
        r, sale_form = self.result, self.sheet.sale_form
        if not r.calculated or self.order_m <= 0:
            return []
        greige, dyed = sale_form in NO_DYEING_FORMS, sale_form in NO_WEAVING_FORMS
        job = sale_form in JOB_FORMS
        sold_m_per_kg = r.greige_m_per_kg if greige else r.finished_m_per_kg
        rows = [
            DemandStepDTO(
                step="Thành phẩm giao khách",
                meters=self.order_m,
                kg=_div(self.order_m, sold_m_per_kg),
                losses="Số lượng đặt (giao mộc)"
                if job and greige
                else "Số lượng đặt (bán mộc)"
                if greige
                else "Số lượng đặt",
            )
        ]
        if not greige:
            rows.append(
                DemandStepDTO(
                    step="Thành phẩm nhuộm ra",
                    meters=r.finished_meters_needed,
                    kg=r.finished_kg,
                    losses=f"B/C thành phẩm {_pct(r.finished_bc_rate)}",
                )  # fmt: skip
            )
            rows.append(self.cost_row("Chi phí Nhuộm", r.dyeing_total, f"{_money(r.dyeing_per_m)} đ/m thành phẩm"))
        rows.append(DemandStepDTO(step="Vải mộc", meters=r.greige_meters, kg=r.greige_kg, losses=self.greige_losses()))
        if greige and r.dyeing_total:
            rows.append(self.cost_row("Chi phí Nhuộm", r.dyeing_total))
        if sale_form == SaleForm.DYEING_JOB:  # BR-90
            rows.append(self.cost_row("Mộc khách giao", ZERO, "Khách giao mộc: không tính tiền", r.greige_meters))
        elif dyed:
            price = self.sheet.greige_buy_price or ZERO
            rows.append(self.cost_row("Mua mộc ngoài", price * r.greige_meters, f"Giá mộc {_money(price)} đ/m"))
        else:
            factor = f"Hệ số số lượng {r.quantity_factor:.3f}".rstrip("0").rstrip(".").replace(".", ",")
            rows.append(self.cost_row("Chi phí Dệt", r.weaving_total, factor))
            yarn_kg = sum((line.yarn_kg for line in r.yarn_lines), ZERO)
            losses = (
                f"Tiêu hao sợi {_range(line.loss_rate for line in r.yarn_lines)}; "
                f"sợi cặn {_range(line.waste_rate for line in self.sheet.yarn_lines)}"
            )
            if sale_form == SaleForm.WEAVING_JOB:  # BR-89: kg the customer must give, no cost
                rows.append(DemandStepDTO(step="Sợi khách giao", kg=yarn_kg, losses=losses))
                rows.append(self.cost_row("Chi phí Sợi", ZERO, "Khách giao sợi: không tính tiền"))
            else:
                rows.append(DemandStepDTO(step="Sợi", kg=yarn_kg, losses=losses))
                rows.append(self.cost_row("Chi phí Sợi", r.yarn_total))
        if not job:  # BR-89, BR-90: no B/C liquidation on a job order
            bc_meters = r.greige_meters - self.order_m
            rows.append(self.cost_row("Thanh lý B/C (trừ)", -r.bc_liquidation, "Bán vải B/C dư", bc_meters))
        rows.append(
            DemandStepDTO(
                step="Tổng chi phí / Đơn giá",
                meters=self.order_m,
                cost=r.total_cost,
                cost_per_m=r.unit_cost_vnd,
                is_total=True,
            )  # fmt: skip
        )
        return rows

    def greige_losses(self) -> str:
        """BR-18 divisors used from the finished meters to the greige meters."""
        r, sale_form = self.result, self.sheet.sale_form
        if sale_form in NO_DYEING_FORMS:
            return f"B/C thành phẩm {_pct(r.finished_bc_rate)}; B/C mộc {_pct(r.greige_bc_rate)}"
        parts = [f"Tiêu hao nhuộm {_pct(r.dye_loss_rate)}", f"Độ co {_pct(r.shrinkage)}"]
        if sale_form not in NO_WEAVING_FORMS:
            parts.append(f"B/C mộc {_pct(r.greige_bc_rate)}")
        return "; ".join(parts)
