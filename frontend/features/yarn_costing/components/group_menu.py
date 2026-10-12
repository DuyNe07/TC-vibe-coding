"""Khối "📂 Menu theo nhóm người dùng" ở đầu mỗi màn hình (mục 8 "Giao diện đã chốt", chốt 2026-09-29).

Menu bên trái là phần khung dùng chung (không gấp / mở được), nên chức năng tự có khối menu mở rộng / thu gọn này: 5 nhóm
người dùng, mỗi nhóm cũng mở rộng / thu gọn được, mỗi dòng là liên kết mở màn hình. Cũng hiện cảnh báo dữ liệu (BR-61).
"""

import streamlit as st

from backend.features.yarn_costing.dto.reference_dto import ReferenceDataResponse
from frontend.core.base_page import BasePage

MENU_TITLE = "📂 Menu theo nhóm người dùng"


def _menu_groups() -> list[tuple[str, list[tuple[type[BasePage], str]]]]:
    # imported here: the pages import this component
    from frontend.features.yarn_costing.pages.dashboard_page import DashboardPage
    from frontend.features.yarn_costing.pages.excel_import_page import ExcelImportPage
    from frontend.features.yarn_costing.pages.loss_group_page import LossGroupPage
    from frontend.features.yarn_costing.pages.master_data_page import MasterDataPage
    from frontend.features.yarn_costing.pages.nsm_pricing_page import NsmPricingPage
    from frontend.features.yarn_costing.pages.price_list_page import PriceListPage
    from frontend.features.yarn_costing.pages.user_audit_page import UserAuditPage
    from frontend.features.yarn_costing.pages.yarn_request_page import YarnRequestPage

    return [
        ("🌐 Dùng chung", [(PriceListPage, "Bảng giá đã tính"), (DashboardPage, "Dashboard kiểm soát")]),
        ("🛒 Sales", [(YarnRequestPage, "Yêu cầu tính giá")]),
        ("🏭 Xưởng sợi", [(NsmPricingPage, "Nhập NSM & tính giá"), (LossGroupPage, "Tiêu hao")]),
        (
            "🗂️ Phòng SO",
            [
                (MasterDataPage, "Dữ liệu nền & định mức"),
                (ExcelImportPage, "Nhập dữ liệu từ Excel"),
                (UserAuditPage, "Người dùng & nhật ký"),
            ],
        ),
        ("🧾 Kế toán", [(PriceListPage, "Bảng giá đã tính - nhập mã kế toán")]),
    ]


def render_group_menu(page: BasePage, reference: ReferenceDataResponse | None = None) -> None:
    """Khối menu (mặc định thu gọn); nhóm chứa màn đang mở được mở sẵn khi mở rộng khối."""
    with st.expander(MENU_TITLE, expanded=False):
        for group_label, entries in _menu_groups():
            current = any(isinstance(page, page_cls) for page_cls, _ in entries)
            with st.expander(group_label, expanded=current):
                for page_cls, label in entries:
                    if isinstance(page, page_cls):
                        st.markdown(f"**{page_cls.icon} {label} (đang mở)**")
                    else:
                        page.link_to(page_cls, label=label, icon=page_cls.icon)
    for warning in reference.data_warnings if reference is not None else []:
        st.warning(warning, icon="⚠️")
