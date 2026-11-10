"""Đợt 2 (bổ sung 2026-11-10): BR-93 gợi ý nhóm giá, BR-94 giá nguyên liệu / kg sợi, BR-95 giá báo khách, BR-96 kiểm tra,
BR-97 số báo giá, BR-98 gợi ý mã kế toán."""

import re
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.yarn_costing.business.blend_business import BlendBusiness
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.enums import (
    Incoterm,
    LineType,
    MaterialMarket,
    PriceKind,
    StockSection,
    YarnStatus,
)
from backend.features.yarn_costing.models.material_price import (
    COTTON_PLAN_ID,
    GroupAverage,
    Quote,
    QuoteComponent,
    StockLine,
)
from backend.features.yarn_costing.models.yarn import PriceLine, Yarn, YarnComponent

ZERO = Decimal(0)
ONE = Decimal(1)
CORE_LENGTH = 18
PRICED = (YarnStatus.DA_TINH_GIA, YarnStatus.CO_MA_KE_TOAN)
QUOTE_NO = re.compile(r"^BG-(\d{4})-(\d+)$")
MSG_NO_YARN = "Vui lòng chọn sợi."
MSG_NOT_PRICED = "Sợi {code} chưa có giá."
MSG_QTY = "Số lượng đơn hàng phải lớn hơn 0."
MSG_FACTOR = "Hệ số phải lớn hơn 0."
MSG_NEGATIVE = "GP và Commission không được âm."
MSG_MARGIN = "Tổng GP và Commission phải nhỏ hơn 100%."
MSG_FI = "F&I không được âm."
MSG_NO_GROUP = "Thành phần '{material}' chưa chọn nhóm giá."
MSG_CODE_LONG = "Mã kế toán tối đa 50 ký tự."
MSG_CUSTOMER_LONG = "Khách hàng tối đa 100 ký tự."
MSG_NOTE_LONG = "Ghi chú tối đa 500 ký tự."
MSG_MARKET = "Vui lòng chọn Nội địa hoặc Xuất khẩu."
MSG_DELETE = "Chỉ người tính hoặc Phòng SO được xoá báo giá này."


def label_key(text: str) -> str:
    return " ".join(text.upper().split())


