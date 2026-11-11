"""Screen 2 (`yeu-cau-tinh-gia`) - Yêu cầu tính giá (UC-15..UC-17, UC-19, UC-40; UC-49, UC-50 bổ sung 2026-11-10)."""

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
from backend.features.yarn_costing.dto.sales_dto import (
    SuggestYarnsRequest,
    UseExistingYarnRequest,
    YarnSuggestionDTO,
)
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, panel
from frontend.features.yarn_costing.components.columns import YARN_SUMMARY_CONFIG, yarn_summary_rows
from frontend.features.yarn_costing.components.data_warnings import show_data_warnings
from frontend.features.yarn_costing.components.dialogs import confirm_dialog
from frontend.features.yarn_costing.components.display import count_text, usd, vnd, yes_no
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
from frontend.features.yarn_costing.components.name_input import name_input
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
        self._used_lines()
        items = self._request_list(feature, reference)
        picked = items["picked"]
        if picked:
            self._edit_block(feature, reference, picked)

    # ---- create ----
    def _create_form(self, feature: YarnCostingController, reference: ReferenceDataResponse) -> None:
        factories = reference.factories
        with panel("Tạo yêu cầu tính giá", icon="📝"):
            c1, c_customer, c3 = st.columns([1, 2, 2])
            factory = c1.selectbox(
                "Xưởng",
                factory_codes(factories),
                index=None,
                placeholder="Chọn xưởng",
                format_func=lambda c: factory_label(factories, c),
                key=self.key("new_factory"),
            )
            customer = c_customer.text_input(
                "Khách hàng", max_chars=100, placeholder="Không bắt buộc", key=self.key("new_customer")
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
            # BR-101 / BR-102 (bổ sung 2026-11-11): ô ghép tên / gõ tay + chữ lạ
            name, name_mode, word_reason, name_check = name_input(feature, self.key("new_name"))
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
            same_here = self._suggestions(feature, factory, name, customer)
            reason = ""
            if same_here:  # BR-78
                reason = st.text_area(
                    "Lý do gửi yêu cầu mới",
                    max_chars=500,
                    placeholder=f"Đã có sợi trùng ở xưởng {factory}: {', '.join(same_here[:3])}. "
                    "Ghi lý do vẫn gửi yêu cầu mới.",
                    key=self.key(f"new_reason.{factory}"),
                )
            # BR-63 / UC-42 + BR-47: lý do khoá nút hiện ngay cạnh nút
            check = feature.check_request_submit(CheckRequestSubmitRequest(factory_code=factory))
            no_role, no_role_why = action_state("UC-15", factory)
            reasons = [*([no_role_why] if no_role_why else []), *check.reasons]
            allowed = check.allowed and not no_role
            missing = not (factory and name.strip() and pack) or bool(name_check and name_check.problem)
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
                    CreateYarnRequestRequest(
                        factory_code=factory,
                        yarn_name=name,
                        packaging_code=pack,
                        customer_name=customer,
                        duplicate_reason=reason,
                        unknown_word_reason=word_reason,
                        name_mode=name_mode,
                    )
                )
                set_flash(self.state, result.message)
                for widget in [k for k in st.session_state if str(k).startswith(self.key("new_name"))]:
                    st.session_state.pop(widget, None)
                st.session_state.pop(self.key("new_customer"), None)
                st.rerun()
            with reason_col:
                explain(*reasons)

    # ---- UC-49 / UC-50 ----
    def _suggestions(self, feature: YarnCostingController, factory: str | None, name: str, customer: str) -> list[str]:
        """Show the Trùng / Gần giống tables under the form; return the Trùng codes of the chosen factory (BR-78)."""
        if not name.strip():
            return []
        data = feature.suggest_similar_yarns(SuggestYarnsRequest(yarn_name=name, factory_code=factory))
        if data.blend_text:
            st.markdown(f"**App đọc được:** {data.blend_text}")
        if data.message:
            st.caption(data.message)
        picked: YarnSuggestionDTO | None = None
        for title, items, key in (
            (f"Sợi trùng ({len(data.same)})", data.same, "same"),
            (f"Sợi gần giống ({len(data.near)})", data.near, "near"),
        ):
            if not items:
                continue
            st.markdown(f"**{title}**")
            rows = [
                {
                    "Xưởng": str(s.factory_code),
                    "Mã": s.yarn_code,
                    "Tên chuẩn": s.yarn_name,
                    "Tên theo khách": s.customer_names_text,
                    ("Khác ở đâu" if key == "near" else "Ghi chú"): s.note,
                    "Trạng thái": s.status.value,
                    "Tổng (VND/kg)": vnd(s.total_vnd),
                    "USD/kg": usd(s.usd_per_kg),
                    "Mã kế toán": s.accounting_code,
                }
                for s in items
            ]
            chosen = data_table(rows, selection="single", key=self.key(f"suggest.{key}"))
            if chosen:
                picked = next((s for s in items if s.yarn_code == chosen[0]["Mã"]), picked)
        if data.same or data.near:
            disabled, why = action_state("UC-50")
            if st.button(
                "Dùng sợi này",
                icon="✅",
                key=self.key("use_existing"),
                disabled=disabled or picked is None,
                help=why or ("Chọn một dòng trong bảng gợi ý." if picked is None else None),
            ):
                assert picked is not None
                result = feature.use_existing_yarn(
                    UseExistingYarnRequest(yarn_code=picked.yarn_code, typed_name=name, customer_name=customer)
                )
                self.state.set("request_used", result.model_dump(mode="json"))
                set_flash(self.state, result.message)
                for k in ("new_name", "new_customer"):
                    st.session_state.pop(self.key(k), None)
                st.rerun()
            explain(why)
        return data.same_in_factory

    def _used_lines(self) -> None:
        """UC-50 output: the price lines of the yarn chosen with "Dùng sợi này"."""
        used = self.state.get("request_used")
        if not used:
            return
        with panel(f"Dòng giá của sợi {used['yarn_code']} - {used['yarn_name']}", icon="💰"):
            data_table(
                [
                    {
                        "Mã dòng": line["line_code"],
                        "Loại dòng": str(line["line_type"]),
                        "Tổng (VND/kg)": vnd(line["total_vnd"]),
                        "USD/kg": usd(line["usd_per_kg"]),
                        "Mã kế toán": line["accounting_code"],
                    }
                    for line in used["lines"]
                ],
                key=self.key("used_lines"),
                empty_message="Sợi chưa có dòng giá.",
            )
            if st.button("Đóng", key=self.key("used_close")):
                self.state.pop("request_used")
                st.rerun()

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
            with c1:  # BR-101 (bổ sung 2026-11-11): gõ tay + kiểm tra chữ lạ
                name, name_mode, word_reason, _ = name_input(
                    feature, self.key(f"edit_name.{code}"), initial=item.yarn_name, allow_builder=False
                )
            customer = c1.text_input(
                "Khách hàng", value=item.customer_name, max_chars=100, key=self.key(f"edit_customer.{code}")
            )
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
                    UpdateYarnRequestRequest(
                        yarn_code=code,
                        yarn_name=name,
                        packaging_code=pack or "",
                        customer_name=customer,
                        unknown_word_reason=word_reason,
                        name_mode=name_mode,
                    )
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
