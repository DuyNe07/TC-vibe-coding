"""Screen 10 (`doi-chieu-gia-ke-toan`) - Đối chiếu giá kế toán (UC-53, UC-54, bổ sung 2026-11-10)."""

from decimal import Decimal

import streamlit as st

from backend.core.gateway import gateway
from backend.features.yarn_costing import YarnCostingController
from backend.features.yarn_costing.dto.reference_dto import GetReferenceDataRequest, ReferenceDataResponse
from backend.features.yarn_costing.dto.sales_dto import (
    AccountingComparisonResponse,
    AccountingImportResponse,
    GetAccountingComparisonRequest,
    ImportAccountingFileRequest,
    ListAccountingMonthsRequest,
)
from frontend.core.base_page import BasePage
from frontend.core.components import bar_chart, data_table, download_button, empty_state, file_upload, panel, stat_row
from frontend.core.formatting import format_number
from frontend.features.yarn_costing.components.columns import count_col, date_col, datetime_col, money, percent
from frontend.features.yarn_costing.components.data_warnings import show_data_warnings
from frontend.features.yarn_costing.components.dialogs import confirm_dialog
from frontend.features.yarn_costing.components.display import percent_text, percent_value, plain, vnd
from frontend.features.yarn_costing.components.flash import show_flash
from frontend.features.yarn_costing.components.labels import factory_codes, factory_label
from frontend.features.yarn_costing.components.permissions import action_state, explain

BOTH = "Cả hai"
PREVIEW_KEY = "z_preview"
DONE_KEY = "z_done"
NO_MONTH = "Chưa có file giá thành kế toán. Sales hoặc Phòng SO tải file Z ở khối bên dưới."


def month_text(period: str) -> str:
    year, month = period.split("-")
    return f"{month}/{year}"


