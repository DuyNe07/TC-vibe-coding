"""Screen 11 (`gia-nguyen-lieu`) - Giá nguyên liệu (UC-55..UC-59, UC-64; đợt 2, bổ sung 2026-11-10)."""

from decimal import Decimal
from typing import Any

import streamlit as st

from backend.core.gateway import gateway
from backend.features.yarn_costing import YarnCostingController
from backend.features.yarn_costing.dto.material_dto import (
    CottonOrigin,
    CottonShareDTO,
    GetMaterialAveragesRequest,
    GetMaterialSetupRequest,
    GetMonthlySettingRequest,
    GetStockOutComparisonRequest,
    ImportStockFileRequest,
    ListStockMonthsRequest,
    MaterialAveragesResponse,
    MaterialDecision,
    MaterialMarket,
    MaterialSetupResponse,
    PriceGroupKind,
    RecoveryDTO,
    SaveMonthlySettingRequest,
    SavePriceGroupRequest,
    SaveStockItemSettingsRequest,
    StockImportResponse,
    StockItemRowDTO,
    StockOutRowDTO,
)
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, editable_table, empty_state, file_upload, panel, stat_row
from frontend.core.formatting import format_number
from frontend.features.yarn_costing.components.columns import count_col, datetime_col, money, percent, usd_col
from frontend.features.yarn_costing.components.dialogs import confirm_dialog
from frontend.features.yarn_costing.components.display import percent_value, plain, usd, vnd
from frontend.features.yarn_costing.components.flash import show_flash
from frontend.features.yarn_costing.components.material_ui import (
    current_period,
    material_denied,
    month_options,
    month_text,
    run_save,
)
from frontend.features.yarn_costing.components.permissions import action_state, explain

PREVIEW_KEY = "stock_preview"
HUNDRED = Decimal(100)
NONE = "—"
DECISIONS = [d.value for d in MaterialDecision]
MARKETS = [m.value for m in MaterialMarket]
KINDS = [k.value for k in PriceGroupKind]
ORIGINS = [o.value for o in CottonOrigin]


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value)) if value not in (None, "") else Decimal(0)
    except ArithmeticError:
        return Decimal(0)