class QuoteBusiness(BaseBusiness[Quote]):
    # ---- BR-93 ----
    def suggest_group(self, material_label: str, quotes: Sequence[Quote]) -> str:
        """Group chosen for the same material in the latest saved quote; else cotton-like names → Cotton (phương án)."""
        key = label_key(material_label)
        for quote in sorted(quotes, key=lambda q: q.created_at, reverse=True):
            for component in quote.components:
                if label_key(component.material_label) == key and component.price_group_id:
                    return component.price_group_id
        if key.startswith(("CM", "CD")) or "COTTON" in key:
            return COTTON_PLAN_ID
        return ""

    # ---- BR-94 ----
    def component_loss(self, yarn: Yarn, component: YarnComponent) -> Decimal:
        """Tiêu hao lũy kế of the component's carding pass; no carding (or no detail) → the largest of the yarn."""
        if component.carding_stage:
            for detail in yarn.stage_details:
                if (
                    detail.stage_code == component.carding_stage
                    and label_key(detail.material_label) == label_key(component.material_label)
                    and (component.pass_no is None or detail.pass_no in (None, component.pass_no))
                ):
                    return detail.cumulative_loss
        return max((d.cumulative_loss for d in yarn.stage_details), default=ZERO)

    # ---- BR-96 ----
    def ensure_valid(
        self,
        yarn: Yarn | None,
        line: PriceLine | None,
        market: MaterialMarket,
        order_qty: Decimal,
        norm_factor: Decimal,
        gp: Decimal,
        commission: Decimal,
        incoterm: Incoterm,
        fi: Decimal,
        groups: Sequence[tuple[str, str]],
        accounting_code: str,
        customer: str,
        note: str,
    ) -> None:
        """``groups`` = (material label, chosen group id) of every component."""
        if yarn is None:
            raise YarnValidationError(MSG_NO_YARN)
        if yarn.status not in PRICED or line is None or line.total_vnd <= 0:
            raise YarnValidationError(MSG_NOT_PRICED.format(code=yarn.yarn_code))
        if market == MaterialMarket.CHUNG:
            raise YarnValidationError(MSG_MARKET)
        if order_qty <= 0:
            raise YarnValidationError(MSG_QTY)
        if norm_factor <= 0:
            raise YarnValidationError(MSG_FACTOR)
        if gp < 0 or commission < 0:
            raise YarnValidationError(MSG_NEGATIVE)
        if gp + commission >= ONE:
            raise YarnValidationError(MSG_MARGIN)
        if incoterm == Incoterm.CIF and fi < 0:
            raise YarnValidationError(MSG_FI)
        for material, group_id in groups:
            if not group_id:
                raise YarnValidationError(MSG_NO_GROUP.format(material=material))
        if len(accounting_code) > 50:
            raise YarnValidationError(MSG_CODE_LONG)
        if len(customer) > 100:
            raise YarnValidationError(MSG_CUSTOMER_LONG)
        if len(note) > 500:
            raise YarnValidationError(MSG_NOTE_LONG)

    def price_line(self, yarn: Yarn, kind: PriceKind) -> PriceLine | None:
        wanted = LineType.THUONG if kind == PriceKind.THUONG else LineType.THI_NGHIEM
        return next((line for line in yarn.lines if line.line_type == wanted), None)

    # ---- BR-94 / BR-95 ----
    def material_components(
        self, yarn: Yarn, chosen: dict[str, str], averages: Sequence[GroupAverage], market: MaterialMarket
    ) -> tuple[list[QuoteComponent], list[str]]:
        """Components with their group price (BR-92) → (components, groups without price notes)."""
        components: list[QuoteComponent] = []
        missing: list[str] = []
        for component in yarn.components:
            group_id = chosen.get(component.material_label, "")
            loss = self.component_loss(yarn, component)
            found = next((a for a in averages if a.group_id == group_id and a.market == market), None)
            if found is None or found.net is None or found.average is None:
                missing.append(found.note if found is not None and found.note else group_id)
                components.append(
                    QuoteComponent(
                        material_label=component.material_label,
                        ratio=component.ratio,
                        loss=loss,
                        price_group_id=group_id,
                        price_group=found.group_name if found else "",
                    )
                )
                continue
            cost = component.ratio * found.net / (ONE - loss) if loss < ONE else ZERO
            components.append(
                QuoteComponent(
                    material_label=component.material_label,
                    ratio=component.ratio,
                    loss=loss,
                    price_group_id=group_id,
                    price_group=found.group_name,
                    average_usd=found.average,
                    recovery_usd=found.recovery,
                    net_usd=found.net,
                    cost_usd=cost,
                )
            )
        return components, missing

    def yarn_stock(
        self, accounting_code: str, lines: Sequence[StockLine], rate: Decimal
    ) -> tuple[Decimal, Decimal | None]:
        """BR-95 sợi tồn: (SL tồn, giá tồn USD/kg) of the finished-yarn codes with the same first 18 characters."""
        core = accounting_code.strip().upper()[:CORE_LENGTH]
        if not core:
            return ZERO, None
        found = [
            line
            for line in lines
            if line.section == StockSection.SOI_THANH_PHAM
            and line.accounting_code[:CORE_LENGTH] == core
            and line.closing_qty > 0
        ]
        qty = sum((line.closing_qty for line in found), ZERO)
        if qty <= 0:
            return ZERO, None
        return qty, sum((line.closing_value for line in found), ZERO) / rate / qty

    def calculate(
        self,
        base: Quote,
        components: list[QuoteComponent],
        norm_vnd: Decimal,
        stock_qty: Decimal,
        stock_cost: Decimal | None,
    ) -> Quote:
        """BR-95 on the inputs already set in ``base`` (rate, factor, GP, commission, incoterm, F&I, order qty)."""
        material = sum((c.cost_usd for c in components), ZERO)
        norm = norm_vnd / base.exchange_rate * base.norm_factor
        new_cost = material + norm
        if stock_cost is not None and stock_qty > 0:
            average = (stock_qty * stock_cost + base.order_qty * new_cost) / (stock_qty + base.order_qty)
        else:
            average = new_cost
        fob = average / (ONE - base.gp_percent - base.commission_percent)
        cif = fob + base.fi_usd if base.incoterm == Incoterm.CIF else None
        return base.model_copy(
            update={
                "components": components,
                "norm_vnd": norm_vnd,
                "material_usd": material,
                "norm_usd": norm,
                "new_cost_usd": new_cost,
                "stock_qty": stock_qty if stock_cost is not None else ZERO,
                "stock_cost_usd": stock_cost,
                "avg_cost_usd": average,
                "fob_usd": fob,
                "cif_usd": cif,
            }
        )

    # ---- BR-97 ----
    def next_number(self, used: Sequence[str], today: date) -> str:
        top = 0
        for number in used:
            match = QUOTE_NO.match(number)
            if match and int(match.group(1)) == today.year:
                top = max(top, int(match.group(2)))
        return f"BG-{today.year}-{top + 1:04d}"

    def ensure_can_delete(self, quote: Quote, username: str | None, is_so: bool) -> None:
        if not is_so and quote.created_username != (username or ""):
            raise YarnValidationError(MSG_DELETE)

    # ---- BR-98 ----
    def accounting_suggestions(
        self, yarn: Yarn, family: Sequence[Yarn], stock_lines: Sequence[StockLine]
    ) -> list[tuple[str, str, Decimal]]:
        """(code, name, closing qty) - codes of the yarn's price lines first, then finished-yarn stock with the same blend."""
        stock = {line.accounting_code: line for line in stock_lines if line.section == StockSection.SOI_THANH_PHAM}
        by_core: dict[str, Decimal] = {}
        for line in stock.values():
            core = line.accounting_code[:CORE_LENGTH]
            by_core[core] = by_core.get(core, ZERO) + line.closing_qty
        found: dict[str, tuple[str, str, Decimal]] = {}
        for member in family:
            for line in member.lines:
                code = (line.accounting_code or "").strip().upper()
                if code and code not in found:
                    found[code] = (code, member.yarn_name, by_core.get(code[:CORE_LENGTH], ZERO))
        blend = BlendBusiness()
        target = blend.parse(yarn.yarn_name)
        if target.readable:
            for line in sorted(stock.values(), key=lambda s: s.accounting_code):
                if line.accounting_code in found:
                    continue
                if blend.parse(line.item_name).same_blend(target):
                    found[line.accounting_code] = (line.accounting_code, line.item_name, line.closing_qty)
        return list(found.values())

    # ---- UC-63 ----
    def filter(
        self,
        quotes: Sequence[Quote],
        date_from: date | None,
        date_to: date | None,
        period: str,
        customer: str,
        search: str,
    ) -> list[Quote]:
        """Bộ lọc của "Các lần đã tính", newest first."""
        needle = label_key(search)
        found = []
        for quote in quotes:
            day = quote.created_at.date()
            if (date_from and day < date_from) or (date_to and day > date_to):
                continue
            if period and quote.period != period:
                continue
            if customer and label_key(quote.customer_name) != label_key(customer):
                continue
            haystack = label_key(f"{quote.quote_no} {quote.yarn_name} {quote.accounting_code} {quote.line_code}")
            if needle and needle not in haystack:
                continue
            found.append(quote)
        return sorted(found, key=lambda q: q.created_at, reverse=True)
