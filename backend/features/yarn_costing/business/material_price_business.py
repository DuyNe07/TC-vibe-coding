"""Đợt 2 (bổ sung 2026-11-10): BR-85 nhóm giá, BR-88 khai báo tháng, BR-89 tỷ giá tháng, BR-92 giá nguyên liệu bình quân,
BR-99 so giá xuất kho."""

import calendar
from collections.abc import Callable, Sequence
from datetime import date
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.enums import (
    CottonOrigin,
    FactoryCode,
    MaterialDecision,
    MaterialMarket,
    PriceCurrency,
    PriceGroupKind,
    StockSection,
)
from backend.features.yarn_costing.models.exchange_rate import ExchangeRate
from backend.features.yarn_costing.models.material_price import (
    COTTON_PLAN_ID,
    COTTON_PLAN_NAME,
    ArrivalLot,
    ArrivalMapping,
    AverageSource,
    CottonShare,
    GroupAverage,
    GroupRecovery,
    MaterialPriceGroup,
    MonthInputs,
    MonthlyMaterialSetting,
    Quote,
    StockItemSetting,
    StockLine,
    StockOutCompareRow,
)

KeyOf = Callable[[str, str], tuple[str, str]]
ZERO = Decimal(0)
ONE = Decimal(1)
HUNDRED = Decimal(100)
CORE_LENGTH = 18
TOLERANCE = Decimal("0.00001")
MARKETS = (MaterialMarket.NOI_DIA, MaterialMarket.XUAT_KHAU)
DEFAULT_NORM_FACTOR = Decimal("1.10")
DEFAULT_FI = Decimal("0.03")
MSG_NO_RATE = "Chưa có tỷ giá cho tháng {month}. Phòng SO thêm tỷ giá ở màn Dữ liệu nền."
MSG_GROUP_NAME = "Vui lòng nhập tên nhóm."
MSG_GROUP_LONG = "Tên nhóm tối đa 100 ký tự."
MSG_GROUP_DUP = "Đã có nhóm giá '{name}'."
MSG_GROUP_ORIGIN = "Nhóm cotton phải chọn xuất xứ."
MSG_NOTE_LONG = "Ghi chú tối đa 500 ký tự."
MSG_FACTOR = "Hệ số phải lớn hơn 0."
MSG_FI = "F&I không được âm."
MSG_RECOVERY = "Hồi phế của nhóm '{group}' không được âm."
MSG_RECOVERY_DUP = "Nhóm '{group}' bị khai báo hồi phế hai lần."
MSG_ORIGIN_DUP = "Xuất xứ '{origin}' bị lặp trong phương án."
MSG_PLAN_TOTAL = "Tổng tỷ lệ phương án pha bông phải bằng 100% (hiện là {total}%)."
MSG_PLAN_PERCENT = "Tỷ lệ của xuất xứ '{origin}' phải lớn hơn 0."
MSG_NO_DATA = "Nhóm '{group}' ({market}) chưa có giá tháng {month}: không có tồn và hàng về."
MSG_NO_PLAN = "Chưa khai báo phương án pha bông tháng {month}."
MSG_NO_STOCK = "Chưa có file kho tháng {month} (tháng trước tháng tính). Vui lòng tải ở thẻ File kho."
MSG_LEVEL = "Mức cảnh báo phải là số lớn hơn 0."
NOTE_NO_AVG = "chưa có giá BQ tháng {month}"
NOTE_UNDECLARED = "chưa khai báo nhóm"
NOTE_NO_QUOTE = "chưa tính giá báo khách"
WARN_GAP = "🔴 Lệch nhiều"
STOCK_KIND = "Tồn"
ARRIVAL_KIND = "Hàng về"


def month_text(period: str) -> str:
    year, month = period.split("-")
    return f"{month}/{year}"


def previous_period(period: str) -> str:
    year, month = (int(p) for p in period.split("-"))
    return f"{year - 1:04d}-12" if month == 1 else f"{year:04d}-{month - 1:02d}"


def month_end(period: str) -> date:
    year, month = (int(p) for p in period.split("-"))
    return date(year, month, calendar.monthrange(year, month)[1])


