"""Screen 12 (`nguyen-lieu-sap-ve`) - Nguyên liệu sắp về (UC-60, UC-61; đợt 2, bổ sung 2026-11-10)."""

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

import streamlit as st

from backend.core.gateway import gateway
from backend.features.yarn_costing import YarnCostingController
from backend.features.yarn_costing.dto.material_dto import (
    ArrivalImportResponse,
    ArrivalListResponse,
    ArrivalLotRowDTO,
    ArrivalMappingRowDTO,
    FactoryCode,
    ImportArrivalFileRequest,
    ListArrivalsRequest,
    MaterialDecision,
    MaterialMarket,
    SaveArrivalLotsRequest,
    SaveArrivalMappingsRequest,
)
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, editable_table, file_upload, panel, stat_row
from frontend.core.formatting import format_number
from frontend.features.yarn_costing.components.columns import count_col, datetime_col, money
from frontend.features.yarn_costing.components.dialogs import confirm_dialog
from frontend.features.yarn_costing.components.display import plain
from frontend.features.yarn_costing.components.flash import show_flash
from frontend.features.yarn_costing.components.material_ui import material_denied, month_text, run_save
from frontend.features.yarn_costing.components.permissions import action_state, explain

PREVIEW_KEY = "arrival_preview"
ALL = ""
DECISIONS = [d.value for d in MaterialDecision]
MARKETS = [m.value for m in MaterialMarket]
FACTORIES = [f.value for f in FactoryCode]
ID = "_id"
LOT_COLUMNS = [
    ID, "Nhà cung cấp", "Loại hàng", "Mô tả", "Spec", "Hợp đồng", "SL (kg)", "Đơn giá", "Tiền tệ", "Giá nhập kho (USD/kg)",
    "Ngày về kho", "Kho", "Xưởng", "Nội địa / XK / Chung", "Nhóm giá", "Ghi chú",
]  # fmt: skip