class MaterialPricePage(BasePage):
    title = "Giá nguyên liệu"
    menu_group = "Sales"
    icon = "🧶"
    slug = "gia-nguyen-lieu"
    description = (
        "Giá nguyên liệu bình quân tháng (tồn kho S4 + hàng sắp về, trừ hồi phế), file kho hằng tháng, khai báo nhóm giá, "
        "khai báo tháng và so giá xuất kho."
    )

    def render(self) -> None:
        if material_denied("UC-59"):
            return
        show_flash(self.state)
        feature = gateway.open(YarnCostingController)
        tabs = st.tabs(["📊 Giá bình quân", "📥 File kho", "🏷️ Khai báo", "🗓️ Khai báo tháng", "⚖️ So giá xuất"])
        with tabs[0]:
            self._averages(feature)
        with tabs[1]:
            self._stock_file(feature)
        with tabs[2]:
            setup = feature.get_material_setup(GetMaterialSetupRequest())
            self._groups(feature, setup)
            self._stock_items(feature, setup)
        with tabs[3]:
            self._monthly(feature)
        with tabs[4]:
            self._stock_out(feature)

    # ---- UC-59 ----
    def _averages(self, feature: YarnCostingController) -> None:
        months = month_options()
        period = st.selectbox(
            "Tháng tính",
            months,
            index=months.index(current_period()),
            format_func=month_text,
            key=self.key("avg_period"),
        )
        data: MaterialAveragesResponse = feature.get_material_averages(GetMaterialAveragesRequest(period=period))
        if data.problem:
            st.warning(data.problem, icon="⚠️")
            return
        st.caption(
            f"File kho tháng {month_text(data.stock_period)} · Tỷ giá {format_number(float(data.exchange_rate or 0), 0)} · "
            f"Phương án bông: {data.plan_text or 'chưa khai báo'}"
        )
        if data.undeclared_codes or data.undeclared_lots:
            st.warning(
                f"Có {data.undeclared_codes} mã kho và {data.undeclared_lots} lô hàng về chưa khai báo nhóm, "
                "chưa được tính vào giá bình quân.",
                icon="⚠️",
            )
        rows = [
            {
                "Nhóm": r.group_name,
                "Nội địa / XK": r.market.value,
                "SL tồn (kg)": plain(r.stock_qty),
                "Giá tồn": usd(r.stock_unit),
                "SL về (kg)": plain(r.arrival_qty),
                "Giá về": usd(r.arrival_unit),
                "Giá BQ": usd(r.average),
                "Hồi phế": usd(r.recovery),
                "Giá tính USD": usd(r.net_usd),
                "Giá tính VND": vnd(r.net_vnd),
                "Ghi chú": r.note,
            }
            for r in data.rows
        ]
        selected = data_table(
            rows,
            column_config={
                "SL tồn (kg)": money("SL tồn (kg)"),
                "SL về (kg)": money("SL về (kg)"),
                **{k: usd_col(k) for k in ("Giá tồn", "Giá về", "Giá BQ", "Hồi phế", "Giá tính USD")},
                "Giá tính VND": money("Giá tính VND"),
            },
            selection="single",
            empty_message="Chưa có nhóm giá nào. Khai báo nhóm ở thẻ Khai báo.",
            key=self.key("averages"),
        )
        if selected:
            row = next(
                r
                for r in data.rows
                if r.group_name == selected[0]["Nhóm"] and r.market.value == selected[0]["Nội địa / XK"]
            )
            st.markdown(f"**Chi tiết: {row.group_name} - {row.market.value}**")
            data_table(
                [
                    {
                        "Loại": s.kind,
                        "Mã / hợp đồng": s.code,
                        "Tên hàng": s.name,
                        "Loại hàng": s.market.value,
                        "SL (kg)": plain(s.quantity),
                        "Đơn giá (USD/kg)": usd(s.unit_usd),
                    }
                    for s in row.sources
                ],
                column_config={"SL (kg)": money("SL (kg)"), "Đơn giá (USD/kg)": usd_col("Đơn giá (USD/kg)")},
                empty_message="Không có tồn và hàng về.",
                key=self.key("sources"),
            )

    # ---- UC-56 ----
    def _stock_file(self, feature: YarnCostingController) -> None:
        disabled, why = action_state("UC-56")
        with panel("Tải file kho tháng", icon="📤"):
            st.caption(
                "Báo cáo nhập - xuất - tồn kho S4 từ hệ thống kế toán (ví dụ 'GIÁ SỢI 4 THÁNG 10.xlsx'), giữ nguyên. Tải lại một "
                "tháng đã có thì bản mới thay bản cũ (bản cũ vẫn được giữ để tra)."
            )
            file = file_upload("File kho", types=[".xlsx", ".xlsm", ".xls"], key=self.key("stock_file"))
            signature = (file.filename, len(file.content)) if file is not None else None
            if st.button(
                "Kiểm tra file",
                type="primary",
                icon="🔍",
                key=self.key("stock_check"),
                disabled=disabled or file is None,
                help=why or ("Vui lòng chọn file Excel." if file is None else None),
            ):
                preview = feature.import_stock_file(ImportStockFileRequest(file=file, commit=False))
                self.state.set(PREVIEW_KEY, {"sig": signature, "result": preview})
                if preview.period:
                    st.session_state[self.key("stock_period")] = preview.period
                else:
                    st.session_state.pop(self.key("stock_period"), None)
            explain(why)
            stored = self.state.get(PREVIEW_KEY)
            if stored and file is not None and stored["sig"] == signature:
                preview: StockImportResponse = stored["result"]
                st.info(preview.message)
                if preview.replace_note:
                    st.warning(preview.replace_note, icon="⚠️")
                stat_row(
                    [
                        ("Mã nguyên liệu", format_number(preview.material_count)),
                        ("Mã sợi thành phẩm", format_number(preview.yarn_count)),
                        ("Mã phụ liệu", format_number(preview.accessory_count)),
                        ("Mã nguyên liệu mới", format_number(preview.new_codes)),
                        ("Dòng bị loại", format_number(len(preview.rejected_rows))),
                    ]
                )
                if preview.rejected_rows:
                    data_table(
                        [{"Dòng": r.excel_row, "Mã": r.key, "Lý do": r.reason} for r in preview.rejected_rows],
                        column_config={"Dòng": count_col("Dòng")},
                        key=self.key("stock_rejected"),
                    )
                months = month_options([preview.period] if preview.period else [])
                period = st.selectbox(
                    "Tháng của file", months, index=None, placeholder="Chọn tháng", format_func=month_text,
                    key=self.key("stock_period"),
                )  # fmt: skip
                period = period or ""
                valid = preview.material_count + preview.yarn_count + preview.accessory_count
                if st.button(
                    f"Lưu tháng {month_text(period)}",
                    type="primary",
                    icon="💾",
                    key=self.key("stock_commit"),
                    disabled=disabled or valid == 0 or not period,
                    help=why or ("Không có dòng hợp lệ để lưu." if valid == 0 else None),
                ):
                    request = ImportStockFileRequest(file=file, period=period, commit=True)

                    def action() -> str:
                        result = feature.import_stock_file(request)
                        self.state.pop(PREVIEW_KEY)
                        return result.message

                    confirm_dialog(
                        self.state,
                        self.key("dlg.stock_commit"),
                        "Xác nhận lưu file kho",
                        f"Lưu file kho tháng {month_text(period)} ({valid} mã)?"
                        + (" Bản đã có của tháng này sẽ được thay." if preview.replace_note else ""),
                        "Lưu",
                        action,
                    )
        with panel("Các tháng đã lưu", icon="🗂️"):
            months_saved = feature.list_stock_months(ListStockMonthsRequest()).items
            data_table(
                [
                    {
                        "Tháng": month_text(m.period),
                        "File": m.file_name,
                        "Mã nguyên liệu": m.material_count,
                        "Mã sợi thành phẩm": m.yarn_count,
                        "Mã phụ liệu": m.accessory_count,
                        "Người tải": m.imported_by,
                        "Lúc tải": m.imported_at,
                    }
                    for m in months_saved
                ],
                column_config={
                    "Mã nguyên liệu": count_col("Mã nguyên liệu"),
                    "Mã sợi thành phẩm": count_col("Mã sợi thành phẩm"),
                    "Mã phụ liệu": count_col("Mã phụ liệu"),
                    "Lúc tải": datetime_col("Lúc tải"),
                },
                empty_message="Chưa có tháng nào.",
                key=self.key("stock_months"),
            )

    # ---- UC-55 ----
    def _groups(self, feature: YarnCostingController, setup: MaterialSetupResponse) -> None:
        disabled, why = action_state("UC-55")
        with panel(
            "Nhóm giá nguyên liệu",
            icon="🏷️",
            description="Cotton theo xuất xứ, xơ theo nhà cung cấp. Nhóm 'Cotton (phương án)' luôn có sẵn.",
        ):
            selected = data_table(
                [
                    {
                        "Tên": g.name,
                        "Loại": g.kind.value if g.kind else "",
                        "Xuất xứ": g.origin.value if g.origin else "",
                        "Ghi chú": g.note,
                        "Số mã kho đang gán": g.code_count,
                    }
                    for g in setup.groups
                ],
                column_config={"Số mã kho đang gán": count_col("Số mã kho đang gán")},
                selection="single",
                empty_message="Chưa có nhóm giá nào.",
                key=self.key("groups"),
            )
            current = next((g for g in setup.groups if selected and g.name == selected[0]["Tên"]), None)
            scope = current.id if current else "new"
            st.markdown("**Sửa nhóm đang chọn**" if current else "**Thêm nhóm**")
            c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
            name = c1.text_input(
                "Tên nhóm", value=current.name if current else "", max_chars=100, key=self.key(f"g_name.{scope}")
            )
            kind_value = c2.selectbox(
                "Loại",
                KINDS,
                index=KINDS.index(current.kind.value) if current and current.kind else 1,
                key=self.key(f"g_kind.{scope}"),
            )
            kind = PriceGroupKind(kind_value)
            origin = None
            if kind == PriceGroupKind.COTTON:
                origin_value = c3.selectbox(
                    "Xuất xứ",
                    ORIGINS,
                    index=ORIGINS.index(current.origin.value) if current and current.origin else None,
                    key=self.key(f"g_origin.{scope}"),
                )
                origin = CottonOrigin(origin_value) if origin_value else None
            note = c4.text_input(
                "Ghi chú", value=current.note if current else "", max_chars=500, key=self.key(f"g_note.{scope}")
            )
            request = SavePriceGroupRequest(
                group_id=current.id if current else None, name=name, kind=kind, origin=origin, note=note
            )
            b1, b2, _ = st.columns([1, 1, 3])
            if b1.button(
                "Lưu nhóm" if current else "Thêm nhóm",
                type="primary",
                icon="💾",
                key=self.key("g_save"),
                disabled=disabled,
                help=why,
            ):
                run_save(self.state, lambda: feature.save_price_group(request).message)
            if current and b2.button("Xoá nhóm", icon="🗑️", key=self.key("g_delete"), disabled=disabled, help=why):
                confirm_dialog(
                    self.state,
                    self.key("dlg.g_delete"),
                    "Xác nhận xoá nhóm giá",
                    f"Xoá nhóm '{current.name}'? {current.code_count} mã kho đang gán sẽ trở về Chưa khai báo.",
                    "Xoá",
                    lambda: feature.save_price_group(SavePriceGroupRequest(group_id=current.id, delete=True)).message,
                )
            explain(why)

    # ---- UC-57 ----
    def _stock_items(self, feature: YarnCostingController, setup: MaterialSetupResponse) -> None:
        disabled, why = action_state("UC-57")
        with panel(
            "Mã kho nguyên liệu",
            icon="📦",
            description="Gán từng mã kho vào nhóm giá hoặc chọn Không tính; loại hàng gợi ý theo đuôi mã.",
        ):
            stat_row([("Chưa khai báo", format_number(setup.undeclared_count))])
            only_new = st.toggle(
                "Chỉ hiện mã chưa khai báo", value=setup.undeclared_count > 0, key=self.key("only_new")
            )
            names = {g.id: g.name for g in setup.groups}
            ids = {g.name: g.id for g in setup.groups}
            items = [i for i in setup.stock_items if not only_new or i.decision == MaterialDecision.CHUA_KHAI_BAO]
            if not setup.stock_items:
                empty_state("Chưa có mã kho nào. Tải file kho ở thẻ File kho.")
                return
            edited = editable_table(
                [
                    {
                        "Mã kế toán": i.accounting_code,
                        "Tên hàng": i.item_name,
                        "Nhóm kế toán": i.ica_name,
                        f"Tồn cuối {month_text(setup.latest_period)} (kg)": plain(i.closing_qty),
                        "Cách dùng": i.decision.value,
                        "Nhóm giá": names.get(i.price_group_id or ""),
                        "Loại hàng": i.market.value,
                    }
                    for i in items
                ],
                key=self.key(f"items.{only_new}"),
                column_config={
                    f"Tồn cuối {month_text(setup.latest_period)} (kg)": money(
                        f"Tồn cuối {month_text(setup.latest_period)} (kg)"
                    ),
                    "Cách dùng": st.column_config.SelectboxColumn("Cách dùng", options=DECISIONS, required=True),
                    "Nhóm giá": st.column_config.SelectboxColumn("Nhóm giá", options=list(ids)),
                    "Loại hàng": st.column_config.SelectboxColumn("Loại hàng", options=MARKETS, required=True),
                },
                disabled=("Mã kế toán", "Tên hàng", "Nhóm kế toán", f"Tồn cuối {month_text(setup.latest_period)} (kg)"),
            )
            if st.button(
                "Lưu khai báo mã kho",
                type="primary",
                icon="💾",
                key=self.key("items_save"),
                disabled=disabled,
                help=why,
            ):
                rows = [
                    StockItemRowDTO(
                        accounting_code=r["Mã kế toán"],
                        decision=MaterialDecision(r.get("Cách dùng") or MaterialDecision.CHUA_KHAI_BAO.value),
                        price_group_id=ids.get(r.get("Nhóm giá") or ""),
                        market=MaterialMarket(r.get("Loại hàng") or MaterialMarket.CHUNG.value),
                    )
                    for r in edited
                ]
                run_save(
                    self.state,
                    lambda: feature.save_stock_item_settings(SaveStockItemSettingsRequest(rows=rows)).message,
                )
            explain(why)

    # ---- UC-58 ----
    def _monthly(self, feature: YarnCostingController) -> None:
        disabled, why = action_state("UC-58")
        months = month_options()
        period = st.selectbox(
            "Tháng", months, index=months.index(current_period()), format_func=month_text, key=self.key("m_period")
        )
        data = feature.get_monthly_setting(GetMonthlySettingRequest(period=period))
        if data.saved:
            st.caption(f"Đã lưu{' bởi ' + data.updated_by if data.updated_by else ''}.")
        elif data.copied_from:
            st.info(f"Chép từ tháng {month_text(data.copied_from)}, chưa lưu.")
        else:
            st.info("Tháng đầu tiên: dùng số mặc định, chưa lưu.")
        c1, c2, c3 = st.columns(3)
        factor = c1.number_input(
            "Hệ số norm mặc định (%)",
            min_value=0.0,
            value=float(data.norm_factor * HUNDRED),
            step=1.0,
            key=self.key(f"m_factor.{period}"),
        )
        fi = c2.number_input(
            "F&I mặc định (USD/kg)",
            min_value=0.0,
            value=float(data.default_fi),
            step=0.005,
            format="%.4f",
            key=self.key(f"m_fi.{period}"),
        )
        plan_note = c3.text_input(
            "Ghi chú phương án", value=data.cotton_plan_note, max_chars=200, key=self.key(f"m_note.{period}")
        )
        st.markdown("**Phương án pha bông** (tổng 100%)")
        plan = editable_table(
            [{"Xuất xứ": s.origin.value, "Tỷ lệ %": float(s.percent * HUNDRED)} for s in data.cotton_plan],
            key=self.key(f"m_plan.{period}"),
            columns=["Xuất xứ", "Tỷ lệ %"],
            column_config={
                "Xuất xứ": st.column_config.SelectboxColumn("Xuất xứ", options=ORIGINS, required=True),
                "Tỷ lệ %": percent("Tỷ lệ %"),
            },
            allow_add_delete=True,
        )
        st.markdown("**Hồi phế nguyên liệu (USD/kg)** - trừ khỏi giá bình quân")
        names = [g.name for g in data.group_options]
        ids = {g.name: g.id for g in data.group_options}
        recoveries = editable_table(
            [{"Nhóm giá": r.group_name, "USD/kg": float(r.usd_per_kg)} for r in data.recoveries],
            key=self.key(f"m_recovery.{period}"),
            columns=["Nhóm giá", "USD/kg"],
            column_config={
                "Nhóm giá": st.column_config.SelectboxColumn("Nhóm giá", options=names, required=True),
                "USD/kg": usd_col("USD/kg"),
            },
            allow_add_delete=True,
        )
        if st.button(
            "Lưu khai báo tháng", type="primary", icon="💾", key=self.key("m_save"), disabled=disabled, help=why
        ):
            request = SaveMonthlySettingRequest(
                period=period,
                norm_factor=dec(factor) / HUNDRED,
                default_fi=dec(fi),
                cotton_plan_note=plan_note,
                cotton_plan=[
                    CottonShareDTO(origin=CottonOrigin(r["Xuất xứ"]), percent=dec(r.get("Tỷ lệ %")) / HUNDRED)
                    for r in plan
                    if r.get("Xuất xứ")
                ],
                recoveries=[
                    RecoveryDTO(group_id=ids[r["Nhóm giá"]], usd_per_kg=dec(r.get("USD/kg")))
                    for r in recoveries
                    if r.get("Nhóm giá") in ids
                ],
            )
            run_save(self.state, lambda: feature.save_monthly_setting(request).message)
        explain(why)

    # ---- UC-64 ----
    def _stock_out(self, feature: YarnCostingController) -> None:
        months = feature.list_stock_months(ListStockMonthsRequest()).items
        if not months:
            empty_state("Chưa có file kho. Vui lòng tải ở thẻ File kho.")
            return
        c1, c2, c3 = st.columns(3)
        period = c1.selectbox("Tháng kho", [m.period for m in months], format_func=month_text, key=self.key("o_period"))
        gap = c2.number_input("Lệch nhiều trên (%)", min_value=0.0, value=10.0, step=1.0, key=self.key("o_gap"))
        only_gap = c3.toggle("Chỉ hiện mã lệch nhiều", key=self.key("o_only"))
        if gap <= 0:
            st.warning("Mức cảnh báo phải là số lớn hơn 0.", icon="⚠️")
            return
        data = feature.get_stock_out_comparison(
            GetStockOutComparisonRequest(period=period, gap_percent=Decimal(str(gap)), only_gap=only_gap)
        )
        if data.problem:
            st.warning(data.problem, icon="⚠️")
            return
        stat_row(
            [
                ("Mã nguyên liệu so được", format_number(data.material_count)),
                ("Mã sợi so được", format_number(data.yarn_count)),
                ("Lệch nhiều", format_number(data.gap_count)),
                ("Chưa có giá so", format_number(data.no_compare_count)),
            ]
        )
        with panel(
            "Nguyên liệu", icon="🧶", description="Đơn giá xuất tháng so với giá bình quân (trước hồi phế) của nhóm."
        ):
            data_table(
                [self._out_row(r, material=True) for r in data.material_rows],
                column_config=self._out_config(),
                empty_message="Không có mã nguyên liệu xuất trong tháng.",
                key=self.key("o_materials"),
            )
        with panel(
            "Sợi thành phẩm",
            icon="🧵",
            description="Đơn giá xuất tháng so với giá vốn BQ của lần tính báo giá gần nhất cùng mã.",
        ):
            data_table(
                [self._out_row(r, material=False) for r in data.yarn_rows],
                column_config=self._out_config(),
                empty_message="Không có mã sợi xuất trong tháng.",
                key=self.key("o_yarns"),
            )

    def _out_row(self, r: StockOutRowDTO, material: bool) -> dict[str, Any]:
        row: dict[str, Any] = {"Mã kế toán": r.accounting_code, "Tên hàng": r.item_name}
        if material:
            row |= {"Nhóm giá": r.group_name, "Loại hàng": r.market.value if r.market else ""}
        row |= {"SL xuất (kg)": plain(r.out_qty), "Đơn giá xuất (USD/kg)": usd(r.out_unit_usd)}
        if material:
            row["Giá BQ tháng (USD/kg)"] = usd(r.compare_usd)
        else:
            row |= {
                "Đơn giá xuất (VND/kg)": vnd(r.out_unit_vnd),
                "Báo giá so sánh": f"{r.quote_no} ({r.quote_date:%d/%m/%Y})" if r.quote_no and r.quote_date else "",
                "Giá vốn BQ báo giá": usd(r.compare_usd),
            }
        row |= {
            "Chênh lệch": usd(r.difference),
            "Chênh lệch %": percent_value(r.difference_percent),
            "Cảnh báo": "🔴 Lệch nhiều" if r.is_gap else "",
            "Ghi chú": r.note,
        }
        return row

    def _out_config(self) -> dict[str, Any]:
        return {
            "SL xuất (kg)": money("SL xuất (kg)"),
            "Đơn giá xuất (VND/kg)": money("Đơn giá xuất (VND/kg)"),
            "Chênh lệch %": percent("Chênh lệch %"),
            **{
                k: usd_col(k)
                for k in ("Đơn giá xuất (USD/kg)", "Giá BQ tháng (USD/kg)", "Giá vốn BQ báo giá", "Chênh lệch")
            },
        }
