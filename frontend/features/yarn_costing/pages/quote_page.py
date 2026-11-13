"""Screen 13 (`tinh-gia-bao-khach`) - Tính giá báo khách (UC-62, UC-63; đợt 2, bổ sung 2026-11-10)."""

from decimal import Decimal
from typing import Any

import streamlit as st

from backend.core.gateway import gateway
from backend.features.yarn_costing import YarnCostingController
from backend.features.yarn_costing.dto.common_dto import LineType, YarnStatus
from backend.features.yarn_costing.dto.material_dto import (
    CalculateQuoteRequest,
    CottonOrigin,
    CottonShareDTO,
    DeleteQuoteRequest,
    ExportQuotesRequest,
    GetQuoteFormRequest,
    Incoterm,
    ListQuotesRequest,
    MaterialMarket,
    PriceKind,
    QuoteDTO,
    QuoteFormResponse,
)
from backend.features.yarn_costing.dto.price_dto import ListPriceLinesRequest
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, editable_table, empty_state, panel, stat_row
from frontend.core.formatting import format_number
from frontend.features.yarn_costing.components.columns import count_col, datetime_col, money, percent, usd_col
from frontend.features.yarn_costing.components.dialogs import confirm_dialog
from frontend.features.yarn_costing.components.display import pct, plain, usd, vnd
from frontend.features.yarn_costing.components.flash import show_flash
from frontend.features.yarn_costing.components.material_ui import (
    current_period,
    material_denied,
    month_options,
    month_text,
    run_save,
    try_call,
)
from frontend.features.yarn_costing.components.permissions import action_state, explain

RESULT_KEY = "quote_result"
PRICED = (YarnStatus.DA_TINH_GIA, YarnStatus.CO_MA_KE_TOAN)
HUNDRED = Decimal(100)
COMPONENT_COLUMNS = ["Nguyên liệu", "Tỷ lệ %", "Tiêu hao %", "Nhóm giá"]
COTTON_PLAN_ID = "cotton-plan"  # nhóm cố định "Cotton (phương án)" (BR-92)
ORIGINS = [CottonOrigin.USA, CottonOrigin.BRAZIL, CottonOrigin.AUSTRALIA]


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value)) if value not in (None, "") else Decimal(0)
    except ArithmeticError:
        return Decimal(0)


def usd_text(value: Any) -> str:
    return "-" if value is None else format_number(float(value), 4)


