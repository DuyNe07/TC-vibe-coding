"""Screen 6 (`nhap-du-lieu-excel`) - Nhập dữ liệu từ Excel (UC-33..UC-35, UC-41, UC-44, UC-45)."""

from datetime import date
from typing import Any

import streamlit as st

from backend.core.base import UploadedFileDTO
from backend.core.gateway import gateway
from backend.features.yarn_costing import YarnCostingController
from backend.features.yarn_costing.dto.common_dto import ImportMode
from backend.features.yarn_costing.dto.import_dto import (
    DownloadComponentTemplateRequest,
    DownloadTemplateRequest,
    GetLegacyComparisonRequest,
    ImportResultResponse,
    ImportWorkbookRequest,
    ListImportBatchesRequest,
)
from backend.features.yarn_costing.dto.reference_dto import GetReferenceDataRequest
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, file_upload, panel, stat_row
from frontend.core.formatting import format_number
from frontend.features.yarn_costing.components.columns import count_col, date_col, datetime_col, money, percent
from frontend.features.yarn_costing.components.component_import import render_component_import
from frontend.features.yarn_costing.components.data_warnings import show_data_warnings
from frontend.features.yarn_costing.components.dialogs import confirm_dialog
from frontend.features.yarn_costing.components.display import fmt_date, percent_value, vnd
from frontend.features.yarn_costing.components.factory_picker import factory_segment
from frontend.features.yarn_costing.components.flash import show_flash
from frontend.features.yarn_costing.components.labels import IMPORT_MODE_LABELS, label_of
from frontend.features.yarn_costing.components.permissions import action_state, explain, is_so, own_factory

PREVIEW_KEY = "import_preview"
COMMITTED_KEY = "import_committed"
SELECTED_IMPORT_KEY = "selected_import_id"
COST_ITEMS = (
    ("labor", "Nhân công"),
    ("depreciation", "Khấu hao"),
    ("electricity", "Điện"),
    ("materials", "Vật tư"),
    ("overhead", "CPQL"),
)
SHEET_CONFIG = {
    "Đọc": count_col("Đọc"),
    "Tạo": count_col("Tạo"),
    "Cập nhật": count_col("Cập nhật"),
    "Bị loại": count_col("Bị loại"),
}


def _sheet_rows(result: ImportResultResponse) -> list[dict[str, Any]]:
    return [
        {
            "Sheet": s.sheet,
            "Đọc": s.read,
            "Tạo": s.created,
            "Cập nhật": s.updated,
            "Bị loại": s.rejected,
            "Ghi chú": s.skipped_message,
        }
        for s in result.sheets
    ]


