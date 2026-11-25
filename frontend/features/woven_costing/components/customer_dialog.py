"""UC-18 Thêm khách hàng ngay trên costsheet (similar names shown before creating a new one)."""

import streamlit as st

from backend.core.current_user import get_current_user, set_current_user
from backend.features.woven_costing import WovenCostingController
from backend.features.woven_costing.dto.list_dto import AddCustomerRequest, AddCustomerResponse
from frontend.core.base_page import BasePage
from frontend.core.components import data_table
from frontend.features.woven_costing.components.errors import attempt
from frontend.features.woven_costing.components.flash import set_flash
from frontend.features.woven_costing.components.working import choose_customer


def add_customer_dialog(page: BasePage, feature: WovenCostingController) -> None:
    user = get_current_user()
    key = page.key("add_customer")
    result_key = f"{key}.result"
    st.session_state.pop(result_key, None)

    def done(response: AddCustomerResponse) -> None:
        choose_customer(page.state, response.customer_name)
        set_flash(page.state, response.message or f"Đã thêm khách hàng {response.customer_name}.")
        st.session_state.pop(result_key, None)
        st.rerun()

    @st.dialog("Thêm khách hàng", icon=":material/person_add:", width="medium")
    def _dialog() -> None:
        set_current_user(user)
        name = st.text_input("Tên khách hàng", max_chars=200, key=f"{key}.name")
        code = st.text_input("Mã khách hàng (2-8 ký tự)", max_chars=8, key=f"{key}.code")
        st.caption("Để trống mã khách hàng: app gợi ý mã.")
        request = {"name": (name or "").strip(), "customer_code": (code or "").strip() or None}
        if st.button("Kiểm tra", type="primary", icon=":material/fact_check:", key=f"{key}.check"):
            response = attempt(lambda: feature.add_customer(AddCustomerRequest(**request, confirm_new=False)))
            if response is not None:
                if response.created:
                    done(response)
                st.session_state[result_key] = response
        response = st.session_state.get(result_key)
        if response is None or response.created:
            return
        st.markdown("**Tên tương tự:**")
        picked = data_table(
            [{"Tên": c.name, "Mã KH": c.customer_code, "Team": c.team} for c in response.similar],
            selection="single",
            key=f"{key}.similar",
            empty_message="Không có tên tương tự.",
        )
        if response.suggested_code:
            st.caption(f"Mã gợi ý: {response.suggested_code}")
        with st.container(horizontal=True, gap="small"):
            use = st.button("Dùng tên đã chọn", disabled=not picked, key=f"{key}.use")
            confirm = st.button("Xác nhận tạo mới", type="primary", key=f"{key}.confirm")
        if use and picked:
            choose_customer(page.state, str(picked[0]["Tên"]))
            st.session_state.pop(result_key, None)
            st.rerun()
        if confirm:
            created = attempt(lambda: feature.add_customer(AddCustomerRequest(**request, confirm_new=True)))
            if created is not None:
                done(created)

    _dialog()
