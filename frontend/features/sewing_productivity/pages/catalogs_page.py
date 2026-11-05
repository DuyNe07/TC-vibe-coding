"""Screen 9 - Danh mục: 4 tabs, each with a table edited in place and the list of what is still missing."""

from collections.abc import Callable, Mapping, Sequence
from typing import Any

import streamlit as st

from backend.core.base import EmptyRequest
from backend.core.exceptions import AppError
from backend.core.gateway import gateway
from backend.features.sewing_productivity import SewingProductivityController
from backend.features.sewing_productivity.dto.catalog_dto import (
    SaveCatalogResponse,
    SaveCustomerGroupsRequest,
    SaveLineMappingsRequest,
    SaveProductGroupsRequest,
    SaveStyleProductsRequest,
)
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, editable_table, section_title, show_error
from frontend.features.sewing_productivity.components.page_messages import (
    leave_flash,
    show_flash,
    show_no_permission,
)

TAB_LABELS = ("Nhóm sản phẩm", "Nhóm khách hàng", "Số chuyền Fac 1", "Tên sản phẩm theo style")
COUNT_COLUMN = {"Số dòng": st.column_config.NumberColumn(format="localized")}


class CatalogsPage(BasePage):
    title = "Danh mục"
    icon = "🗂️"
    slug = "catalogs"
    description = "Sửa các danh mục dùng để làm sạch dữ liệu. Sửa xong áp dụng ngay cho toàn bộ dữ liệu."
    menu_group = "Quản lý dữ liệu"

    def render(self) -> None:
        feature = gateway.open(SewingProductivityController)
        try:
            catalogs = feature.get_catalogs(EmptyRequest())
        except AppError as exc:  # BR-09 is the only failure of this use case
            show_no_permission(exc)
            return
        show_flash(self.state)

        # not lazy: a closed tab would lose what is being edited, because an edit table cannot keep its state
        products, customers, lines, styles = st.tabs(TAB_LABELS, key=self.key("tabs"))
        with products:
            self._grid(
                "products",
                catalogs.product_groups,
                {"product_name": "Tên sản phẩm", "product_group": "Nhóm sản phẩm"},
                "Lưu nhóm sản phẩm",
                lambda rows: feature.save_product_groups(SaveProductGroupsRequest(rows=rows)),
            )
            section_title("Tên sản phẩm chưa phân nhóm")
            data_table(
                [
                    {"Tên sản phẩm": item.product_name, "Số dòng": item.row_count}
                    for item in catalogs.unclassified_products
                ],
                column_config=COUNT_COLUMN,
                key=self.key("unclassified"),
                empty_message="Không còn tên sản phẩm chưa phân nhóm.",
            )
        with customers:
            self._grid(
                "customers",
                catalogs.customer_groups,
                {"customer_name": "Tên khách hàng", "customer_group": "Nhóm khách hàng"},
                "Lưu nhóm khách hàng",
                lambda rows: feature.save_customer_groups(SaveCustomerGroupsRequest(rows=rows)),
            )
            section_title("Tên khách hàng đang có")
            data_table(
                [
                    {
                        "Tên khách hàng": item.customer_name,
                        "Nhóm hiện tại": item.customer_group,
                        "Số dòng": item.row_count,
                    }
                    for item in catalogs.customer_names
                ],
                column_config=COUNT_COLUMN,
                key=self.key("customer_names"),
                empty_message="Chưa có tên khách hàng nào.",
            )
        with lines:
            self._grid(
                "lines",
                catalogs.line_mappings,
                {"old_line": "Chuyền cũ", "new_line": "Chuyền mới"},
                "Lưu bảng số chuyền",
                lambda rows: feature.save_line_mappings(SaveLineMappingsRequest(rows=rows)),
            )
        with styles:
            self._grid(
                "styles",
                catalogs.style_products,
                {"style": "Style", "product_name": "Tên sản phẩm"},
                "Lưu tên sản phẩm",
                lambda rows: feature.save_style_products(SaveStyleProductsRequest(rows=rows)),
            )
            section_title("Style chưa có tên sản phẩm")
            data_table(
                [
                    {"Style": item.style, "Khách hàng": item.customer_name, "Số dòng": item.row_count}
                    for item in catalogs.styles_without_product
                ],
                column_config=COUNT_COLUMN,
                key=self.key("styles_without_product"),
                empty_message="Không còn style chưa có tên sản phẩm.",
            )

    def _grid(
        self,
        name: str,
        rows: Sequence[Any],
        labels: Mapping[str, str],
        button: str,
        save: Callable[[list[dict[str, Any]]], SaveCatalogResponse],
    ) -> None:
        """The columns are the DTO fields, so the edited rows go straight into the request."""
        version = self.state.get(f"grid_{name}_version", 0)
        edited = editable_table(
            [row.model_dump() for row in rows],
            key=self.key(f"grid_{name}_{version}"),
            columns=list(labels),
            column_config={field: st.column_config.TextColumn(label) for field, label in labels.items()},
            allow_add_delete=True,
        )
        if not st.button(button, type="primary", key=self.key(f"save_{name}")):
            return
        try:
            result = save(edited)
        except AppError as exc:  # shown under the table, the edits stay (AC-48)
            show_error(exc)
            return
        leave_flash(self.state, result.message)
        # a new key: the editor would otherwise apply the rows just added on top of the saved data, doubling them
        self.state.set(f"grid_{name}_version", version + 1)
        st.rerun()
