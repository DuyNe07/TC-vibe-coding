"""Screen 2 - Product list & stock report (URL: /sample-product-import-products)."""

import plotly.express as px
import streamlit as st

from backend.core.gateway import gateway
from backend.features.sample_product_import import SampleProductImportController
from backend.features.sample_product_import.dto.product_dto import (
    ExportProductsRequest,
    ListProductsRequest,
    StockStatus,
)
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, panel, stat_row
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
                export = products.export_products(ExportProductsRequest(keyword=keyword, stock_status=status))
                download_button(export, label="Xuất Excel", key=self.key("export"), primary=True)
        with chart_col, panel("Tồn kho", icon="📊"):
            counts = {"Hết hàng": summary.out_of_stock, "Sắp hết": summary.low_stock, "Còn hàng": summary.in_stock}
            if summary.product_count:
                figure = px.pie(
                    names=list(counts),
                    values=list(counts.values()),
                    hole=0.55,
                    color_discrete_sequence=["#DA1E28", "#FF832B", "#24A148"],
                )
                figure.update_layout(margin={"l": 0, "r": 0, "t": 10, "b": 0}, height=260, showlegend=True)
                st.plotly_chart(figure, key=self.key("chart"))
            else:
                st.caption("Chưa có dữ liệu.")