class QuotePage(BasePage):
    title = "Tính giá báo khách"
    menu_group = "Sales"
    icon = "💵"
    slug = "tinh-gia-bao-khach"
    description = (
        "Giá vốn có nguyên liệu (bình quân với sợi tồn), GP, Commission → giá FOB / CIF; lưu và xuất các lần đã tính."
    )

    def render(self) -> None:
        if material_denied("UC-62"):
            return
        show_flash(self.state)
        feature = gateway.open(YarnCostingController)
        self._calculator(feature)
        self._history(feature)

    # ---- UC-62 ----
    def _calculator(self, feature: YarnCostingController) -> None:
        disabled, why = action_state("UC-62")
        lines = [
            r
            for r in feature.list_price_lines(ListPriceLinesRequest()).items
            if str(r.factory_code) == "S4" and r.line_type == LineType.THUONG and r.status in PRICED and r.total_vnd > 0
        ]
        labels = {
            r.line_code: f"{r.line_code} - {r.yarn_name}"
            + (f" · {r.customer_names_text}" if r.customer_names_text else "")
            + (f" · KT {r.accounting_code}" if r.accounting_code else "")
            + (f" · tên cũ {r.old_names_text}" if r.old_names_text else "")  # BR-108
            + (f" · KT gộp {', '.join(r.merged_accounting_codes)}" if r.merged_accounting_codes else "")
            for r in lines
        }
        with panel("Tính giá", icon="🧮"):
            c1, c2 = st.columns([1, 3])
            period = c1.selectbox(
                "Tháng tính", month_options(), index=month_options().index(current_period()), format_func=month_text,
                key=self.key("period"),
            )  # fmt: skip
            line_code = c2.selectbox(
                "Sợi (dòng giá Thường của S4)",
                list(labels),
                index=None,
                placeholder="Gõ mã, tên sợi, tên theo khách hoặc mã kế toán",
                format_func=lambda c: labels.get(c, c),
                key=self.key("line"),
            )
            if not line_code:
                empty_state("Chọn sợi để tính giá báo khách.")
                return
            form: QuoteFormResponse = feature.get_quote_form(GetQuoteFormRequest(line_code=line_code, period=period))
            self._defaults(form)
            c1, c2, c3 = st.columns(3)
            kinds = [PriceKind.THUONG, PriceKind.THI_NGHIEM] if form.has_trial_line else [PriceKind.THUONG]
            kind = c1.radio("Giá gia công", kinds, format_func=lambda k: k.value, horizontal=True, key=self.key("kind"))
            market = c2.radio(
                "Loại hàng",
                [MaterialMarket.NOI_DIA, MaterialMarket.XUAT_KHAU],
                format_func=lambda m: m.value,
                horizontal=True,
                key=self.key("market"),
            )
            incoterm = c3.radio(
                "Giá bán",
                [Incoterm.FOB, Incoterm.CIF],
                format_func=lambda i: i.value,
                horizontal=True,
                key=self.key("incoterm"),
            )
            c1, c2, c3 = st.columns(3)
            suggestions = {s.code: s for s in form.accounting_suggestions}
            accounting = c1.selectbox(
                "Mã kế toán (gợi ý hoặc dán mã)",
                list(suggestions),
                index=None,
                accept_new_options=True,
                placeholder="Chọn gợi ý hoặc dán mã kế toán",
                format_func=lambda c: (
                    f"{c} - {suggestions[c].name} (tồn {format_number(float(suggestions[c].stock_qty), 2)} kg)"
                    if c in suggestions
                    else c
                ),
                key=self.key(f"accounting.{line_code}"),
            )
            customer = c2.text_input("Khách hàng", max_chars=100, key=self.key("customer"))
            order_qty = c3.number_input("SL đơn hàng (kg)", min_value=0.0, step=100.0, key=self.key("qty"))
            names = {g.id: g.name for g in form.group_options}
            ids_by_name = {g.name: g.id for g in form.group_options}
            st.markdown("**Thành phần** - chọn nhóm giá nguyên liệu cho từng thành phần")
            edited = editable_table(
                [
                    {
                        "Nguyên liệu": c.material_label,
                        "Tỷ lệ %": pct(c.ratio),
                        "Tiêu hao %": pct(c.loss),
                        "Nhóm giá": names.get(c.suggested_group_id),
                    }
                    for c in form.components
                ],
                key=self.key(f"components.{line_code}"),
                columns=COMPONENT_COLUMNS,
                column_config={
                    "Tỷ lệ %": percent("Tỷ lệ %"),
                    "Tiêu hao %": percent("Tiêu hao %"),
                    "Nhóm giá": st.column_config.SelectboxColumn("Nhóm giá", options=list(ids_by_name), required=True),
                },
                disabled=("Nguyên liệu", "Tỷ lệ %", "Tiêu hao %"),
            )
            plan, supima, coin = self._cotton_block(form, line_code, edited, ids_by_name)
            c1, c2, c3, c4 = st.columns(4)
            factor = c1.number_input("Hệ số norm (%)", min_value=0.0, step=1.0, key=self.key("factor"))
            gp = c2.number_input("GP (% giá bán)", min_value=0.0, max_value=99.0, step=0.5, key=self.key("gp"))
            commission = c3.number_input(
                "Commission (% giá bán)", min_value=0.0, max_value=99.0, step=0.5, key=self.key("commission")
            )
            fi = (
                c4.number_input("F&I (USD/kg)", min_value=0.0, step=0.005, format="%.4f", key=self.key("fi"))
                if incoterm == Incoterm.CIF
                else 0.0
            )
            note = st.text_input("Ghi chú", max_chars=500, key=self.key("note"))
            request = CalculateQuoteRequest(
                period=period,
                line_code=line_code,
                price_kind=kind,
                accounting_code=accounting or "",
                customer_name=customer,
                market=market,
                order_qty=dec(order_qty),
                norm_factor=dec(factor) / HUNDRED,
                gp_percent=dec(gp) / HUNDRED,
                commission_percent=dec(commission) / HUNDRED,
                incoterm=incoterm,
                fi_usd=dec(fi),
                groups={row["Nguyên liệu"]: ids_by_name.get(row.get("Nhóm giá") or "", "") for row in edited},
                note=note,
                cotton_plan=plan,
                supima_percent=supima,
                supima_coin=coin,
            )
            b1, b2, _ = st.columns([1, 1, 3])
            if b1.button("Tính thử", icon="🧮", key=self.key("try"), disabled=disabled, help=why):
                self.state.set(RESULT_KEY, try_call(lambda: feature.calculate_quote(request)))
            if b2.button("Lưu lần tính", type="primary", icon="💾", key=self.key("save"), disabled=disabled, help=why):

                def save() -> str:
                    result = feature.calculate_quote(request.model_copy(update={"commit": True}))
                    self.state.set(RESULT_KEY, result)
                    self.state.set("selected_quote", result.quote.id)
                    return result.message

                run_save(self.state, save)
            explain(why)
        result = self.state.get(RESULT_KEY)
        if result is not None and result.quote.line_code == line_code:
            with panel(
                "Kết quả"
                + (f" - báo giá {result.quote.quote_no}" if result.quote.quote_no else " (tính thử, chưa lưu)"),
                icon="📋",
            ):
                self._quote_detail(result.quote, "result")

    def _cotton_block(
        self, form: QuoteFormResponse, line_code: str, edited: list[dict[str, Any]], ids_by_name: dict[str, str]
    ) -> tuple[list[CottonShareDTO] | None, Decimal, bool]:
        """BR-110 / BR-111 (bổ sung 2026-11-13): khối Pha bông - only when a component uses Cotton (phương án);
        the Supima coin tick only when the Supima share is > 0."""
        if not any(ids_by_name.get(r.get("Nhóm giá") or "") == COTTON_PLAN_ID for r in edited):
            return None, Decimal(0), False
        monthly = {s.origin: float(s.percent * HUNDRED) for s in form.cotton_plan}
        with st.container(border=True):
            st.markdown("**Pha bông** - phương án cho lần tính này (mặc định theo khai báo tháng) và tỷ lệ Supima")
            cols = st.columns(5)
            plan = []
            for col, origin in zip(cols[:3], ORIGINS, strict=True):
                key = self.key(f"plan.{line_code}.{origin.value}")
                st.session_state.setdefault(key, monthly.get(origin, 0.0))
                value = col.number_input(
                    f"{origin.value} %", min_value=0.0, max_value=100.0, step=1.0, format="%g", key=key
                )
                plan.append(CottonShareDTO(origin=origin, percent=dec(value) / HUNDRED))
            supima_key = self.key(f"supima.{line_code}")
            st.session_state.setdefault(supima_key, float(form.supima_percent * HUNDRED))
            supima = cols[3].number_input(
                "Tỷ lệ Supima %", min_value=0.0, max_value=100.0, step=5.0, format="%g", key=supima_key
            )
            coin = False
            if supima > 0:
                coin = cols[4].checkbox("Truyền điểm Supima coin trên TG", key=self.key(f"coin.{line_code}"))
        return plan, dec(supima) / HUNDRED, coin

    def _defaults(self, form: QuoteFormResponse) -> None:
        """Fill the inputs with the month defaults the first time (or after "Dùng lại")."""
        defaults = {
            "factor": float(form.norm_factor * HUNDRED),
            "fi": float(form.default_fi),
            "gp": 0.0,
            "commission": 0.0,
            "qty": 0.0,
        }
        for name, value in defaults.items():
            st.session_state.setdefault(self.key(name), value)
        key = self.key(f"accounting.{form.line_code}")
        if key not in st.session_state and form.default_accounting_code:
            st.session_state[key] = form.default_accounting_code

    def _quote_detail(self, q: QuoteDTO, scope: str) -> None:
        rate = q.exchange_rate
        stat_row(
            [
                (
                    "Giá vốn BQ (USD/kg)",
                    usd_text(q.avg_cost_usd),
                    f"{format_number(float(q.avg_cost_usd * rate), 0)} đ/kg",
                ),
                ("Giá FOB (USD/kg)", usd_text(q.fob_usd), f"{format_number(float(q.fob_usd * rate), 0)} đ/kg"),
                (
                    "Giá CIF (USD/kg)",
                    usd_text(q.cif_usd),
                    f"{format_number(float(q.cif_usd * rate), 0)} đ/kg"
                    if q.cif_usd is not None
                    else "Chọn CIF để có giá CIF",
                ),
            ]
        )
        st.caption(
            f"Tháng {month_text(q.period)} · tỷ giá {format_number(float(rate), 0)} · dòng {q.line_code} ({q.price_kind.value}) · "
            f"{q.market.value} · mã kế toán {q.accounting_code or '-'} · khách {q.customer_name or '-'}"
        )
        data_table(
            [
                {
                    "Nguyên liệu": c.material_label,
                    "Tỷ lệ %": pct(c.ratio),
                    "Tiêu hao %": pct(c.loss),
                    "Nhóm giá": c.price_group,
                    "Giá BQ": usd(c.average_usd),
                    "Hồi phế": usd(c.recovery_usd),
                    "Giá tính": usd(c.net_usd),
                    "Chi phí NL/kg sợi": usd(c.cost_usd),
                    "Cách pha": self._mix_text(c),
                }
                for c in q.components
            ],
            column_config={
                "Tỷ lệ %": percent("Tỷ lệ %"),
                "Tiêu hao %": percent("Tiêu hao %"),
                **{k: usd_col(k) for k in ("Giá BQ", "Hồi phế", "Giá tính", "Chi phí NL/kg sợi")},
            },
            key=self.key(f"components_out.{scope}"),
        )
        if q.cotton_plan:
            plan_text = " + ".join(
                f"{s.origin.value} {format_number(float(s.percent * HUNDRED), 2)}%" for s in q.cotton_plan
            )
            st.caption(
                f"Phương án bông: {plan_text}"
                + (f" · Supima {format_number(float(q.supima_percent * HUNDRED), 2)}%" if q.supima_percent else "")
                + (" · có truyền điểm Supima coin" if q.supima_coin else "")
            )
        stock = (
            f"Sợi tồn ({format_number(float(q.stock_qty), 2)} kg)"
            if q.stock_cost_usd is not None
            else "Sợi tồn (không có sợi tồn cùng mã kế toán)"
        )
        items = [
            ("Giá nguyên liệu", q.material_usd),
            *([("Phí Supima coin (cộng vào giá Supima)", q.coin_fee_usd)] if q.supima_coin else []),
            (f"Norm (dòng {q.line_code}, {format_number(float(q.norm_vnd), 0)} đ/kg)", q.norm_vnd / rate),
            (f"Norm × hệ số {format_number(float(q.norm_factor * HUNDRED), 2)}%", q.norm_usd),
            ("Giá vốn sợi sản xuất mới", q.new_cost_usd),
            (stock, q.stock_cost_usd),
            ("Giá vốn bình quân", q.avg_cost_usd),
            (f"GP {format_number(float(q.gp_percent * HUNDRED), 2)}%", q.fob_usd * q.gp_percent),
            (
                f"Commission {format_number(float(q.commission_percent * HUNDRED), 2)}%",
                q.fob_usd * q.commission_percent,
            ),
            ("Giá FOB", q.fob_usd),
        ]
        if q.cif_usd is not None:
            items += [("F&I", q.fi_usd), ("Giá CIF", q.cif_usd)]
        data_table(
            [
                {"Khoản": label, "USD/kg": usd(value), "VND/kg": vnd(value * rate) if value is not None else None}
                for label, value in items
            ],
            column_config={"USD/kg": usd_col("USD/kg"), "VND/kg": money("VND/kg")},
            key=self.key(f"prices_out.{scope}"),
        )

    # ---- UC-63 ----
    def _history(self, feature: YarnCostingController) -> None:
        with panel("Các lần đã tính", icon="🗂️"):
            c1, c2, c3, c4, c5 = st.columns(5)
            date_from = c1.date_input("Từ ngày", value=None, format="DD/MM/YYYY", key=self.key("from"))
            date_to = c2.date_input("Đến ngày", value=None, format="DD/MM/YYYY", key=self.key("to"))
            base = feature.list_quotes(ListQuotesRequest())
            period = c3.selectbox(
                "Tháng tính",
                ["", *base.periods],
                format_func=lambda p: month_text(p) or "Tất cả",
                key=self.key("h_period"),
            )
            customer = c4.selectbox(
                "Khách hàng", ["", *base.customers], format_func=lambda c: c or "Tất cả", key=self.key("h_customer")
            )
            search = c5.text_input("Tìm số BG / tên / mã KT", key=self.key("h_search"))
            filters = ListQuotesRequest(
                date_from=date_from, date_to=date_to, period=period, customer=customer, search=search
            )
            items = feature.list_quotes(filters).items
            rows = [
                {
                    "Số báo giá": q.quote_no,
                    "Ngày": q.created_at,
                    "Người tính": q.created_by,
                    "Khách hàng": q.customer_name,
                    "Tên chuẩn": q.yarn_name,
                    "Mã kế toán": q.accounting_code,
                    "Thường / TN": q.price_kind.value,
                    "Nội địa / XK": q.market.value,
                    "SL đơn (kg)": plain(q.order_qty),
                    "Giá vốn BQ": usd(q.avg_cost_usd),
                    "GP %": pct(q.gp_percent),
                    "Commission %": pct(q.commission_percent),
                    "FOB / CIF": q.incoterm.value,
                    "Giá FOB": usd(q.fob_usd),
                    "Giá CIF": usd(q.cif_usd),
                }
                for q in items
            ]
            selected = data_table(
                rows,
                column_config={
                    "Ngày": datetime_col("Ngày"),
                    "SL đơn (kg)": count_col("SL đơn (kg)"),
                    "GP %": percent("GP %"),
                    "Commission %": percent("Commission %"),
                    **{k: usd_col(k) for k in ("Giá vốn BQ", "Giá FOB", "Giá CIF")},
                },
                selection="single",
                empty_message="Chưa có lần tính nào phù hợp bộ lọc.",
                key=self.key("quotes"),
            )
            download_button(
                lambda: feature.export_quotes(ExportQuotesRequest(**filters.model_dump())),
                label="Xuất Excel",
                key=self.key("export"),
                file_name="gia-bao-khach.xlsx",
            )
            chosen_no = selected[0]["Số báo giá"] if selected else None
            if chosen_no is None and self.state.get("selected_quote"):
                chosen_no = next((q.quote_no for q in items if q.id == self.state.get("selected_quote")), None)
            quote = next((q for q in items if q.quote_no == chosen_no), None)
            if quote is None:
                return
            st.markdown(f"**Báo giá {quote.quote_no}** - {quote.yarn_name}")
            self._quote_detail(quote, "history")
            disabled, why = action_state("UC-63")
            b1, b2, _ = st.columns([1, 1, 3])
            if b1.button("Dùng lại để tính mới", icon="♻️", key=self.key("reuse"), disabled=disabled, help=why):
                self._reuse(quote)
            if b2.button("Xoá lần tính", icon="🗑️", key=self.key("delete"), disabled=disabled, help=why):
                confirm_dialog(
                    self.state,
                    self.key("dlg.delete"),
                    "Xác nhận xoá báo giá",
                    f"Xoá báo giá {quote.quote_no} ({quote.yarn_name})? Báo giá được đánh dấu xoá, không mất khỏi dữ liệu.",
                    "Xoá",
                    lambda: feature.delete_quote(DeleteQuoteRequest(quote_id=quote.id)).message,
                    on_done=lambda: self.state.pop("selected_quote"),
                )
            explain(why)

    @staticmethod
    def _mix_text(c: Any) -> str:
        """BR-111: how the cotton component is mixed ("" when it is not)."""
        if not c.supima_ratio:
            return ""
        s = float(c.supima_ratio * HUNDRED)
        supima = f"Supima {format_number(s, 2)}% · {format_number(float(c.supima_net), 4)} ÷ (1 − {format_number(float(c.supima_loss * HUNDRED), 2)}%)"
        if c.supima_ratio >= 1:
            return supima
        normal = (
            f"Bông thường {format_number(100 - s, 2)}% · {format_number(float(c.normal_net), 4)} ÷ "
            f"(1 − {format_number(float(c.normal_loss * HUNDRED), 2)}%)"
        )
        return f"{normal} | {supima}"

    def _reuse(self, q: QuoteDTO) -> None:
        """Fill the Tính giá block with the numbers of a saved quote, then rerun."""
        state = st.session_state
        state[self.key("period")] = q.period if q.period in month_options() else current_period()
        state[self.key("line")] = q.line_code
        state[self.key("kind")] = q.price_kind
        state[self.key("market")] = q.market
        state[self.key("incoterm")] = q.incoterm
        state[self.key(f"accounting.{q.line_code}")] = q.accounting_code or None
        state[self.key("customer")] = q.customer_name
        state[self.key("qty")] = float(q.order_qty)
        state[self.key("factor")] = float(q.norm_factor * HUNDRED)
        state[self.key("gp")] = float(q.gp_percent * HUNDRED)
        state[self.key("commission")] = float(q.commission_percent * HUNDRED)
        state[self.key("fi")] = float(q.fi_usd)
        state[self.key("note")] = q.note
        shares = {s.origin: float(s.percent * HUNDRED) for s in q.cotton_plan}
        if shares:  # BR-110 / BR-111: the plan, Supima share and coin tick of the reused quote
            for origin in ORIGINS:
                state[self.key(f"plan.{q.line_code}.{origin.value}")] = shares.get(origin, 0.0)
        state[self.key(f"supima.{q.line_code}")] = float(q.supima_percent * HUNDRED)
        state[self.key(f"coin.{q.line_code}")] = q.supima_coin
        self.state.pop(RESULT_KEY)
        st.rerun()