class ExcelImportPage(BasePage):
    title = "Nhập dữ liệu từ Excel"
    menu_group = "Phòng SO"
    icon = "📥"
    slug = "nhap-du-lieu-excel"
    description = "Tải file mẫu, chuyển dữ liệu cũ từ file Excel, cập nhật hàng loạt NSM và tiêu hao, đối chiếu giá cũ với giá app."

    def render(self) -> None:
        feature = gateway.open(YarnCostingController)
        reference = feature.get_reference_data(GetReferenceDataRequest(factory_code=None))
        show_data_warnings(reference)
        show_flash(self.state)

        with panel("Chọn dữ liệu", icon="⚙️"):
            c1, c2, c3, c4 = st.columns([1, 2, 1, 1], vertical_alignment="bottom")
            with c1:
                factory = factory_segment(reference.factories, self.key("factory"), own_factory())
            if factory is None:
                return
            mode = c2.radio(
                "Loại tải",
                [ImportMode.BAN_DAU, ImportMode.HANG_LOAT, ImportMode.THANH_PHAN],
                index=1,
                horizontal=True,
                format_func=lambda v: label_of(IMPORT_MODE_LABELS, v),
                key=self.key("mode"),
            )
            mode = mode or ImportMode.HANG_LOAT
            components = mode == ImportMode.THANH_PHAN
            cutoff = c3.date_input(
                "Ngày hiệu lực" if components else "Ngày chốt",
                value=date.today(),
                format="DD/MM/YYYY",
                key=self.key("cutoff"),
            )
            template_key = f"template.{factory}.{'components' if components else 'workbook'}"
            if c4.button("Tải file mẫu", icon="📄", key=self.key("template")):
                if components:  # UC-44
                    file = feature.download_component_template(DownloadComponentTemplateRequest(factory_code=factory))
                else:  # UC-33
                    file = feature.download_template(DownloadTemplateRequest(factory_code=factory))
                self.state.set(template_key, file)
            template = self.state.get(template_key)
            if template is not None:
                download_button(template, label="Tải file mẫu về máy", key=self.key(f"{template_key}.dl"))
            if not is_so() and not components:
                st.caption(
                    "Xưởng chỉ được 'Cập nhật hàng loạt' sheet '1. Input NSM' và '2. Input tieu hao' của xưởng mình; "
                    "các sheet khác sẽ bị bỏ qua."
                )

        if components:  # UC-45
            render_component_import(self, feature, factory, cutoff)
            import_id = self._import_list(feature, factory)
            if import_id:
                self._comparison(feature, import_id)
            return

        with panel("Tải file", icon="📤"):
            file = file_upload(
                "File Excel",
                types=[".xlsx", ".xlsm", ".xls"],
                key=self.key("file"),
                help="Tối đa 60 MB, mỗi sheet tối đa 10.000 dòng.",
            )
            disabled, why = action_state("UC-34", factory)
            if not disabled and mode == ImportMode.BAN_DAU and not is_so():
                disabled, why = True, "Chuyển dữ liệu ban đầu chỉ Phòng SO được thực hiện."
            signature = self._signature(file, factory, mode, cutoff)
            if st.button(
                "Kiểm tra file",
                type="primary",
                icon="🔍",
                key=self.key("check"),
                disabled=disabled or file is None,
                help=why or ("Vui lòng chọn file Excel." if file is None else None),
            ):
                preview = feature.import_workbook(
                    ImportWorkbookRequest(
                        factory_code=factory,
                        mode=mode,
                        cutoff_date=cutoff,
                        file=file,
                        commit=False,
                    )
                )
                self.state.set(PREVIEW_KEY, {"sig": signature, "result": preview})
                self.state.pop(COMMITTED_KEY)
            explain(why)

        stored = self.state.get(PREVIEW_KEY)
        if stored and file is not None and stored["sig"] == signature:
            self._preview_block(feature, stored["result"], file, factory, mode, cutoff, disabled, why)
        committed = self.state.get(COMMITTED_KEY)
        if committed is not None:
            self._committed_block(committed)

        import_id = self._import_list(feature, factory)
        if import_id:
            self._comparison(feature, import_id)

    @staticmethod
    def _signature(file: UploadedFileDTO | None, factory: str, mode: ImportMode, cutoff: date) -> tuple | None:
        if file is None:
            return None
        return (file.filename, len(file.content), factory, str(mode), cutoff.isoformat())

    def _result_tables(self, result: ImportResultResponse, key: str) -> None:
        stat_row(
            [
                ("Dòng hợp lệ", format_number(result.valid_count)),
                ("Dòng bị loại", format_number(len(result.rejected_rows))),
                ("Sheet đã đọc", format_number(len(result.sheets))),
            ]
        )
        data_table(
            _sheet_rows(result),
            column_config=SHEET_CONFIG,
            empty_message="Không đọc được sheet nào.",
            key=self.key(f"{key}.sheets"),
        )
        only_errors = st.toggle("Chỉ hiện dòng lỗi", value=True, key=self.key(f"{key}.only_errors"))
        rows = [
            {"Sheet": r.sheet, "Dòng": r.excel_row, "Mã / nhóm": r.key, "Lý do": r.reason} for r in result.rejected_rows
        ]
        if not only_errors:
            rows += [
                {"Sheet": s.sheet, "Dòng": None, "Mã / nhóm": "", "Lý do": s.skipped_message}
                for s in result.sheets
                if s.skipped_message
            ]
        data_table(
            rows,
            column_config={"Dòng": count_col("Dòng")},
            empty_message="Không có dòng nào bị loại.",
            key=self.key(f"{key}.rejected"),
        )
        if result.result_file is not None:
            download_button(result.result_file, label="Tải kết quả nhập file", key=self.key(f"{key}.result_dl"))

    def _preview_block(
        self,
        feature: YarnCostingController,
        preview: ImportResultResponse,
        file: UploadedFileDTO,
        factory: str,
        mode: ImportMode,
        cutoff: date,
        disabled: bool,
        why: str | None,
    ) -> None:
        with panel("Kết quả kiểm tra file", icon="📊"):
            if preview.message:
                st.info(preview.message)
            self._result_tables(preview, "preview")
            count = preview.valid_count
            if st.button(
                f"Lưu {count} dòng hợp lệ",
                type="primary",
                icon="💾",
                key=self.key("commit"),
                disabled=disabled or count == 0,
                help=why,
            ):
                request = ImportWorkbookRequest(
                    factory_code=factory,
                    mode=mode,
                    cutoff_date=cutoff,
                    file=file,
                    commit=True,
                )

                def action() -> str:
                    result = feature.import_workbook(request)
                    self.state.set(COMMITTED_KEY, result)
                    self.state.pop(PREVIEW_KEY)
                    if result.import_id:
                        self.state.set(SELECTED_IMPORT_KEY, result.import_id)
                    return result.message

                confirm_dialog(
                    self.state,
                    self.key("dlg.commit"),
                    "Xác nhận lưu dữ liệu từ file",
                    f"Lưu {count} dòng hợp lệ từ file {file.filename}? App sẽ lưu dữ liệu cho xưởng {factory} và tính "
                    f"lại toàn bộ giá của xưởng với ngày hiệu lực {fmt_date(cutoff)}.",
                    "Lưu dữ liệu",
                    action,
                )

    def _committed_block(self, committed: ImportResultResponse) -> None:
        with panel("Kết quả lần lưu vừa rồi", icon="✅"):
            self._result_tables(committed, "committed")
            if committed.import_id and st.button("Đối chiếu giá cũ", icon="⚖️", key=self.key("compare_committed")):
                self.state.set(SELECTED_IMPORT_KEY, committed.import_id)
                st.rerun()

    def _import_list(self, feature: YarnCostingController, factory: str) -> str | None:
        batches = feature.list_import_batches(ListImportBatchesRequest(factory_code=factory))
        with panel("Các lần nhập", icon="🗂️"):
            picked = data_table(
                [
                    {
                        "Mã lần nhập": b.import_id,
                        "Xưởng": str(b.factory_code),
                        "Loại": b.mode.value,
                        "Ngày chốt": b.cutoff_date,
                        "Tên file": b.file_name,
                        "Người nhập": b.imported_by,
                        "Lúc nhập": b.imported_at,
                        "Tạo": b.created_count,
                        "Cập nhật": b.updated_count,
                        "Bị loại": b.rejected_count,
                    }
                    for b in batches.items
                ],
                column_config={
                    "Ngày chốt": date_col("Ngày chốt"),
                    "Lúc nhập": datetime_col("Lúc nhập"),
                    "Tạo": count_col("Tạo"),
                    "Cập nhật": count_col("Cập nhật"),
                    "Bị loại": count_col("Bị loại"),
                },
                selection="single",
                key=self.key(f"imports.{factory}"),
                empty_message="Chưa có lần nhập file nào.",
            )
        if picked:
            return str(picked[0]["Mã lần nhập"])
        selected = self.state.get(SELECTED_IMPORT_KEY)
        known = {b.import_id for b in batches.items}
        return selected if selected in known else None

    def _comparison(self, feature: YarnCostingController, import_id: str) -> None:
        with panel(f"Đối chiếu giá cũ - {import_id}", icon="⚖️"):
            only = st.toggle("Chỉ hiện mã lệch trên 1 VND/kg", value=False, key=self.key(f"cmp_only.{import_id}"))
            comparison = feature.get_legacy_comparison(
                GetLegacyComparisonRequest(import_id=import_id, only_mismatch=only)
            )
            stat_row(
                [
                    ("Mã khớp", format_number(comparison.matched_count)),
                    ("Mã lệch", format_number(comparison.mismatched_count)),
                    ("Mã chưa tính được", format_number(comparison.not_priced_count)),
                ]
            )
            rows = [
                {
                    "Mã": r.yarn_code,
                    "Tên sợi": r.yarn_name,
                    "Tổng cũ": vnd(r.old_total),
                    "Tổng app": vnd(r.app_total),
                    "Chênh lệch (VND)": vnd(r.diff_vnd),
                    "Chênh lệch (%)": percent_value(r.diff_percent),
                    **{f"{label} cũ": vnd(getattr(r, f"old_{field}")) for field, label in COST_ITEMS},
                    **{f"{label} mới": vnd(getattr(r, f"new_{field}")) for field, label in COST_ITEMS},
                    "Trạng thái": r.status,
                }
                for r in comparison.items
            ]
            money_cols = ["Tổng cũ", "Tổng app", "Chênh lệch (VND)"]
            money_cols += [f"{label} cũ" for _, label in COST_ITEMS] + [f"{label} mới" for _, label in COST_ITEMS]
            data_table(
                rows,
                column_config={**{c: money(c) for c in money_cols}, "Chênh lệch (%)": percent("Chênh lệch (%)")},
                empty_message="Lần nhập này không có giá cũ để đối chiếu.",
                key=self.key(f"cmp_table.{import_id}"),
            )
            download_button(comparison.file, label="Xuất Excel", key=self.key(f"cmp_dl.{import_id}"))
