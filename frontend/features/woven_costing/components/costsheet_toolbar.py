"""Screen 2 action bar: only the buttons in ``allowed_actions`` (status + role + owner, decided by the backend)."""

from collections.abc import Callable
from typing import Any

import streamlit as st

from backend.features.woven_costing import WovenCostingController
from backend.features.woven_costing.dto.common_dto import CostsheetAction
from backend.features.woven_costing.dto.costsheet_dto import (
    CostsheetActionRequest,
    CostsheetInputRequest,
    CostsheetResponse,
    SaveOcRequest,
)
from frontend.core.base_page import BasePage
from frontend.features.woven_costing.components.costsheet_request import build_input_request
from frontend.features.woven_costing.components.dialogs import ActionResult, confirm_dialog
from frontend.features.woven_costing.components.errors import attempt
from frontend.features.woven_costing.components.fabric_form import override_dialog
from frontend.features.woven_costing.components.flash import set_flash
from frontend.features.woven_costing.components.label_dialog import label_dialog
from frontend.features.woven_costing.components.labels import pct_text
from frontend.features.woven_costing.components.working import DIRTY, replace_working

A = CostsheetAction
UNSAVED = "Có thay đổi chưa lưu"
# UC-16 runs by itself when a cell changes (2026-11-23): no "Tính lại" button (the action stays allowed for that)
BUTTONS: tuple[tuple[CostsheetAction, str, str, bool], ...] = (
    (A.SAVE_DRAFT, "Lưu nháp", ":material/save:", True),
    (A.SUBMIT, "Gửi duyệt", ":material/send:", False),
    (A.APPROVE, "Duyệt", ":material/check:", True),
    (A.RETURN, "Trả lại", ":material/undo:", False),
    (A.COPY, "Sao chép", ":material/content_copy:", False),
    (A.NEW_VERSION, "Tạo phiên bản mới", ":material/add_circle:", False),
    (A.SAVE_OC, "Lưu OC", ":material/tag:", False),
    (A.CLOSE_ORDER, "Chốt đơn", ":material/verified:", False),
    (A.CANCEL, "Hủy", ":material/block:", False),
    (A.PRINT_LABEL, "In nhãn", ":material/print:", False),
    (A.CONFIRM_YARN_PRICES, "Xác nhận giá sợi hôm nay", ":material/event_available:", False),
    (A.EDIT_FABRIC, "Sửa thông số vải", ":material/edit:", False),
)


def warning_hint(response: CostsheetResponse) -> list[str]:
    count = len(response.warnings)
    return [f"Phiếu có {count} cảnh báo, xem thẻ Cảnh báo."] if count else []


