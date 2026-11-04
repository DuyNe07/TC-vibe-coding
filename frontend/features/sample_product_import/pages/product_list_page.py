"""Screen 2 - Product list & stock report (URL: /duyne07-sample-product-import-products)."""

import streamlit as st

from backend.core.gateway import gateway
from backend.features.sample_product_import import SampleProductImportController
from backend.features.sample_product_import.dto.product_dto import (
    ExportProductsRequest,
    ListProductsRequest,
    StockStatus,
)
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, panel, pie_chart, stat_row
from frontend.core.formatting import format_currency, format_datetime, format_number
from frontend.features.sample_product_import.components.labels import STOCK_STATUS_LABELS


class ProductListPage(BasePage):
    title = "Danh sách sản phẩm"
    icon = "📋"
    slug = "products"
    description = "Tra cứu sản phẩm, trạng thái tồn kho và xuất báo cáo Excel."

    def render(self) -> None:
        with panel("Bộ lọc", icon="🔎"):
            left, right = st.columns([2, 1])
            keyword = left.text_input("Từ khoá (mã hoặc tên)", key=self.key("keyword"))
            status = right.selectbox(
                "Trạng thái",
                [None, *StockStatus],
                key=self.key("status"),
                format_func=lambda s: "Tất cả" if s is None else STOCK_STATUS_LABELS[s],
            )

        products = gateway.open(SampleProductImportController)
        data = products.list_products(ListProductsRequest(keyword=keyword, stock_status=status))
        summary = data.summary
        stat_row(
            [
                ("Sản phẩm", format_number(summary.product_count)),
                ("Tổng số lượng", format_number(summary.total_quantity)),
                ("Tổng giá trị", format_currency(summary.total_value)),
                ("Hết / sắp hết", f"{summary.out_of_stock} / {summary.low_stock}"),
            ]
        )

        table_col, chart_col = st.columns([3, 1])
        with table_col, panel("Sản phẩm", icon="📦"):
            data_table(
                [
                    {
                        "Mã SP": p.code,
                        "Tên sản phẩm": p.name,
                        "Đơn vị": p.unit,
                        "Số lượng": p.quantity,
                        "Đơn giá": p.unit_price,
                        "Thành tiền": p.total_value,
                        "Trạng thái": STOCK_STATUS_LABELS[p.stock_status],
                        "Cập nhật": format_datetime(p.updated_at),
                    }
                    for p in data.items
                ],
                column_config={
                    "Đơn giá": st.column_config.NumberColumn(format="localized"),
                    "Thành tiền": st.column_config.NumberColumn(format="localized"),
                },
                empty_message="Chưa có sản phẩm. Hãy nhập từ Excel trước.",
                key=self.key("table"),
            )
            if data.items:
                request = ExportProductsRequest(keyword=keyword, stock_status=status)
                download_button(  # the file is built only when the user clicks
                    lambda: products.export_products(request),
                    label="Xuất Excel",
                    key=self.key("export"),
                    primary=True,
                    file_name="ton-kho.xlsx",
                )
        with chart_col, panel("Tồn kho", icon="📊"):
            counts = {"Hết hàng": summary.out_of_stock, "Sắp hết": summary.low_stock, "Còn hàng": summary.in_stock}
            pie_chart(
                [{"Trạng thái": name, "Số sản phẩm": count} for name, count in counts.items()],
                names="Trạng thái",
                values="Số sản phẩm",
                key=self.key("chart"),
                height=260,
                empty_message="Chưa có dữ liệu.",
            )