def optional(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def as_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if hasattr(value, "date"):
        return value.date()
    return None


class ArrivalPage(BasePage):
    title = "Nguyên liệu sắp về"
    menu_group = "Sales"
    icon = "🚢"
    slug = "nguyen-lieu-sap-ve"
    description = (
        "Theo dõi các lô nguyên liệu sẽ về nhà máy (nhập file theo dõi của Sales hoặc sửa tay) để tính giá bình quân."
    )

    def render(self) -> None:
        if material_denied("UC-61"):
            return
        show_flash(self.state)
        feature = gateway.open(YarnCostingController)
        data = self._lots(feature)
        self._mappings(feature, data)
        self._upload(feature)
        with panel("Các lần nhập file", icon="🗂️"):
            data_table(
                [
                    {
                        "File": i.file_name,
                        "Sheet": i.sheet_name,
                        "Số lô": i.lot_count,
                        "Bị loại": i.rejected_count,
                        "Người nhập": i.imported_by,
                        "Lúc nhập": i.imported_at,
                    }
                    for i in data.imports
                ],
                column_config={
                    "Số lô": count_col("Số lô"),
                    "Bị loại": count_col("Bị loại"),
                    "Lúc nhập": datetime_col("Lúc nhập"),
                },
                empty_message="Chưa nhập file nào.",
                key=self.key("imports"),
            )

    # ---- UC-61: lots ----
    def _lots(self, feature: YarnCostingController) -> ArrivalListResponse:
        disabled, why = action_state("UC-61")
        base = feature.list_arrivals(ListArrivalsRequest(factory_code=None))
        with panel("Bộ lọc", icon="🔎"):
            c1, c2, c3, c4, c5 = st.columns(5)
            factory = c1.selectbox("Xưởng", FACTORIES, index=FACTORIES.index("S4"), key=self.key("factory"))
            month = c2.selectbox(
                "Tháng về", [ALL, *base.months], format_func=lambda m: month_text(m) or "Tất cả", key=self.key("month")
            )
            groups = {g.name: g.id for g in base.groups}
            group = c3.selectbox("Nhóm giá", [ALL, *groups], format_func=lambda g: g or "Tất cả", key=self.key("group"))
            market = c4.selectbox(
                "Loại hàng",
                [ALL, MaterialMarket.NOI_DIA.value, MaterialMarket.XUAT_KHAU.value],
                format_func=lambda m: m or "Tất cả",
                key=self.key("market"),
            )
            only_unmapped = c5.toggle("Chỉ hiện lô chưa có nhóm", key=self.key("unmapped"))
        data = feature.list_arrivals(
            ListArrivalsRequest(
                factory_code=FactoryCode(factory),
                month=month,
                group_id=groups.get(group, ""),
                market=MaterialMarket(market) if market else None,
                only_unmapped=only_unmapped,
            )
        )
        stat_row(
            [
                ("Số lô", format_number(len(data.lots))),
                ("Tổng SL (kg)", format_number(float(data.total_qty), 0)),
                ("Lô chưa có nhóm", format_number(data.unmapped_count)),
            ]
        )
        with panel(
            "Lô hàng sắp về",
            icon="🚢",
            description="Sửa trực tiếp trong bảng, thêm / xoá dòng, rồi bấm Lưu thay đổi lô. Nhập lại file sẽ thay toàn bộ lô.",
        ):
            rows = [
                {
                    ID: lot.id,
                    "Nhà cung cấp": lot.supplier,
                    "Loại hàng": lot.commodity,
                    "Mô tả": lot.description,
                    "Spec": lot.spec,
                    "Hợp đồng": lot.contract_no,
                    "SL (kg)": plain(lot.quantity),
                    "Đơn giá": plain(lot.unit_price),
                    "Tiền tệ": lot.price_currency.value,
                    "Giá nhập kho (USD/kg)": plain(lot.receiving_price),
                    "Ngày về kho": lot.eta_warehouse,
                    "Kho": lot.warehouse,
                    "Xưởng": lot.factory_code.value,
                    "Nội địa / XK / Chung": lot.market.value,
                    "Nhóm giá": lot.group_name,
                    "Ghi chú": lot.note,
                }
                for lot in data.lots
            ]
            edited = editable_table(
                rows,
                key=self.key(f"lots.{factory}.{month}.{group}.{market}.{only_unmapped}"),
                columns=LOT_COLUMNS,
                column_order=LOT_COLUMNS[1:],
                column_config={
                    "SL (kg)": money("SL (kg)"),
                    "Đơn giá": st.column_config.NumberColumn("Đơn giá", format="%.4f", help="Lớn hơn 100 = VND/kg"),
                    "Giá nhập kho (USD/kg)": st.column_config.NumberColumn("Giá nhập kho (USD/kg)", format="%.4f"),
                    "Ngày về kho": st.column_config.DateColumn("Ngày về kho", format="DD/MM/YYYY"),
                    "Xưởng": st.column_config.SelectboxColumn("Xưởng", options=FACTORIES),
                    "Nội địa / XK / Chung": st.column_config.SelectboxColumn("Nội địa / XK / Chung", options=MARKETS),
                },
                disabled=("Tiền tệ", "Nhóm giá"),
                allow_add_delete=True,
            )
            if st.button(
                "Lưu thay đổi lô", type="primary", icon="💾", key=self.key("lots_save"), disabled=disabled, help=why
            ):
                kept = {r.get(ID) for r in edited if r.get(ID)}
                request = SaveArrivalLotsRequest(
                    rows=[
                        ArrivalLotRowDTO(
                            id=r.get(ID) or None,
                            supplier=str(r.get("Nhà cung cấp") or ""),
                            commodity=str(r.get("Loại hàng") or ""),
                            description=str(r.get("Mô tả") or ""),
                            spec=str(r.get("Spec") or ""),
                            contract_no=str(r.get("Hợp đồng") or ""),
                            quantity=optional(r.get("SL (kg)")),
                            unit_price=optional(r.get("Đơn giá")),
                            receiving_price=optional(r.get("Giá nhập kho (USD/kg)")),
                            eta_warehouse=as_date(r.get("Ngày về kho")),
                            warehouse=str(r.get("Kho") or ""),
                            factory_code=FactoryCode(r["Xưởng"]) if r.get("Xưởng") else FactoryCode(factory),
                            market=MaterialMarket(r["Nội địa / XK / Chung"]) if r.get("Nội địa / XK / Chung") else None,
                            note=str(r.get("Ghi chú") or ""),
                        )
                        for r in edited
                    ],
                    deleted_ids=[lot.id for lot in data.lots if lot.id not in kept],
                )
                run_save(self.state, lambda: feature.save_arrival_lots(request).message)
            explain(why)
        return data

    # ---- UC-61: pairs ----
    def _mappings(self, feature: YarnCostingController, data: ArrivalListResponse) -> None:
        disabled, why = action_state("UC-61")
        with panel(
            "Khai báo nhóm cho nhà cung cấp + mô tả",
            icon="🏷️",
            description="App nhớ cặp nhà cung cấp + mô tả thuộc nhóm giá nào; lần nhập sau tự gán. Cặp chưa khai báo không vào giá bình quân.",
        ):
            names = {g.id: g.name for g in data.groups}
            ids = {g.name: g.id for g in data.groups}
            keys = {(m.supplier, m.description): (m.supplier_key, m.description_key) for m in data.mappings}
            edited = editable_table(
                [
                    {
                        "Nhà cung cấp": m.supplier,
                        "Mô tả": m.description,
                        "Số lô": m.lot_count,
                        "Cách dùng": m.decision.value,
                        "Nhóm giá": names.get(m.price_group_id or ""),
                    }
                    for m in data.mappings
                ],
                key=self.key("mappings"),
                columns=["Nhà cung cấp", "Mô tả", "Số lô", "Cách dùng", "Nhóm giá"],
                column_config={
                    "Số lô": count_col("Số lô"),
                    "Cách dùng": st.column_config.SelectboxColumn("Cách dùng", options=DECISIONS, required=True),
                    "Nhóm giá": st.column_config.SelectboxColumn("Nhóm giá", options=list(ids)),
                },
                disabled=("Nhà cung cấp", "Mô tả", "Số lô"),
            )
            if st.button(
                "Lưu khai báo nhóm", type="primary", icon="💾", key=self.key("map_save"), disabled=disabled, help=why
            ):
                rows = [
                    ArrivalMappingRowDTO(
                        supplier_key=keys[(r["Nhà cung cấp"], r["Mô tả"])][0],
                        description_key=keys[(r["Nhà cung cấp"], r["Mô tả"])][1],
                        decision=MaterialDecision(r.get("Cách dùng") or MaterialDecision.CHUA_KHAI_BAO.value),
                        price_group_id=ids.get(r.get("Nhóm giá") or ""),
                    )
                    for r in edited
                    if (r.get("Nhà cung cấp"), r.get("Mô tả")) in keys
                ]
                run_save(
                    self.state, lambda: feature.save_arrival_mappings(SaveArrivalMappingsRequest(rows=rows)).message
                )
            explain(why)

    # ---- UC-60 ----
    def _upload(self, feature: YarnCostingController) -> None:
        disabled, why = action_state("UC-60")
        with panel("Nhập file", icon="📤"):
            st.caption(
                "File theo dõi xơ về của Sales (ví dụ 'Ke hoach xo ve NM - 06.11.xlsx'): app đọc sheet 'Update Fiber arrival ...'. "
                "Cột 'Giá nhập kho' (USD/kg) để trống thì dùng Unit price. Lưu sẽ thay toàn bộ lô hiện có (kể cả lô nhập tay)."
            )
            file = file_upload("File hàng sắp về", types=[".xlsx", ".xlsm", ".xls"], key=self.key("file"))
            signature = (file.filename, len(file.content)) if file is not None else None
            if st.button(
                "Kiểm tra file",
                type="primary",
                icon="🔍",
                key=self.key("check"),
                disabled=disabled or file is None,
                help=why or ("Vui lòng chọn file Excel." if file is None else None),
            ):
                self.state.set(
                    PREVIEW_KEY,
                    {"sig": signature, "result": feature.import_arrival_file(ImportArrivalFileRequest(file=file))},
                )
            explain(why)
            stored = self.state.get(PREVIEW_KEY)
            if not stored or file is None or stored["sig"] != signature:
                return
            preview: ArrivalImportResponse = stored["result"]
            st.info(preview.message)
            stat_row(
                [
                    ("Lô hợp lệ", format_number(preview.valid_count)),
                    ("Lô S4", format_number(preview.s4_count)),
                    ("Lô S1", format_number(preview.s1_count)),
                    ("Cặp mới chưa khai báo", format_number(preview.new_pairs)),
                    ("Dòng bị loại", format_number(len(preview.rejected_rows))),
                ]
            )
            if preview.rejected_rows:
                data_table(
                    [{"Dòng": r.excel_row, "Nhà cung cấp": r.key, "Lý do": r.reason} for r in preview.rejected_rows],
                    column_config={"Dòng": count_col("Dòng")},
                    key=self.key("rejected"),
                )
            if st.button(
                f"Lưu {preview.valid_count} lô",
                type="primary",
                icon="💾",
                key=self.key("commit"),
                disabled=disabled or preview.valid_count == 0,
                help=why or ("Không có dòng hợp lệ để lưu." if preview.valid_count == 0 else None),
            ):
                request = ImportArrivalFileRequest(file=file, commit=True)

                def action() -> str:
                    result = feature.import_arrival_file(request)
                    self.state.pop(PREVIEW_KEY)
                    return result.message

                confirm_dialog(
                    self.state,
                    self.key("dlg.commit"),
                    "Xác nhận lưu hàng sắp về",
                    f"Lưu {preview.valid_count} lô? {preview.replace_count} lô hiện có (kể cả lô nhập tay) sẽ được thay bằng lô của file.",
                    "Lưu",
                    action,
                )
