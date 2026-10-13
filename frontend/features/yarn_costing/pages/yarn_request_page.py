"""Screen 2 (`yeu-cau-tinh-gia`) - Yêu cầu tính giá (UC-15..UC-17, UC-19, UC-40)."""

from datetime import date, timedelta

import streamlit as st

from backend.core.gateway import gateway
from backend.features.yarn_costing import YarnCostingController
from backend.features.yarn_costing.dto.common_dto import YarnStatus
from backend.features.yarn_costing.dto.reference_dto import GetReferenceDataRequest, ReferenceDataResponse
from backend.features.yarn_costing.dto.request_dto import (
    AnalyzeYarnNameRequest,
    CancelYarnRequestRequest,
    CheckRequestSubmitRequest,
    CreateYarnRequestRequest,
    ListYarnsRequest,
    UpdateYarnRequestRequest,
    YarnSummaryDTO,
)
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, panel
from frontend.features.yarn_costing.components.columns import YARN_SUMMARY_CONFIG, yarn_summary_rows
from frontend.features.yarn_costing.components.data_warnings import show_data_warnings
from frontend.features.yarn_costing.components.dialogs import confirm_dialog
from frontend.features.yarn_costing.components.display import count_text, yes_no
from frontend.features.yarn_costing.components.flash import set_flash, show_flash
from frontend.features.yarn_costing.components.labels import (
    ALL,
    SALES_ORIGIN,
    STATUS_LABELS,
    STATUS_ORDER,
    TECHNOLOGY_LABELS,
    all_or,
    factory_codes,
    factory_label,
    label_of,
)
from frontend.features.yarn_costing.components.permissions import action_state, explain


def packaging_choices(reference: ReferenceDataResponse, factory: str | None) -> dict[str, str]:
    """Loại đóng gói chọn được của xưởng (BR-52: đang dùng và có định mức): mã -> tên."""
    if not factory:
        return {}
    return {p.code: p.name for p in reference.packaging if str(p.factory_code) == str(factory) and p.selectable}


def default_packaging(reference: ReferenceDataResponse, factory: str | None) -> str | None:
    """BR-60: loại đóng gói mặc định của xưởng (điền sẵn nếu chọn được)."""
    for f in reference.factories:
        if factory and str(f.code) == str(factory):
            return f.default_packaging_code
    return None


