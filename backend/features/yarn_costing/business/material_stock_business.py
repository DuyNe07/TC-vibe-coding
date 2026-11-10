"""Đợt 2 (bổ sung 2026-11-10): BR-86 / BR-87 đọc và lưu file kho tháng, BR-90 / BR-91 đọc và lưu hàng sắp về."""

import re
from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from backend.core.base import BaseBusiness
from backend.features.yarn_costing.models.enums import (
    FactoryCode,
    MaterialDecision,
    MaterialMarket,
    PriceCurrency,
    StockSection,
)
from backend.features.yarn_costing.models.material_price import (
    ArrivalLot,
    ArrivalMapping,
    StockItemSetting,
    StockLine,
)
from backend.shared.utils.text import strip_accents

CORE_LENGTH = 18  # BR-86 / BR-95: the part of an accounting code before its suffix
PERIOD_PATTERN = re.compile(r"(\d{1,2})\s*[-/.]\s*(\d{1,2})\s*[-/.]\s*(\d{4})")
VND_THRESHOLD = Decimal(100)  # BR-90: unit price above 100 = VND/kg
NUMBER_FIELDS = {
    "opening_qty": "SL_TON",
    "opening_value": "GT_TON",
    "in_qty": "SL_NHAP",
    "in_value": "GT_NHAP",
    "out_qty": "SL_XUAT",
    "out_value": "GT_XUAT",
    "closing_qty": "SL_CUOI",
    "closing_value": "GT_CUOI1",
}
MSG_NOT_NUMBER = "Cột {column} không phải số."
MSG_DUPLICATE = "Mã '{code}' bị trùng trong file."
MSG_NO_TYPE = "Thiếu mô tả hàng (TYPE)."
MSG_QUANTITY = "Số lượng phải lớn hơn 0."
MSG_NO_PRICE = "Chưa có đơn giá."
MSG_RECEIVING = "Giá nhập kho phải lớn hơn 0."
MSG_NO_ETA = "Chưa có ngày về kho."
MSG_WAREHOUSE = "Không nhận ra kho '{warehouse}'."
MSG_TOO_LONG = "{field} tối đa {limit} ký tự."


def to_number(value: object) -> Decimal | None:
    """Excel cell → Decimal (empty = None; text that is not a number raises InvalidOperation)."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        raise InvalidOperation
    if isinstance(value, int | float | Decimal):
        number = Decimal(str(value))
        if not number.is_finite():
            raise InvalidOperation
        return number
    text = str(value).strip().replace(" ", "").replace(",", "")
    return Decimal(text)


def to_date(value: object) -> date | None:
    """Excel cell → date ('17/09/2026', datetime, date); anything else → None."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    match = PERIOD_PATTERN.search(str(value or ""))
    if not match:
        return None
    day, month, year = (int(g) for g in match.groups())
    try:
        return date(year, month, day)
    except ValueError:
        return None


def text_key(value: object) -> str:
    """BR-91: upper case, no accents, single spaces."""
    return " ".join(strip_accents(str(value or "")).upper().split())


def clean(value: object) -> str:
    return " ".join(str(value or "").split())