class AccountingPage(BasePage):
    title = "Đối chiếu giá kế toán"
    menu_group = "Dùng chung"
    icon = "🧾"
    slug = "doi-chieu-gia-ke-toan"
    description = (
        "So giá định mức trên app với giá thành kế toán từng tháng (file Z) theo mã kế toán; tải file Z hằng tháng."
    )

    def render(self) -> None:
        feature = gateway.open(YarnCostingController)
        reference = feature.get_reference_data(GetReferenceDataRequest(factory_code=None))
        show_data_warnings(reference)
        show_flash(self.state)
        months = feature.list_accounting_months(ListAccountingMonthsRequest()).items
        if months:
            self._comparison(feature, reference, [m.period for m in months])
        else:
            empty_state(NO_MONTH)
        self._upload(feature)
        with panel("Các tháng đã lưu", icon="🗂️"):
            data_table(
                [
                    {
                        "Tháng": month_text(m.period),
                        "File": m.file_name,
                        "Sheet": m.sheet_name,
                        "Số mã": m.row_count,
                        "Tổng số lượng (kg)": plain(m.total_quantity),
                        "Người tải": m.imported_by,
                        "Lúc tải": m.imported_at,
                    }
                    for m in months
                ],
                column_config={
                    "Số mã": count_col("Số mã"),
                    "Tổng số lượng (kg)": money("Tổng số lượng (kg)"),
                    "Lúc tải": datetime_col("Lúc tải"),
                },
                empty_message="Chưa có tháng nào.",
                key=self.key("months"),
            )

    # ---- UC-54 ----
    def _comparison(self, feature: YarnCostingController, reference: ReferenceDataResponse, periods: list[str]) -> None:
        factories = reference.factories
        with panel("Bộ lọc", icon="🔎"):
            c1, c2, c3, c4 = st.columns(4)
            period = c1.selectbox("Tháng", periods, format_func=month_text, key=self.key("period"))
            factory = c2.selectbox(
                "Xưởng",
                [BOTH, *factory_codes(factories)],
                format_func=lambda c: c if c == BOTH else factory_label(factories, c),
                key=self.key("factory"),
            )
            small = c3.number_input(
                "Sản lượng nhỏ dưới (kg)", min_value=0.0, value=100.0, step=10.0, key=self.key("small")
            )
            gap = c4.number_input("Lệch nhiều trên (%)", min_value=0.0, value=10.0, step=1.0, key=self.key("gap"))
            t1, t2 = st.columns(2)
            only_gap = t1.toggle("Chỉ hiện mã lệch nhiều", key=self.key("only_gap"))
            hide_small = t2.toggle("Ẩn mã sản lượng nhỏ", key=self.key("hide_small"))
        if small <= 0 or gap <= 0:
            st.warning("Mức cảnh báo phải là số lớn hơn 0.", icon="⚠️")
            return
        data: AccountingComparisonResponse = feature.get_accounting_comparison(
            GetAccountingComparisonRequest(
                period=period,
                factory_code=None if factory == BOTH else factory,
                small_kg=Decimal(str(small)),
                gap_percent=Decimal(str(gap)),
                only_gap=only_gap,
                hide_small=hide_small,
            )
        )
        stat_row(
            [
                ("Mã so được", format_number(data.matched_count)),
                ("Lệch nhiều", format_number(data.gap_count)),
                ("Sản lượng nhỏ", format_number(data.small_count)),
                ("Không có trên app", format_number(data.missing_count)),
                ("Chênh bình quân (theo sản lượng)", percent_text(data.weighted_gap_percent)),
            ]
        )
        with panel(f"Đối chiếu tháng {month_text(period)}", icon="📋"):
            st.caption(
                "Giá kế toán chế biến = (Cộng − VLC) ÷ Số lượng. Giá app = giá đang hiệu lực ngày cuối tháng (lịch sử giá); "
                "chưa có lịch sử trước ngày đó thì dùng giá hiện tại. Chênh lệch = Giá app − Giá kế toán."
            )
            data_table(
                [
                    {
                        "Xưởng": str(r.factory_code),
                        "Mã kế toán": r.accounting_code,
                        "Tên sợi (kế toán)": r.product_name,
                        "Mã dòng app": r.line_code,
                        "Tên chuẩn": r.yarn_name,
                        "Số lượng (kg)": plain(r.quantity),
                        "Giá app": vnd(r.app_total),
                        "Ngày giá app": r.app_price_date,
                        "Ghi chú giá app": r.app_price_note,
                        "Giá KT chế biến": vnd(r.accounting_conversion),
                        "Chênh lệch": vnd(r.difference),
                        "Chênh lệch %": percent_value(r.difference_percent),
                        "Cảnh báo": " ".join(r.warnings),
                        "Nhân công app": vnd(r.app_labor),
                        "NC+BT KT": vnd(r.kt_labor),
                        "Khấu hao app": vnd(r.app_depreciation),
                        "Khấu hao KT": vnd(r.kt_depreciation),
                        "Điện app": vnd(r.app_electricity),
                        "Động lực KT": vnd(r.kt_power),
                        "Vật tư app": vnd(r.app_materials),
                        "Vật tư KT": vnd(r.kt_materials),
                        "CPQL app": vnd(r.app_overhead),
                        "CPQL KT": vnd(r.kt_overhead),
                        "Giá thành KT có nguyên liệu": vnd(r.accounting_unit_cost),
                    }
                    for r in data.rows
                ],
                column_config={
                    "Mã kế toán": st.column_config.TextColumn("Mã kế toán", pinned=True),
                    "Số lượng (kg)": money("Số lượng (kg)"),
                    "Ngày giá app": date_col("Ngày giá app"),
                    "Chênh lệch %": percent("Chênh lệch %"),
                    **{
                        label: money(label)
                        for label in (
                            "Giá app",
                            "Giá KT chế biến",
                            "Chênh lệch",
                            "Nhân công app",
                            "NC+BT KT",
                            "Khấu hao app",
                            "Khấu hao KT",
                            "Điện app",
                            "Động lực KT",
                            "Vật tư app",
                            "Vật tư KT",
                            "CPQL app",
                            "CPQL KT",
                            "Giá thành KT có nguyên liệu",
                        )
                    },
                },
                empty_message="Không có mã nào phù hợp bộ lọc.",
                key=self.key("rows"),
            )
        with panel("20 mã lệch nhiều nhất", icon="📊"):
            bar_chart(
                [
                    {"Mã kế toán": r.accounting_code, "Chênh lệch %": percent_value(r.difference_percent)}
                    for r in data.top_gaps
                ],
                x="Mã kế toán",
                y="Chênh lệch %",
                key=self.key("chart"),
                horizontal=True,
                empty_message="Không có mã để vẽ biểu đồ.",
            )
        with panel(f"Mã trong file Z chưa có trên app ({len(data.missing)})", icon="❓"):
            data_table(
                [
                    {
                        "Xưởng": str(m.factory_code),
                        "Mã kế toán": m.accounting_code,
                        "Tên sợi": m.product_name,
                        "Số lượng (kg)": plain(m.quantity),
                        "Giá KT chế biến": vnd(m.accounting_conversion),
                    }
                    for m in data.missing
                ],
                column_config={"Số lượng (kg)": money("Số lượng (kg)"), "Giá KT chế biến": money("Giá KT chế biến")},
                empty_message="Mọi mã trong file đều có trên app.",
                key=self.key("missing"),
            )

    # ---- UC-53 ----
    def _upload(self, feature: YarnCostingController) -> None:
        disabled, why = action_state("UC-53")
        with panel("Tải file Z", icon="📤"):
            st.caption(
                "File 'Bảng tổng hợp giá thành sợi' kế toán gửi hằng tháng, giữ nguyên. App đọc mọi sheet tên 'Z SỢI Txx.yy' "
                "(mỗi sheet một tháng). Tải lại một tháng đã có thì bản mới thay bản cũ (bản cũ vẫn được giữ để tra)."
            )
            file = file_upload("File Z", types=[".xlsx", ".xlsm", ".xls"], key=self.key("z_file"))
            signature = (file.filename, len(file.content)) if file is not None else None
            if st.button(
                "Kiểm tra file",
                type="primary",
                icon="🔍",
                key=self.key("z_check"),
                disabled=disabled or file is None,
                help=why or ("Vui lòng chọn file Excel." if file is None else None),
            ):
                preview = feature.import_accounting_file(ImportAccountingFileRequest(file=file, commit=False))
                self.state.set(PREVIEW_KEY, {"sig": signature, "result": preview})
                self.state.pop(DONE_KEY)
            explain(why)
            stored = self.state.get(PREVIEW_KEY)
            if stored and file is not None and stored["sig"] == signature:
                preview: AccountingImportResponse = stored["result"]
                st.info(preview.message)
                self._result(preview, "preview")
                count = sum(1 for m in preview.months if m.s1_count + m.s4_count > 0)
                if st.button(
                    f"Lưu {count} tháng",
                    type="primary",
                    icon="💾",
                    key=self.key("z_commit"),
                    disabled=disabled or count == 0,
                    help=why or ("Không có dòng hợp lệ để lưu." if count == 0 else None),
                ):
                    request = ImportAccountingFileRequest(file=file, commit=True)
                    first = next((m.period for m in preview.months if m.s1_count + m.s4_count > 0), "")

                    def action() -> str:
                        result = feature.import_accounting_file(request)
                        self.state.set(DONE_KEY, result)
                        self.state.pop(PREVIEW_KEY)
                        st.session_state[self.key("period")] = first  # select the month just saved
                        return result.message

                    replaced = [m for m in preview.months if m.note.startswith("Tháng này đã có")]
                    confirm_dialog(
                        self.state,
                        self.key("dlg.z_commit"),
                        "Xác nhận lưu giá thành kế toán",
                        f"Lưu {count} tháng ({preview.valid_count} mã)?"
                        + (f" {len(replaced)} tháng đã có sẽ được thay bằng bản mới." if replaced else ""),
                        "Lưu",
                        action,
                    )
            done: AccountingImportResponse | None = self.state.get(DONE_KEY)
            if done is not None:
                st.success(done.message)
                self._result(done, "done")
                if done.result_file is not None:
                    download_button(done.result_file, label="Tải kết quả nhập file", key=self.key("z_result"))

    def _result(self, result: AccountingImportResponse, key: str) -> None:
        data_table(
            [
                {
                    "Tháng": month_text(m.period) if m.period else "",
                    "Sheet": m.sheet,
                    "Số mã S1": m.s1_count,
                    "Số mã S4": m.s4_count,
                    "Tổng số lượng (kg)": plain(m.total_quantity),
                    "Dòng bị loại": m.rejected_count,
                    "Ghi chú": m.note,
                }
                for m in result.months
            ],
            column_config={
                "Số mã S1": count_col("Số mã S1"),
                "Số mã S4": count_col("Số mã S4"),
                "Tổng số lượng (kg)": money("Tổng số lượng (kg)"),
                "Dòng bị loại": count_col("Dòng bị loại"),
            },
            key=self.key(f"z_months.{key}"),
        )
        if result.rejected_rows:
            st.markdown("**Dòng bị loại**")
            data_table(
                [{"Sheet": r.sheet, "Dòng": r.excel_row, "Mã": r.key, "Lý do": r.reason} for r in result.rejected_rows],
                column_config={"Dòng": count_col("Dòng")},
                key=self.key(f"z_rejected.{key}"),
            )