def toolbar(page: BasePage, feature: WovenCostingController, w: CostsheetResponse, values: dict[str, Any]) -> bool:
    """Draws the buttons and runs the clicked one; True when a button was clicked on this run."""
    allowed = set(w.allowed_actions)
    shown = [b for b in BUTTONS if b[0] in allowed]
    if not shown:
        st.caption("Bạn chỉ được xem phiếu này.")
        return False
    state = page.state
    label = f"{w.costsheet_no} v{w.version}"
    oc_no = (values.get("order") or {}).get("oc_no", w.input.oc_no)

    def request(confirm: bool = False) -> CostsheetInputRequest:
        return build_input_request(w, values, confirm_yarn_prices=confirm)

    def act(
        id_request: Callable[[str | None], CostsheetResponse], warnings: bool = False
    ) -> Callable[..., ActionResult]:
        def run(reason: str | None) -> ActionResult:
            response = id_request(reason)
            replace_working(state, response)
            return response.message, (response.warning_texts if warnings else warning_hint(response))

        return run

    def apply(response: CostsheetResponse | None, default_message: str) -> None:
        if response is None:
            return
        replace_working(state, response)
        set_flash(state, response.message or default_message, warning_hint(response))
        st.rerun()

    clicked: dict[CostsheetAction, bool] = {}
    with st.container(horizontal=True, gap="small"):
        for action, text_label, icon, primary in shown:
            clicked[action] = st.button(
                text_label, icon=icon, type="primary" if primary else "secondary", key=page.key(f"act.{action}.{w.id}")
            )
            if action == A.SAVE_DRAFT and state.get(DIRTY):
                st.caption(f":orange[{UNSAVED}]")
    key = page.key(f"dialog.{w.id}")
    if clicked.get(A.SAVE_DRAFT):
        apply(attempt(lambda: feature.save_draft(request())), f"Đã lưu nháp costsheet {label}.")
    if clicked.get(A.CONFIRM_YARN_PRICES):
        apply(attempt(lambda: feature.save_draft(request(confirm=True))), f"Đã lưu nháp costsheet {label}.")
    if clicked.get(A.COPY):
        apply(attempt(lambda: feature.copy_costsheet(CostsheetActionRequest(costsheet_id=w.id))), "Đã sao chép.")
    if clicked.get(A.NEW_VERSION):
        apply(
            attempt(lambda: feature.new_version(CostsheetActionRequest(costsheet_id=w.id))),
            f"Đã tạo phiên bản {w.version + 1} của costsheet {w.costsheet_no}.",
        )
    if clicked.get(A.SAVE_OC):
        apply(
            attempt(lambda: feature.save_oc(SaveOcRequest(costsheet_id=w.id, oc_no=oc_no, close_order=False))),
            "Đã lưu OC.",
        )
    if clicked.get(A.SUBMIT):
        confirm_dialog(
            state, f"{key}.submit", "Gửi duyệt", f"Lưu các thay đổi và gửi duyệt costsheet {label}?", "Gửi duyệt",
            act(lambda _: feature.submit_costsheet(
                CostsheetActionRequest(costsheet_id=w.id, input=request() if w.editable else None)
            ), warnings=True),
        )  # fmt: skip
    if clicked.get(A.APPROVE):
        notes = [x.message for x in w.warnings if not x.blocking]
        confirm_dialog(
            state, f"{key}.approve", "Duyệt costsheet",
            f"Duyệt costsheet {label}? GP% {pct_text(w.result.gp_pct)}, OP% {pct_text(w.result.op_pct)}.", "Duyệt",
            act(lambda _: feature.approve_costsheet(CostsheetActionRequest(costsheet_id=w.id))), notes=notes,
        )  # fmt: skip
    if clicked.get(A.RETURN):
        confirm_dialog(
            state, f"{key}.return", "Trả lại costsheet", f"Trả lại costsheet {label} cho người lập?", "Trả lại",
            act(lambda reason: feature.return_costsheet(CostsheetActionRequest(costsheet_id=w.id, reason=reason))),
            reason_label="Lý do trả lại",
        )  # fmt: skip
    if clicked.get(A.CLOSE_ORDER):
        confirm_dialog(
            state, f"{key}.close", "Chốt đơn", f"Chốt đơn costsheet {label} với OC {oc_no or '(trống)'}?", "Chốt đơn",
            act(lambda _: feature.save_oc(SaveOcRequest(costsheet_id=w.id, oc_no=oc_no, close_order=True))),
        )  # fmt: skip
    if clicked.get(A.CANCEL):
        confirm_dialog(
            state, f"{key}.cancel", "Hủy costsheet",
            f"Hủy costsheet {label}? Phiếu đã hủy chỉ còn xem và sao chép.", "Hủy phiếu",
            act(lambda reason: feature.cancel_costsheet(CostsheetActionRequest(costsheet_id=w.id, reason=reason))),
            reason_label="Lý do hủy",
        )  # fmt: skip
    if clicked.get(A.PRINT_LABEL):
        tcfno = w.fabric.tcfno if w.fabric else w.input.tcfno
        label_dialog(feature, [tcfno], page.key(f"label.{w.id}"), fixed=True)
    if clicked.get(A.EDIT_FABRIC):
        override_dialog(page, feature, w)
    return any(clicked.values())