def in_period(day: date, period: str) -> bool:
    return f"{day.year:04d}-{day.month:02d}" == period


def name_key(name: str) -> str:
    return " ".join(name.split()).casefold()


class MaterialPriceBusiness(BaseBusiness[MaterialPriceGroup]):
    # ---- BR-85 ----
    def ensure_group_valid(
        self,
        name: str,
        kind: PriceGroupKind,
        origin: CottonOrigin | None,
        note: str,
        others: Sequence[MaterialPriceGroup],
    ) -> None:
        clean = " ".join(name.split())
        if not clean:
            raise YarnValidationError(MSG_GROUP_NAME)
        if len(clean) > 100:
            raise YarnValidationError(MSG_GROUP_LONG)
        if name_key(clean) == name_key(COTTON_PLAN_NAME) or any(name_key(g.name) == name_key(clean) for g in others):
            raise YarnValidationError(MSG_GROUP_DUP.format(name=clean))
        if kind == PriceGroupKind.COTTON and origin is None:
            raise YarnValidationError(MSG_GROUP_ORIGIN)
        if len(note) > 500:
            raise YarnValidationError(MSG_NOTE_LONG)

    # ---- BR-88 ----
    def draft(self, period: str, previous: MonthlyMaterialSetting | None) -> MonthlyMaterialSetting:
        """Month without a saved version: copy of the latest earlier one (or the defaults)."""
        if previous is None:
            return MonthlyMaterialSetting(period=period, norm_factor=DEFAULT_NORM_FACTOR, default_fi=DEFAULT_FI)
        return MonthlyMaterialSetting(
            period=period,
            norm_factor=previous.norm_factor,
            default_fi=previous.default_fi,
            cotton_plan_note=previous.cotton_plan_note,
            cotton_plan=list(previous.cotton_plan),
            recoveries=list(previous.recoveries),
            copied_from=previous.period,
        )

    def latest_before(self, period: str, settings: Sequence[MonthlyMaterialSetting]) -> MonthlyMaterialSetting | None:
        earlier = [s for s in settings if s.period < period]
        return max(earlier, key=lambda s: s.period) if earlier else None

    def ensure_setting_valid(
        self,
        norm_factor: Decimal,
        default_fi: Decimal,
        plan: Sequence[CottonShare],
        recoveries: Sequence[GroupRecovery],
        group_names: dict[str, str],
    ) -> None:
        if norm_factor <= 0:
            raise YarnValidationError(MSG_FACTOR)
        if default_fi < 0:
            raise YarnValidationError(MSG_FI)
        seen: set[str] = set()
        for recovery in recoveries:
            label = group_names.get(recovery.group_id, recovery.group_id)
            if recovery.usd_per_kg < 0:
                raise YarnValidationError(MSG_RECOVERY.format(group=label))
            if recovery.group_id in seen:
                raise YarnValidationError(MSG_RECOVERY_DUP.format(group=label))
            seen.add(recovery.group_id)
        origins: set[CottonOrigin] = set()
        for share in plan:
            if share.origin in origins:
                raise YarnValidationError(MSG_ORIGIN_DUP.format(origin=share.origin.value))
            if share.percent <= 0:
                raise YarnValidationError(MSG_PLAN_PERCENT.format(origin=share.origin.value))
            origins.add(share.origin)
        if plan:
            total = sum((s.percent for s in plan), ZERO)
            if abs(total - ONE) > TOLERANCE:
                shown = f"{(total * HUNDRED).normalize():f}".replace(".", ",")
                raise YarnValidationError(MSG_PLAN_TOTAL.format(total=shown))

    def setting_of(self, period: str, settings: Sequence[MonthlyMaterialSetting]) -> MonthlyMaterialSetting:
        """Saved version of month M, else the draft copied from the latest earlier month (BR-88)."""
        saved = next((s for s in settings if s.period == period), None)
        return saved if saved is not None else self.draft(period, self.latest_before(period, settings))

    def month_view(
        self, inputs: MonthInputs, mapping_key: KeyOf
    ) -> tuple[Decimal | None, MonthlyMaterialSetting, list[GroupAverage], str]:
        """(tỷ giá M, khai báo tháng M, BR-92 averages, problem) - problem = missing rate or missing stock file of M−1."""
        period = inputs.period
        monthly = self.setting_of(period, inputs.monthly)
        rate = self.rate_of_month(inputs.rates, period)
        if rate is None or rate <= 0:
            return None, monthly, [], MSG_NO_RATE.format(month=month_text(period))
        if inputs.stock_month is None:
            return rate, monthly, [], MSG_NO_STOCK.format(month=month_text(previous_period(period)))
        averages = self.averages(
            period,
            inputs.stock_lines,
            inputs.settings,
            inputs.groups,
            inputs.lots,
            inputs.mappings,
            mapping_key,
            monthly,
            rate,
        )
        return rate, monthly, averages, ""

    # ---- BR-89 ----
    def rate_of_month(self, rates: Sequence[ExchangeRate], period: str) -> Decimal | None:
        end = month_end(period)
        found = [r for r in rates if r.effective_date <= end]
        if not found:
            return None
        return max(found, key=lambda r: (r.effective_date, r.created_at)).rate

    def ensure_rate(self, rate: Decimal | None, period: str) -> Decimal:
        if rate is None or rate <= 0:
            raise YarnValidationError(MSG_NO_RATE.format(month=month_text(period)))
        return rate

    # ---- BR-92 ----
    def averages(
        self,
        period: str,
        stock_lines: Sequence[StockLine],
        settings: dict[str, StockItemSetting],
        groups: dict[str, MaterialPriceGroup],
        lots: Sequence[ArrivalLot],
        mappings: dict[tuple[str, str], ArrivalMapping],
        mapping_key: KeyOf,
        monthly: MonthlyMaterialSetting,
        rate: Decimal,
    ) -> list[GroupAverage]:
        """Average of every group × market for month M (stock of month M−1 + S4 lots arriving in M), cotton plan first.
        ``mapping_key(supplier, description)`` gives the 4.27 key of a lot."""
        pools: dict[tuple[str, MaterialMarket], GroupAverage] = {
            (gid, market): GroupAverage(group_id=gid, group_name=g.name, market=market)
            for gid, g in groups.items()
            for market in MARKETS
        }
        for line in stock_lines:
            if line.section != StockSection.NGUYEN_LIEU or line.closing_qty <= 0:
                continue
            setting = settings.get(line.accounting_code)
            if (
                setting is None
                or setting.decision != MaterialDecision.THEO_NHOM
                or setting.price_group_id not in groups
            ):
                continue
            value = line.closing_value / rate
            for market in self._markets(setting.market):
                pool = pools[(setting.price_group_id, market)]
                pools[(setting.price_group_id, market)] = pool.model_copy(
                    update={
                        "stock_qty": pool.stock_qty + line.closing_qty,
                        "stock_value": pool.stock_value + value,
                        "sources": [
                            *pool.sources,
                            AverageSource(
                                kind=STOCK_KIND,
                                code=line.accounting_code,
                                name=line.item_name,
                                market=setting.market,
                                quantity=line.closing_qty,
                                unit_usd=value / line.closing_qty,
                            ),
                        ],
                    }
                )
        for lot in lots:
            if lot.factory_code != FactoryCode.S4 or not in_period(lot.eta_warehouse, period):
                continue
            mapping = mappings.get(mapping_key(lot.supplier, lot.description))
            if (
                mapping is None
                or mapping.decision != MaterialDecision.THEO_NHOM
                or mapping.price_group_id not in groups
            ):
                continue
            unit = self.lot_unit_usd(lot, rate)
            for market in self._markets(lot.market):
                pool = pools[(mapping.price_group_id, market)]  # type: ignore[index]
                pools[(mapping.price_group_id, market)] = pool.model_copy(  # type: ignore[index]
                    update={
                        "arrival_qty": pool.arrival_qty + lot.quantity,
                        "arrival_value": pool.arrival_value + lot.quantity * unit,
                        "sources": [
                            *pool.sources,
                            AverageSource(
                                kind=ARRIVAL_KIND,
                                code=lot.contract_no,
                                name=f"{lot.supplier} - {lot.description}",
                                market=lot.market,
                                quantity=lot.quantity,
                                unit_usd=unit,
                            ),
                        ],
                    }
                )
        month = month_text(period)
        result: list[GroupAverage] = []
        for (gid, market), pool in pools.items():
            recovery = monthly.recovery_of(gid)
            if pool.total_qty > 0:
                average = (pool.stock_value + pool.arrival_value) / pool.total_qty
                result.append(
                    pool.model_copy(update={"average": average, "recovery": recovery, "net": average - recovery})
                )
            else:
                note = MSG_NO_DATA.format(group=pool.group_name, market=market.value, month=month)
                result.append(pool.model_copy(update={"recovery": recovery, "note": note}))
        plans = [self._cotton_plan(market, result, groups, monthly, month) for market in MARKETS]
        result.sort(key=lambda a: (a.group_name.casefold(), a.market != MaterialMarket.NOI_DIA))
        return [*plans, *result]

    def lot_unit_usd(self, lot: ArrivalLot, rate: Decimal) -> Decimal:
        """BR-92: Giá nhập kho (USD/kg), empty → Unit price (VND ÷ tỷ giá M)."""
        if lot.receiving_price is not None:
            return lot.receiving_price
        return lot.unit_price / rate if lot.price_currency == PriceCurrency.VND else lot.unit_price

    def _markets(self, market: MaterialMarket) -> tuple[MaterialMarket, ...]:
        return MARKETS if market == MaterialMarket.CHUNG else (market,)

    def _cotton_plan(
        self,
        market: MaterialMarket,
        averages: Sequence[GroupAverage],
        groups: dict[str, MaterialPriceGroup],
        monthly: MonthlyMaterialSetting,
        month: str,
    ) -> GroupAverage:
        recovery = monthly.recovery_of(COTTON_PLAN_ID)
        base = GroupAverage(group_id=COTTON_PLAN_ID, group_name=COTTON_PLAN_NAME, market=market, recovery=recovery)
        if not monthly.cotton_plan:
            return base.model_copy(update={"note": MSG_NO_PLAN.format(month=month)})
        total = ZERO
        parts: list[str] = []
        stock_qty = arrival_qty = ZERO
        sources: list[AverageSource] = []
        for share in monthly.cotton_plan:
            pools = [
                a
                for a in averages
                if a.market == market
                and a.group_id in groups
                and groups[a.group_id].kind == PriceGroupKind.COTTON
                and groups[a.group_id].origin == share.origin
            ]
            qty = sum((a.total_qty for a in pools), ZERO)
            if qty <= 0:
                note = MSG_NO_DATA.format(group=f"Cotton {share.origin.value}", market=market.value, month=month)
                return base.model_copy(update={"note": note})
            origin_avg = sum((a.stock_value + a.arrival_value for a in pools), ZERO) / qty
            total += share.percent * origin_avg
            stock_qty += sum((a.stock_qty for a in pools), ZERO)
            arrival_qty += sum((a.arrival_qty for a in pools), ZERO)
            sources += [s for a in pools for s in a.sources]
            parts.append(f"{share.origin.value} {(share.percent * HUNDRED).normalize():f}%")
        return base.model_copy(
            update={
                "average": total,
                "net": total - recovery,
                "stock_qty": stock_qty,
                "arrival_qty": arrival_qty,
                "note": " + ".join(parts).replace(".", ","),
                "sources": sources,
            }
        )

    def find_average(
        self, averages: Sequence[GroupAverage], group_id: str, market: MaterialMarket
    ) -> GroupAverage | None:
        return next((a for a in averages if a.group_id == group_id and a.market == market), None)

    def undeclared(
        self,
        period: str,
        stock_lines: Sequence[StockLine],
        settings: dict[str, StockItemSetting],
        lots: Sequence[ArrivalLot],
        mappings: dict[tuple[str, str], ArrivalMapping],
        mapping_key: KeyOf,
    ) -> tuple[int, int]:
        """UC-59 warning: (stock codes with closing qty still "Chưa khai báo", S4 lots of month M without a group)."""
        codes = sum(
            1
            for line in stock_lines
            if line.section == StockSection.NGUYEN_LIEU
            and line.closing_qty > 0
            and (s := settings.get(line.accounting_code)) is not None
            and s.decision == MaterialDecision.CHUA_KHAI_BAO
        )
        lot_count = 0
        for lot in lots:
            if lot.factory_code != FactoryCode.S4 or not in_period(lot.eta_warehouse, period):
                continue
            mapping = mappings.get(mapping_key(lot.supplier, lot.description))
            if mapping is None or mapping.decision == MaterialDecision.CHUA_KHAI_BAO:
                lot_count += 1
        return codes, lot_count

    # ---- BR-99 ----
    def ensure_level(self, level: Decimal) -> None:
        if level <= 0:
            raise YarnValidationError(MSG_LEVEL)

    def compare_stock_out(
        self,
        period: str,
        lines: Sequence[StockLine],
        settings: dict[str, StockItemSetting],
        groups: dict[str, MaterialPriceGroup],
        averages: Sequence[GroupAverage] | None,
        quotes: Sequence[Quote],
        rate: Decimal,
        level: Decimal,
    ) -> list[StockOutCompareRow]:
        """``averages`` = BR-92 of month M (None when the stock file of M−1 is missing)."""
        rows: list[StockOutCompareRow] = []
        month = month_text(period)
        latest: dict[str, Quote] = {}
        for quote in sorted(quotes, key=lambda q: q.created_at):
            if quote.accounting_code:
                latest[quote.accounting_code[:CORE_LENGTH]] = quote
        for line in lines:
            if line.out_qty <= 0 or line.section == StockSection.PHU_LIEU:
                continue
            unit_vnd = line.out_value / line.out_qty
            row = StockOutCompareRow(
                section=line.section,
                accounting_code=line.accounting_code,
                item_name=line.item_name,
                out_qty=line.out_qty,
                out_unit_usd=unit_vnd / rate,
                out_unit_vnd=unit_vnd,
            )
            if line.section == StockSection.NGUYEN_LIEU:
                setting = settings.get(line.accounting_code)
                if setting is not None and setting.decision == MaterialDecision.KHONG_TINH:
                    continue
                if (
                    setting is None
                    or setting.decision != MaterialDecision.THEO_NHOM
                    or setting.price_group_id not in groups
                ):
                    rows.append(row.model_copy(update={"note": NOTE_UNDECLARED}))
                    continue
                market = MaterialMarket.NOI_DIA if setting.market == MaterialMarket.CHUNG else setting.market
                row = row.model_copy(
                    update={"group_name": groups[setting.price_group_id].name, "market": setting.market}  # type: ignore[index]
                )
                found = self.find_average(averages or [], setting.price_group_id, market)  # type: ignore[arg-type]
                if found is None or found.average is None:
                    rows.append(row.model_copy(update={"note": NOTE_NO_AVG.format(month=month)}))
                    continue
                rows.append(self._with_gap(row, found.average, level))
            else:
                quote = latest.get(line.accounting_code[:CORE_LENGTH])
                if quote is None:
                    rows.append(row.model_copy(update={"note": NOTE_NO_QUOTE}))
                    continue
                row = row.model_copy(update={"quote_no": quote.quote_no, "quote_date": quote.created_at.date()})
                rows.append(self._with_gap(row, quote.avg_cost_usd, level))
        rows.sort(key=lambda r: (r.difference_percent is None, -abs(r.difference_percent or ZERO)))
        return rows

    def _with_gap(self, row: StockOutCompareRow, compare: Decimal, level: Decimal) -> StockOutCompareRow:
        difference = row.out_unit_usd - compare
        percent = difference / compare * HUNDRED if compare > 0 else None
        return row.model_copy(
            update={
                "compare_usd": compare,
                "difference": difference,
                "difference_percent": percent,
                "is_gap": percent is not None and abs(percent) > level,
            }
        )
