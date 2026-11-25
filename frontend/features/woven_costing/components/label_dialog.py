"""UC-26 In nhãn thông số vải: 1-4 fabric codes + REMARK -> Word file to download."""

from collections.abc import Sequence

import streamlit as st

from backend.core.current_user import get_current_user, set_current_user
from backend.features.woven_costing import WovenCostingController
from backend.features.woven_costing.dto.fabric_dto import LabelInputDTO, PrintLabelRequest
from frontend.core.components import download_button, editable_table
from frontend.features.woven_costing.components.errors import attempt
from frontend.features.woven_costing.components.labels import text_or_empty


def label_dialog(feature: WovenCostingController, tcfnos: Sequence[str], key: str, *, fixed: bool = False) -> None:
    """``fixed`` = one code that cannot change (the costsheet's fabric); otherwise a small editable list."""
    user = get_current_user()
    file_key = f"{key}.file"
    st.session_state.pop(file_key, None)  # called when the dialog opens: forget the file of the previous opening

    @st.dialog("In nhãn thông số vải", width="medium")
    def _dialog() -> None:
        set_current_user(user)
        if fixed and tcfnos:
            st.markdown(f"Mã vải: **{tcfnos[0]}**")
            remark = st.text_input("REMARK", max_chars=200, key=f"{key}.remark")
            labels = [LabelInputDTO(tcfno=tcfnos[0], remark=(remark or "").strip())]
        else:
            rows = [{"Mã vải": t, "REMARK": ""} for t in tcfnos] or [{"Mã vải": "", "REMARK": ""}]
            edited = editable_table(rows, key=f"{key}.rows", columns=["Mã vải", "REMARK"], allow_add_delete=True)
            st.caption("Tối đa 4 mã vải, 4 nhãn trên 1 trang.")
            labels = [
                LabelInputDTO(tcfno=text_or_empty(r.get("Mã vải")), remark=text_or_empty(r.get("REMARK")))
                for r in edited
                if text_or_empty(r.get("Mã vải"))
            ]
        if st.button("Tạo file nhãn", type="primary", icon=":material/print:", key=f"{key}.make"):
            st.session_state.pop(file_key, None)
            file = attempt(lambda: feature.print_label(PrintLabelRequest(labels=labels)))
            if file is not None:
                st.session_state[file_key] = file
        file = st.session_state.get(file_key)
        if file is not None:
            download_button(file, label="Tải file nhãn", key=f"{key}.download", primary=True)

    _dialog()