class YarnRequestPage(BasePage):
    title = "Yêu cầu tính giá"
    menu_group = "Sales"
    icon = "📝"
    slug = "yeu-cau-tinh-gia"
    description = "Sales tạo, sửa, huỷ yêu cầu tính giá sợi mới và theo dõi trạng thái."

    def render(self) -> None:
        feature = gateway.open(YarnCostingController)
        reference = feature.get_reference_data(GetReferenceDataRequest(factory_code=None))
        show_data_warnings(reference)
        show_flash(self.state)

        self._create_form(feature, reference)
        items = self._request_list(feature, reference)
        picked = items["picked"]
        if picked:
            self._edit_block(feature, reference, picked)

    # ---- create ----
    def _create_form(self, feature: YarnCostingController, reference: ReferenceDataResponse) -> None:
        factories = reference.factories
        with panel("Tạo yêu cầu tính giá", icon="📝"):
            c1, c2, c3 = st.columns([1, 3, 2])
            factory = c1.selectbox(
                "Xưởng",
                factory_codes(factories),
                index=None,
                placeholder="Chọn xưởng",
                format_func=lambda c: factory_label(factories, c),
                key=self.key("new_factory"),
            )
            name = c2.text_input(
                "Tên sợi", max_chars=200, placeholder="Ví dụ: CVC 30/1 (60/40) MVS", key=self.key("new_name")
            )
            choices = packaging_choices(reference, factory)
            default_pack = default_packaging(reference, factory)
            options = list(choices)
            pack = c3.selectbox(
                "Loại đóng gói",
                options,
                index=options.index(default_pack) if default_pack in choices else None,
                placeholder="Chọn loại đóng gói",
                format_func=lambda c: f"{c} - {choices.get(c, '')}",
                disabled=not factory,
                key=self.key(f"new_pack.{factory}"),
            )
            if factory and name.strip():
                analysis = feature.analyze_yarn_name(AnalyzeYarnNameRequest(factory_code=factory, yarn_name=name))
                if analysis.valid:
                    st.markdown(
                        f"**App nhận ra:** Nhóm sợi **{analysis.yarn_group or '-'}** · "
                        f"Chi số **{count_text(analysis.count)}** · "
                        f"Công nghệ **{label_of(TECHNOLOGY_LABELS, analysis.technology)}** · "
                        f"Compact **{yes_no(analysis.is_compact)}** · "
                        f"Nhóm tiêu hao **{analysis.loss_group_key or '-'}**"
                    )
                    if not analysis.loss_group_exists:
                        st.warning(
                            f"Nhóm tiêu hao '{analysis.loss_group_key}' chưa có ở xưởng {factory}. Yêu cầu vẫn gửi "
                            "được; xưởng cần khai báo tiêu hao trước khi tính giá.",
                            icon="⚠️",
                        )
                if (not analysis.valid or analysis.duplicate_code) and analysis.message:
                    st.warning(analysis.message, icon="⚠️")
            # BR-63 / UC-42 + BR-47: lý do khoá nút hiện ngay cạnh nút
            check = feature.check_request_submit(CheckRequestSubmitRequest(factory_code=factory))
            no_role, no_role_why = action_state("UC-15", factory)
            reasons = [*([no_role_why] if no_role_why else []), *check.reasons]
            allowed = check.allowed and not no_role
            missing = not (factory and name.strip() and pack)
            button_col, reason_col = st.columns([1, 4], vertical_alignment="center")
            if button_col.button(
                "Gửi yêu cầu",
                type="primary",
                icon="📨",
                key=self.key("send"),
                disabled=not allowed or missing,
                help="Vui lòng chọn xưởng, nhập tên sợi và chọn loại đóng gói." if missing and allowed else None,
            ):
                result = feature.create_yarn_request(
                    CreateYarnRequestRequest(factory_code=factory, yarn_name=name, packaging_code=pack)
                )
                set_flash(self.state, result.message)
                st.session_state.pop(self.key("new_name"), None)
                st.rerun()
            with reason_col:
                explain(*reasons)

    # ---- list ----
    def _request_list(self, feature: YarnCostingController, reference: ReferenceDataResponse) -> dict:
        factories = reference.factories
        today = date.today()
        with panel("Bộ lọc", icon="🔎"):
            c1, c2, c3, c4, c5 = st.columns(5)
            factory = c1.selectbox(
                "Xưởng",
                [ALL, *factory_codes(factories)],
                format_func=lambda c: factory_label(factories, c),
                key=self.key("f_factory"),
            )
            statuses = c2.multiselect(
                "Trạng thái",
                STATUS_ORDER,
                default=[],
                format_func=lambda v: label_of(STATUS_LABELS, v),
                placeholder="Tất cả",
                key=self.key("f_statuses"),
            )
            date_from = c3.date_input(
                "Ngày tạo từ", value=today - timedelta(days=30), format="DD/MM/YYYY", key=self.key("f_from")
            )
            date_to = c4.date_input("Ngày tạo đến", value=today, format="DD/MM/YYYY", key=self.key("f_to"))
            keyword = c5.text_input("Từ khoá", placeholder="Mã hoặc tên sợi", key=self.key("f_keyword"))
        data = feature.list_yarns(
            ListYarnsRequest(
                factory_code=all_or(factory),
                statuses=statuses or None,
                date_from=date_from,
                date_to=date_to,
                keyword=keyword,
                origin=SALES_ORIGIN,
            )
        )
        items = sorted(data.items, key=lambda y: y.requested_at, reverse=True)
        names = {p.code: p.name for p in reference.packaging}
        with panel("Danh sách yêu cầu", icon="📋"):
            picked = data_table(
                yarn_summary_rows(items, names),
                column_config=YARN_SUMMARY_CONFIG,
                selection="single",
                key=self.key("requests"),
                empty_message="Chưa có yêu cầu nào.",
            )
        chosen = None
        if picked:
            code = picked[0]["Mã"]
            chosen = next((y for y in items if y.yarn_code == code), None)
        return {"picked": chosen}

    # ---- edit / cancel ----
    def _edit_block(
        self,
        feature: YarnCostingController,
        reference: ReferenceDataResponse,
        item: YarnSummaryDTO,
    ) -> None:
        code = item.yarn_code
        waiting = item.status == YarnStatus.CHO_XUONG_XEM
        with panel(f"Yêu cầu {code}", icon="✏️"):
            if not waiting:
                st.info(
                    f"Chỉ sửa hoặc huỷ được yêu cầu đang 'Chờ xưởng xem'. Yêu cầu {code} đang ở trạng thái "
                    f"'{label_of(STATUS_LABELS, item.status)}'."
                )
            c1, c2 = st.columns([3, 2])
            name = c1.text_input("Tên sợi", value=item.yarn_name, max_chars=200, key=self.key(f"edit_name.{code}"))
            choices = packaging_choices(reference, str(item.factory_code))
            if item.packaging_code and item.packaging_code not in choices:
                choices = {item.packaging_code: item.packaging_code, **choices}
            options = list(choices)
            pack = c2.selectbox(
                "Loại đóng gói",
                options,
                index=options.index(item.packaging_code) if item.packaging_code in options else None,
                placeholder="Chọn loại đóng gói",
                format_func=lambda c: f"{c} - {choices.get(c, '')}" if choices.get(c, c) != c else c,
                key=self.key(f"edit_pack.{code}"),
            )
            st.caption("Không đổi được xưởng; muốn đổi xưởng hãy huỷ và tạo yêu cầu mới.")
            save_disabled, save_why = action_state("UC-16")
            cancel_disabled, cancel_why = action_state("UC-17")
            left, right, _ = st.columns([1, 1, 3])
            if left.button(
                "Lưu sửa đổi",
                type="primary",
                key=self.key("edit_save"),
                disabled=save_disabled or not waiting,
                help=save_why,
            ):
                result = feature.update_yarn_request(
                    UpdateYarnRequestRequest(yarn_code=code, yarn_name=name, packaging_code=pack or "")
                )
                set_flash(self.state, result.message)
                st.rerun()
            if right.button(
                "Huỷ yêu cầu",
                icon="🚫",
                key=self.key("edit_cancel"),
                disabled=cancel_disabled or not waiting,
                help=cancel_why,
            ):
                confirm_dialog(
                    self.state,
                    self.key(f"dlg.cancel.{code}"),
                    "Xác nhận huỷ yêu cầu",
                    f"Huỷ yêu cầu {code} - {item.yarn_name}? Mã {code} sẽ không được dùng lại.",
                    "Huỷ yêu cầu",
                    lambda: feature.cancel_yarn_request(CancelYarnRequestRequest(yarn_code=code)).message,
                )
            explain(save_why, cancel_why)
