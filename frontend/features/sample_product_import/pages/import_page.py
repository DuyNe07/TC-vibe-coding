"""Screen 1 - Import from Excel (URL: /sample-product-import)."""

import streamlit as st

from backend.core.base import EmptyRequest
from backend.core.gateway import gateway
from backend.features.sample_product_import import SampleProductImportController
from backend.features.sample_product_import.dto.import_dto import CommitImportRequest, PreviewImportRequest
from frontend.core.base_page import BasePage
from frontend.core.components import download_button, file_upload, panel, show_success, stat_row
from frontend.features.sample_product_import.components.import_table import import_rows_table
from frontend.features.sample_product_import.pages.product_list_page import ProductListPage


class ImportPage(BasePage):
    title = "Nhập sản phẩm từ Excel"
    icon = "📥"
    description = "Tải file mẫu, điền dữ liệu, kiểm tra lỗi theo quy tắc nghiệp vụ rồi lưu vào hệ thống."

    def render(self) -> None:
        products = gateway.open(SampleProductImportController)
        self.link_to(ProductListPage, label="Xem danh sách sản phẩm →")

        with panel(
            "Bước 1 · Tải file mẫu", icon="📄", description="Giữ nguyên dòng tiêu đề, mỗi dòng là một sản phẩm."
        ):
            template = products.download_template(EmptyRequest())
            download_button(template, label="Tải file Excel mẫu", key=self.key("template"))

        with panel("Bước 2 · Chọn file để kiểm tra", icon="📤"):
            file = file_upload("File Excel sản phẩm", types=(".xlsx", ".xls"), key=self.key("upload"))
        if file is None:
            return

        with st.spinner("Đang kiểm tra..."):
            result = products.preview_import(PreviewImportRequest(file=file))  # errors shown by BasePage
        with panel("Bước 3 · Kết quả kiểm tra", icon="🔎"):
            stat_row(
                [
                    ("Tổng dòng", result.total_rows),
                    ("Hợp lệ", result.valid_rows),
                    ("Lỗi", result.invalid_rows),
                    ("Tạo mới", result.create_count),
                    ("Cập nhật", result.update_count),
                ]
            )
            only_errors = st.toggle("Chỉ hiện dòng lỗi", key=self.key("only_errors"), disabled=result.invalid_rows == 0)
            rows = [r for r in result.rows if r.errors] if only_errors else result.rows
            import_rows_table(rows, key=self.key("preview_table"))

            label = f"Lưu {result.valid_rows} dòng hợp lệ"
            if st.button(label, type="primary", disabled=result.valid_rows == 0, key=self.key("commit")):
                with st.spinner("Đang lưu..."):
                    saved = products.commit_import(CommitImportRequest(file=file))
                show_success(f"Đã tạo {saved.created}, cập nhật {saved.updated}, bỏ qua {saved.rejected} dòng lỗi.")
