"""Screen 9 - Catalogs: 4 tabs, each with a table edited in place and the list of what is still missing."""

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

TAB_LABELS = ("Product groups", "Customer groups", "Fac Vinh Long line numbers", "Product name by style")
COUNT_COLUMN = {"Rows": st.column_config.NumberColumn(format="localized")}


class CatalogsPage(BasePage):
    title = "Catalogs"
    icon = "🗂️"
    slug = "catalogs"
    description = "Edit the catalogs used to clean the data. A saved change applies to all the data at once."
    menu_group = "Data management"

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
                {"product_name": "Product name", "product_group": "Product group"},
                "Save product groups",
                lambda rows: feature.save_product_groups(SaveProductGroupsRequest(rows=rows)),
            )
            section_title("Product names without a group")
            data_table(
                [
                    {"Product name": item.product_name, "Rows": item.row_count}
                    for item in catalogs.unclassified_products
                ],
                column_config=COUNT_COLUMN,
                key=self.key("unclassified"),
                empty_message="Every product name has a group.",
            )
        with customers:
            self._grid(
                "customers",
                catalogs.customer_groups,
                {"customer_name": "Customer name", "customer_group": "Customer group"},
                "Save customer groups",
                lambda rows: feature.save_customer_groups(SaveCustomerGroupsRequest(rows=rows)),
            )
            section_title("Customer names in the data")
            data_table(
                [
                    {
                        "Customer name": item.customer_name,
                        "Current group": item.customer_group,
                        "Rows": item.row_count,
                    }
                    for item in catalogs.customer_names
                ],
                column_config=COUNT_COLUMN,
                key=self.key("customer_names"),
                empty_message="No customer names yet.",
            )
        with lines:
            self._grid(
                "lines",
                catalogs.line_mappings,
                {"old_line": "Old line", "new_line": "New line"},
                "Save line numbers",
                lambda rows: feature.save_line_mappings(SaveLineMappingsRequest(rows=rows)),
            )
        with styles:
            self._grid(
                "styles",
                catalogs.style_products,
                {"style": "Style", "product_name": "Product name"},
                "Save product names",
                lambda rows: feature.save_style_products(SaveStyleProductsRequest(rows=rows)),
            )
            section_title("Styles without a product name")
            data_table(
                [
                    {"Style": item.style, "Customer": item.customer_name, "Rows": item.row_count}
                    for item in catalogs.styles_without_product
                ],
                column_config=COUNT_COLUMN,
                key=self.key("styles_without_product"),
                empty_message="Every style has a product name.",
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