class MaterialStockBusiness(BaseBusiness[StockLine]):
    # ---- BR-86 ----
    def period_of(self, text: str) -> str:
        """'Từ ngày 01-10-2026 đến ngày 31-10-2026' → '2026-10' ('' when unreadable)."""
        match = PERIOD_PATTERN.search(text or "")
        if not match:
            return ""
        _, month, year = (int(g) for g in match.groups())
        return f"{year:04d}-{month:02d}" if 1 <= month <= 12 else ""

    def section_of(self, ica_name: str) -> StockSection:
        key = text_key(ica_name)
        if key in ("BONG", "XO"):
            return StockSection.NGUYEN_LIEU
        if key == "DO CTY SX":
            return StockSection.SOI_THANH_PHAM
        return StockSection.PHU_LIEU

    def market_of(self, code: str) -> MaterialMarket:
        suffix = code.strip().upper()[CORE_LENGTH:]
        if "D" in suffix:
            return MaterialMarket.NOI_DIA
        if "R" in suffix:
            return MaterialMarket.XUAT_KHAU
        return MaterialMarket.CHUNG

    def read_stock_rows(
        self, rows: Sequence[tuple[int, dict[str, object]]], month_id: str, period: str
    ) -> tuple[list[StockLine], list[tuple[int, str, str]]]:
        """Rows keyed by field name (ica, code, name, unit + NUMBER_FIELDS) → (lines, rejected (row, code, reason))."""
        lines: list[tuple[int, StockLine]] = []
        rejected: list[tuple[int, str, str]] = []
        for excel_row, cells in rows:
            code = str(cells.get("code") or "").strip().upper()
            if not code:
                continue  # total row at the end of the report
            values: dict[str, Decimal] = {}
            problem = ""
            for field, label in NUMBER_FIELDS.items():
                try:
                    value = to_number(cells.get(field))
                except (InvalidOperation, ValueError):
                    problem = MSG_NOT_NUMBER.format(column=label)
                    break
                values[field] = value if value is not None else Decimal(0)
            if problem:
                rejected.append((excel_row, code, problem))
                continue
            ica = clean(cells.get("ica"))
            lines.append(
                (
                    excel_row,
                    StockLine(
                        month_id=month_id,
                        period=period,
                        section=self.section_of(ica),
                        ica_name=ica,
                        accounting_code=code,
                        item_name=clean(cells.get("name")),
                        unit=clean(cells.get("unit")),
                        **values,
                    ),
                )
            )
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

    # ---- BR-87 ----
    def merge_settings(
        self, lines: Sequence[StockLine], existing: dict[str, StockItemSetting]
    ) -> tuple[list[StockItemSetting], int]:
        """New material codes → "Chưa khai báo" with the suggested market; known codes keep their setting (name updated).
        Returns (settings to save, number of new codes)."""
        changed: list[StockItemSetting] = []
        new_count = 0
        for line in lines:
            if line.section != StockSection.NGUYEN_LIEU:
                continue
            current = existing.get(line.accounting_code)
            if current is None:
                changed.append(
                    StockItemSetting(
                        accounting_code=line.accounting_code,
                        item_name=line.item_name,
                        ica_name=line.ica_name,
                        decision=MaterialDecision.CHUA_KHAI_BAO,
                        market=self.market_of(line.accounting_code),
                    )
                )
                new_count += 1
            elif current.item_name != line.item_name or current.ica_name != line.ica_name:
                changed.append(current.model_copy(update={"item_name": line.item_name, "ica_name": line.ica_name}))
        return changed, new_count

    # ---- BR-90 ----
    def warehouse_of(self, warehouse: str) -> tuple[FactoryCode | None, MaterialMarket]:
        compact = text_key(warehouse).replace(" ", "")
        factory = (
            FactoryCode.S4 if compact.startswith("MILL4") else FactoryCode.S1 if compact.startswith("MILL1") else None
        )
        if "KDND" in compact:
            return factory, MaterialMarket.NOI_DIA
        if "SXXK" in compact:
            return factory, MaterialMarket.XUAT_KHAU
        return factory, MaterialMarket.CHUNG

    def currency_of(self, unit_price: Decimal) -> PriceCurrency:
        return PriceCurrency.VND if unit_price > VND_THRESHOLD else PriceCurrency.USD

    def check_lot(self, lot: dict[str, object]) -> str:
        """BR-90 checks of one lot (file row or screen row); '' = valid."""
        if not clean(lot.get("description")):
            return MSG_NO_TYPE
        for field, label, limit in (
            ("supplier", "Nhà cung cấp", 200),
            ("description", "Mô tả", 300),
            ("note", "Ghi chú", 500),
        ):
            if len(clean(lot.get(field))) > limit:
                return MSG_TOO_LONG.format(field=label, limit=limit)
        try:
            quantity = to_number(lot.get("quantity"))
        except (InvalidOperation, ValueError):
            quantity = None
        if quantity is None or quantity <= 0:
            return MSG_QUANTITY
        try:
            price = to_number(lot.get("unit_price"))
        except (InvalidOperation, ValueError):
            price = None
        if price is None or price <= 0:
            return MSG_NO_PRICE
        try:
            receiving = to_number(lot.get("receiving_price"))
        except (InvalidOperation, ValueError):
            return MSG_RECEIVING
        if receiving is not None and receiving <= 0:
            return MSG_RECEIVING
        if to_date(lot.get("eta_warehouse")) is None:
            return MSG_NO_ETA
        factory, _ = self.warehouse_of(clean(lot.get("warehouse")))
        if factory is None and not lot.get("factory_code"):
            return MSG_WAREHOUSE.format(warehouse=clean(lot.get("warehouse")))
        return ""

    def read_arrival_rows(
        self, rows: Sequence[tuple[int, dict[str, object]]], import_id: str
    ) -> tuple[list[ArrivalLot], list[tuple[int, str, str]]]:
        """5.11 rows keyed by field name → (lots, rejected (row, supplier, reason)); empty SUPPLIER rows are skipped."""
        lots: list[ArrivalLot] = []
        rejected: list[tuple[int, str, str]] = []
        for excel_row, cells in rows:
            supplier = clean(cells.get("supplier"))
            if not supplier:
                continue
            problem = self.check_lot(cells)
            if problem:
                rejected.append((excel_row, supplier, problem))
                continue
            lots.append(self.lot_from(cells, import_id=import_id))
        return lots, rejected

    def lot_from(self, cells: dict[str, object], import_id: str | None = None) -> ArrivalLot:
        """A lot from checked cells (check_lot passed). Market / factory come from WAREHOUSE unless given."""
        unit_price = to_number(cells.get("unit_price")) or Decimal(0)
        factory, market = self.warehouse_of(clean(cells.get("warehouse")))
        given_factory = cells.get("factory_code")
        given_market = cells.get("market")
        return ArrivalLot(
            import_id=import_id,
            supplier=clean(cells.get("supplier")),
            commodity=clean(cells.get("commodity")),
            description=clean(cells.get("description")),
            spec=clean(cells.get("spec")),
            contract_no=clean(cells.get("contract_no")),
            contract_date=to_date(cells.get("contract_date")),
            quantity=to_number(cells.get("quantity")) or Decimal(0),
            unit_price=unit_price,
            price_currency=self.currency_of(unit_price),
            receiving_price=to_number(cells.get("receiving_price")),
            term=clean(cells.get("term"))[:20],
            origin_country=clean(cells.get("origin_country"))[:100],
            shipment_date=to_date(cells.get("shipment_date")),
            eta_port=to_date(cells.get("eta_port")),
            eta_warehouse=to_date(cells.get("eta_warehouse")) or date.today(),
            warehouse=clean(cells.get("warehouse"))[:100],
            factory_code=FactoryCode(str(given_factory)) if given_factory else (factory or FactoryCode.S4),
            market=MaterialMarket(str(given_market)) if given_market else market,
            note=clean(cells.get("note")),
        )

    # ---- BR-91 ----
    def mapping_key(self, supplier: str, description: str) -> tuple[str, str]:
        return text_key(supplier), text_key(description)

    def new_mappings(
        self, lots: Sequence[ArrivalLot], existing: dict[tuple[str, str], ArrivalMapping]
    ) -> list[ArrivalMapping]:
        """Pairs (supplier, description) not declared yet → "Chưa khai báo"."""
        added: dict[tuple[str, str], ArrivalMapping] = {}
        for lot in lots:
            key = self.mapping_key(lot.supplier, lot.description)
            if key in existing or key in added:
                continue
            added[key] = ArrivalMapping(
                supplier_key=key[0], description_key=key[1], supplier=lot.supplier, description=lot.description
            )
        return list(added.values())
