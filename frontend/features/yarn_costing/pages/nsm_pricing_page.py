"""Screen 3 (`nhap-nsm-tinh-gia`) - Nhập NSM & tính giá (UC-18..UC-24)."""

from typing import Any

import streamlit as st

from backend.core.gateway import gateway
from backend.features.yarn_costing import YarnCostingController
from backend.features.yarn_costing.dto.common_dto import ActorDTO, NsmMode, YarnStatus
from backend.features.yarn_costing.dto.pricing_dto import (
    CorrectYarnNsmRequest,
    CreateNsmRevisionRequest,
    GetYarnDetailRequest,
    PricingResultResponse,
    SaveYarnNsmRequest,
    SuggestNsmRequest,
    YarnComponentDTO,
    YarnDetailResponse,
)
from backend.features.yarn_costing.dto.reference_dto import GetReferenceDataRequest
from backend.features.yarn_costing.dto.request_dto import (
    AnalyzeYarnNameRequest,
    ListYarnsRequest,
    RejectYarnRequestRequest,
)
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, editable_table, panel, stat_row
from frontend.core.formatting import format_number
from frontend.features.yarn_costing.components.actor_block import actor_factory, render_actor_block
from frontend.features.yarn_costing.components.columns import (
    COMPONENT_CONFIG,
    NO_CARDING,
    STAGE_COST_CONFIG,
    YARN_SUMMARY_CONFIG,
    component_rows,
    stage_cost_rows,
    yarn_summary_rows,
)
from frontend.features.yarn_costing.components.data_warnings import show_data_warnings
from frontend.features.yarn_costing.components.dialogs import confirm_dialog
from frontend.features.yarn_costing.components.display import (
    count_text,
    from_percent,
    optional_decimal,
    pct,
    plain,
    text_or_dash,
    to_decimal,
    usd,
    vnd,
    yes_no,
)
from frontend.features.yarn_costing.components.factory_picker import factory_segment
from frontend.features.yarn_costing.components.flash import set_flash, show_flash
from frontend.features.yarn_costing.components.labels import (
    FINAL_STATUSES,
    NSM_MODE_LABELS,
    STATUS_LABELS,
    STATUS_ORDER,
    TECHNOLOGY_LABELS,
    factory_codes,
    label_of,
)
from frontend.features.yarn_costing.components.permissions import action_state, explain
from frontend.features.yarn_costing.pages.loss_group_page import LOSS_PREFILL_KEY, LossGroupPage

OPEN_YARN_KEY = "open_yarn"
OPEN_CODE_KEY = "nsm_open_code"
LAST_PICK_KEY = "nsm_last_pick"
LIST_COLUMNS = [
    "Mã",
    "Tên sợi",
    "Loại đóng gói",
    "Trạng thái",
    "Người tạo",
    "Ngày tạo",
    "Lý do từ chối / chưa tính được",
    "Tổng (VND/kg)",
]
MATERIAL_COL = "Nguyên liệu"
RATIO_COL = "Tỷ lệ %"
LINE_COL = "Dây chuyền"
PASS_COL = "Lượt"
CARDING_NSM_COL = "NSM chải thô"
NSM_COL = "NSM (kg/giờ)"
REF_COL = "NSM sợi so sánh"
COMPONENT_COLUMNS = [MATERIAL_COL, RATIO_COL, LINE_COL, PASS_COL, CARDING_NSM_COL, REF_COL]
EDITABLE_STATUSES = (YarnStatus.CHO_XUONG_XEM, YarnStatus.CHUA_TINH_DUOC)


class NsmPricingPage(BasePage):
    title = "Nhập NSM & tính giá"
    menu_group = "Xưởng sợi"
    icon = "🧮"
    slug = "nhap-nsm-tinh-gia"
    description = (
        "Xưởng xử lý yêu cầu: nhập năng suất máy và tỷ lệ pha, kiểm tra, xem và lưu giá, tạo bản ĐCNSM hoặc từ chối."
    )

    def render(self) -> None:
        feature = gateway.open(YarnCostingController)
        reference = feature.get_reference_data(GetReferenceDataRequest(factory_code=None))
        show_data_warnings(reference)
        codes = factory_codes(reference.factories)
        pending = self.state.pop(OPEN_YARN_KEY)
        if pending and pending.get("factory_code") in codes:
            st.session_state[self.key("factory")] = pending["factory_code"]
            self.state.set(OPEN_CODE_KEY, pending["yarn_code"])

        actor = render_actor_block(feature, self.state, reference)
        show_flash(self.state)
        if not codes:
            return

        factory = factory_segment(reference.factories, self.key("factory"), actor_factory(self.state)) or codes[0]
        tiles = st.container()
        with panel("Bộ lọc", icon="🔎"):
            c1, c2 = st.columns([3, 2])
            statuses = c1.multiselect(
                "Trạng thái",
                STATUS_ORDER,
                default=list(EDITABLE_STATUSES),
                format_func=lambda v: label_of(STATUS_LABELS, v),
                placeholder="Tất cả",
                key=self.key(f"statuses.{factory}"),
            )
            keyword = c2.text_input("Từ khoá", placeholder="Mã hoặc tên sợi", key=self.key(f"keyword.{factory}"))
        data = feature.list_yarns(
            ListYarnsRequest(factory_code=factory, statuses=statuses or None, keyword=keyword, oldest_first=True)
        )
        with tiles:
            stat_row(
                [(label_of(STATUS_LABELS, s), format_number(data.status_counts.get(str(s), 0))) for s in STATUS_ORDER]
            )
        items = sorted(data.items, key=lambda y: y.requested_at)
        names = {p.code: p.name for p in reference.packaging}
        with panel("Mã cần xử lý", icon="📋"):
            picked = data_table(
                yarn_summary_rows(items, names),
                column_config=YARN_SUMMARY_CONFIG,
                column_order=LIST_COLUMNS,
                selection="single",
                key=self.key(f"yarns.{factory}"),
                empty_message="Không có mã nào cần xử lý.",
            )
        picked_code = str(picked[0]["Mã"]) if picked else None
        if picked_code != self.state.get(LAST_PICK_KEY):
            self.state.set(LAST_PICK_KEY, picked_code)
            if picked_code:
                self.state.set(OPEN_CODE_KEY, picked_code)
        code = self.state.get(OPEN_CODE_KEY)
        if not code:
            return
        detail = feature.get_yarn_detail(GetYarnDetailRequest(yarn_code=code, line_code=None))
        if str(detail.yarn.factory_code) != str(factory):
            self.state.pop(OPEN_CODE_KEY)
            return
        self._open_yarn(feature, actor, detail)

    # ---- the open yarn ----
    def _open_yarn(self, feature: YarnCostingController, actor: ActorDTO | None, detail: YarnDetailResponse) -> None:
        y = detail.yarn
        code = y.yarn_code
        factory = str(y.factory_code)
        mode = self.state.get(f"mode.{code}", "edit")
        ver = self.state.get(f"ver.{code}", 0)
        prefill: dict[str, Any] | None = self.state.get(f"prefill.{code}")
        result: PricingResultResponse | None = self.state.get(f"result.{code}")

        with panel(f"Mã đang mở: {y.yarn_code} - {y.yarn_name}", icon="🧵"):
            facts = [
                ("Tên sợi", y.yarn_name),
                ("Nhóm sợi", text_or_dash(y.yarn_group)),
                ("Chi số", count_text(y.count)),
                ("Công nghệ", label_of(TECHNOLOGY_LABELS, y.technology)),
                ("Nhóm tiêu hao", text_or_dash(y.loss_group_key)),
                ("Đóng gói", text_or_dash(f"{y.packaging_code} - {y.packaging_name}" if y.packaging_code else "")),
                ("Trạng thái", label_of(STATUS_LABELS, y.status)),
                ("Khoá", yes_no(y.is_locked)),
                ("Sợi so sánh", text_or_dash(y.reference_yarn_code)),
            ]
            columns = st.columns(3)
            for index, (label, value) in enumerate(facts):
                columns[index % 3].markdown(f"**{label}:** {value}")
            if y.status_reasons:
                st.warning("\n".join(f"- {reason}" for reason in y.status_reasons), icon="⚠️")
            if st.button("Đóng mã", type="tertiary", key=self.key("close")):
                self.state.pop(OPEN_CODE_KEY)
                st.rerun()
            if y.status in FINAL_STATUSES:
                st.info(f"Mã {y.yarn_code} ở trạng thái '{label_of(STATUS_LABELS, y.status)}' - không nhập NSM được.")
                return
            if mode == "edit" and y.is_locked:
                st.warning(self._locked_message(code), icon="🔒")
            if mode == "revision":
                st.info(f"Đang tạo bản ĐCNSM từ {y.yarn_code}. Bản gốc giữ nguyên.")
                if st.button("Quay lại sửa bản đang mở", type="tertiary", key=self.key(f"back.{code}")):
                    self.state.set(f"mode.{code}", "edit")
                    self.state.pop(f"result.{code}")
                    st.rerun()

            nsm_mode = NsmMode.TU_NHAP
            if mode == "edit":
                nsm_mode = self._nsm_mode(feature, code, factory, ver) or NsmMode.TU_NHAP
            if prefill:
                st.caption(
                    f"Sợi so sánh: {prefill.get('reference_yarn_code')} - {prefill.get('reference_yarn_name')} "
                    f"(chi số {count_text(prefill.get('reference_count'))})"
                )

            components = self._components_grid(detail, mode, ver, prefill)
            rows = self._nsm_grid(detail, mode, ver, prefill)
            nsm = {str(row["Công đoạn"]): to_decimal(row.get(NSM_COL)) for row in rows}

            warn_reason = y.nsm_warning_reason
            if (result and result.warning_stages) or y.nsm_warning_reason:
                warn_reason = st.text_area(
                    "Lý do khác sợi cùng nhóm",
                    value=y.nsm_warning_reason or "",
                    max_chars=500,
                    key=self.key(f"warn_reason.{code}.{mode}"),
                )
            adjust_reason = ""
            if mode == "revision":
                adjust_reason = st.text_area("Lý do điều chỉnh", max_chars=500, key=self.key(f"adjust_reason.{code}"))

            if mode == "edit":
                ref_code = prefill.get("reference_yarn_code") if prefill else y.reference_yarn_code
                self._edit_buttons(feature, actor, detail, components, nsm, nsm_mode, ref_code, warn_reason)
            else:
                self._revision_buttons(feature, actor, detail, components, nsm, adjust_reason, warn_reason)

        if result is not None:
            self._result_block(code, result)

    @staticmethod
    def _locked_message(code: str) -> str:
        return f"Mã {code} đã có mã kế toán nên không sửa được. Muốn điều chỉnh NSM, hãy tạo bản ĐCNSM."

    def _nsm_mode(self, feature: YarnCostingController, code: str, factory: str, ver: int) -> NsmMode | None:
        left, right = st.columns([2, 2], vertical_alignment="bottom")
        nsm_mode = left.segmented_control(
            "Cách nhập",
            [NsmMode.TU_NHAP, NsmMode.TU_DIEN],
            default=NsmMode.TU_NHAP,
            required=True,
            format_func=lambda v: label_of(NSM_MODE_LABELS, v),
            key=self.key(f"nsm_mode.{code}"),
        )
        if nsm_mode == NsmMode.TU_DIEN:
            disabled, why = action_state(self.state, "UC-20", factory)
            if right.button(
                "Lấy NSM từ sợi cùng nhóm", icon="🪄", key=self.key(f"suggest.{code}"), disabled=disabled, help=why
            ):
                suggestion = feature.suggest_nsm(SuggestNsmRequest(yarn_code=code))
                if suggestion.found:
                    self.state.set(f"prefill.{code}", suggestion.model_dump())
                    self.state.pop(f"checked.{code}.edit")
                    self.state.set(f"ver.{code}", ver + 1)
                    set_flash(
                        self.state,
                        suggestion.message
                        or f"Đã điền NSM từ {suggestion.reference_yarn_code} - {suggestion.reference_yarn_name}.",
                    )
                    st.rerun()
                st.warning(suggestion.message or "Chưa có sợi cùng nhóm để tự điền. Vui lòng nhập NSM.", icon="⚠️")
            explain(why)
        return nsm_mode

    def _component_source(
        self, detail: YarnDetailResponse, mode: str, prefill: dict[str, Any] | None
    ) -> list[YarnComponentDTO]:
        """Last checked components (with Lượt) > auto-filled components > the yarn's own components."""
        code = detail.yarn.yarn_code
        checked = self.state.get(f"checked.{code}.{mode}")
        if checked is not None:
            return [YarnComponentDTO.model_validate(c) for c in checked]
        if prefill and prefill.get("components"):
            return [YarnComponentDTO.model_validate(c) for c in prefill["components"]]
        return list(detail.components)

    def _components_grid(
        self, detail: YarnDetailResponse, mode: str, ver: int, prefill: dict[str, Any] | None
    ) -> list[YarnComponentDTO]:
        """Table 1 (4.12.1): material, ratio, carding line, carding NSM; Lượt is numbered by the app."""
        code = detail.yarn.yarn_code
        cver = self.state.get(f"cver.{code}", 0)
        source = self._component_source(detail, mode, prefill)
        rows = [
            {
                MATERIAL_COL: c.material_label,
                RATIO_COL: pct(c.ratio),
                LINE_COL: c.carding_stage or NO_CARDING,
                PASS_COL: c.pass_no,
                CARDING_NSM_COL: plain(c.nsm_carding),
                REF_COL: plain(c.reference_nsm),
            }
            for c in source
        ]
        lines = list(dict.fromkeys([*detail.carding_stages, NO_CARDING, *(r[LINE_COL] for r in rows)]))
        if detail.material_options:
            used = [r[MATERIAL_COL] for r in rows if r[MATERIAL_COL]]
            materials = list(dict.fromkeys([*detail.material_options, *used]))
            material_col = st.column_config.SelectboxColumn(MATERIAL_COL, options=materials, required=True)
        else:
            material_col = st.column_config.TextColumn(MATERIAL_COL, max_chars=200, required=True)
        st.markdown("**① Thành phần nguyên liệu**")
        edited = editable_table(
            rows,
            key=self.key(f"comp_grid.{code}.{mode}.{ver}.{cver}"),
            columns=COMPONENT_COLUMNS,
            disabled=[PASS_COL, REF_COL],
            allow_add_delete=True,
            column_config={
                MATERIAL_COL: material_col,
                RATIO_COL: st.column_config.NumberColumn(
                    RATIO_COL, min_value=0.0, max_value=100.0, step=0.01, format="%.2f"
                ),
                LINE_COL: st.column_config.SelectboxColumn(LINE_COL, options=lines, default=NO_CARDING),
                PASS_COL: st.column_config.NumberColumn(PASS_COL, format="%d"),
                CARDING_NSM_COL: st.column_config.NumberColumn(
                    CARDING_NSM_COL, min_value=0.0, step=0.1, format="localized"
                ),
                REF_COL: st.column_config.NumberColumn(REF_COL, format="localized"),
            },
        )
        st.caption(
            "Tỷ lệ % các nguyên liệu cộng lại bằng 100. Cột Lượt do app tự đánh sau khi bấm "
            "'Kiểm tra và xem giá'. Để trống NSM chải thô khi chọn 'Không chải thô'."
        )
        components = []
        for row in edited:
            label = str(row.get(MATERIAL_COL) or "").strip()
            ratio = row.get(RATIO_COL)
            if not label and ratio in (None, ""):
                continue
            line = str(row.get(LINE_COL) or "").strip()
            line = "" if line == NO_CARDING else line
            components.append(
                YarnComponentDTO(
                    material_label=label,
                    ratio=None if ratio in (None, "") else from_percent(ratio),
                    carding_stage=line,
                    nsm_carding=optional_decimal(row.get(CARDING_NSM_COL)) if line else None,
                )
            )
        st.markdown("**② NSM các công đoạn khác**")
        return components

    def _nsm_grid(
        self, detail: YarnDetailResponse, mode: str, ver: int, prefill: dict[str, Any] | None
    ) -> list[dict[str, Any]]:
        code = detail.yarn.yarn_code
        prefill_nsm = (prefill or {}).get("nsm") or {}
        rows = [
            {
                "Công đoạn": stage.stage_code,
                "Tên công đoạn": stage.stage_name,
                NSM_COL: plain(prefill_nsm.get(stage.stage_code) if prefill else stage.nsm),
                REF_COL: plain(prefill_nsm.get(stage.stage_code) if prefill else stage.reference_nsm),
            }
            for stage in detail.stages
        ]
        edited = editable_table(
            rows,
            key=self.key(f"nsm_grid.{code}.{mode}.{ver}"),
            columns=["Công đoạn", "Tên công đoạn", NSM_COL, REF_COL],
            disabled=["Công đoạn", "Tên công đoạn", REF_COL],
            column_config={
                NSM_COL: st.column_config.NumberColumn(NSM_COL, min_value=0.0, step=0.1, format="localized"),
                REF_COL: st.column_config.NumberColumn(REF_COL, format="localized"),
            },
        )
        st.caption(
            "Để trống hoặc 0 = sợi không chạy công đoạn đó. Công đoạn đóng gói F luôn được tính theo loại đóng gói."
        )
        return edited

    def _edit_buttons(
        self,
        feature: YarnCostingController,
        actor: ActorDTO | None,
        detail: YarnDetailResponse,
        components: list[YarnComponentDTO],
        nsm: dict[str, Any],
        nsm_mode: NsmMode,
        ref_code: str | None,
        warn_reason: str,
    ) -> None:
        y = detail.yarn
        code = y.yarn_code
        factory = str(y.factory_code)
        correcting = y.status not in EDITABLE_STATUSES
        uc = "UC-23" if correcting else "UC-21"
        disabled, why = action_state(self.state, uc, factory)
        if y.is_locked:
            disabled, why = True, self._locked_message(code)
        request_cls = CorrectYarnNsmRequest if correcting else SaveYarnNsmRequest
        method = feature.correct_yarn_nsm if correcting else feature.save_yarn_nsm

        def build(save: bool) -> SaveYarnNsmRequest:
            return request_cls(
                actor=actor,
                yarn_code=code,
                components=components,
                nsm=nsm,
                nsm_mode=nsm_mode,
                reference_yarn_code=ref_code,
                nsm_warning_reason=warn_reason or "",
                save=save,
            )

        reasons: list[str | None] = [why]
        b1, b2, b3, b4 = st.columns(4)
        if b1.button("Kiểm tra và xem giá", icon="🔍", key=self.key(f"check.{code}"), disabled=disabled, help=why):
            self._keep_result(code, "edit", method(build(False)))
            st.rerun()
        if b2.button(
            "Lưu NSM và giá", type="primary", icon="💾", key=self.key(f"save.{code}"), disabled=disabled, help=why
        ):
            self._after_save(code, "edit", method(build(True)))
        if detail.lines:
            rev_disabled, rev_why = action_state(self.state, "UC-24", factory)
            reasons.append(rev_why)
            if b3.button(
                "Tạo bản ĐCNSM", icon="🧬", key=self.key(f"revision.{code}"), disabled=rev_disabled, help=rev_why
            ):
                self.state.set(f"mode.{code}", "revision")
                self.state.pop(f"result.{code}")
                st.rerun()
        analysis = feature.analyze_yarn_name(AnalyzeYarnNameRequest(factory_code=factory, yarn_name=y.yarn_name))
        missing_loss_group = analysis.valid and not analysis.loss_group_exists
        if missing_loss_group and b4.button("Khai báo tiêu hao cho nhóm này", icon="📉", key=self.key(f"loss.{code}")):
            self.state.set(
                LOSS_PREFILL_KEY,
                {
                    "factory_code": factory,
                    "group_label": analysis.loss_group_key or y.loss_group_key,
                    "technology": analysis.technology or y.technology,
                },
            )
            self.go_to(LossGroupPage)

        if y.status == YarnStatus.CHO_XUONG_XEM:
            rej_disabled, rej_why = action_state(self.state, "UC-18", factory)
            reasons.append(rej_why)
            left, right = st.columns([4, 1], vertical_alignment="bottom")
            reason = left.text_input("Lý do từ chối", max_chars=500, key=self.key(f"reject_reason.{code}"))
            if right.button(
                "Từ chối",
                icon="⛔",
                key=self.key(f"reject.{code}"),
                disabled=rej_disabled or not reason.strip(),
                help=rej_why or ("Vui lòng nhập lý do từ chối." if not reason.strip() else None),
            ):
                confirm_dialog(
                    self.state,
                    self.key(f"dlg.reject.{code}"),
                    "Xác nhận từ chối yêu cầu",
                    f"Từ chối yêu cầu {code} - {y.yarn_name}? Sales sẽ thấy lý do bạn nhập.",
                    "Từ chối",
                    lambda: (
                        feature.reject_yarn_request(
                            RejectYarnRequestRequest(actor=actor, yarn_code=code, reason=reason)
                        ).message
                    ),
                )
        explain(*reasons)

    def _revision_buttons(
        self,
        feature: YarnCostingController,
        actor: ActorDTO | None,
        detail: YarnDetailResponse,
        components: list[YarnComponentDTO],
        nsm: dict[str, Any],
        adjust_reason: str,
        warn_reason: str,
    ) -> None:
        y = detail.yarn
        code = y.yarn_code
        disabled, why = action_state(self.state, "UC-24", str(y.factory_code))

        def build(save: bool) -> CreateNsmRevisionRequest:
            return CreateNsmRevisionRequest(
                actor=actor,
                source_yarn_code=code,
                adjust_reason=adjust_reason,
                components=components,
                nsm=nsm,
                nsm_warning_reason=warn_reason or "",
                save=save,
            )

        b1, b2, _ = st.columns([1, 1, 2])
        if b1.button("Kiểm tra và xem giá", icon="🔍", key=self.key(f"rev_check.{code}"), disabled=disabled, help=why):
            self._keep_result(code, "revision", feature.create_nsm_revision(build(False)))
            st.rerun()
        if b2.button(
            "Lưu bản ĐCNSM", type="primary", icon="💾", key=self.key(f"rev_save.{code}"), disabled=disabled, help=why
        ):
            response = feature.create_nsm_revision(build(True))
            if response.saved:
                set_flash(self.state, response.message)
                self.state.pop(f"checked.{code}.revision")
                self.state.set(f"mode.{code}", "edit")
                self.state.pop(f"result.{code}")
                new_code = response.yarn.yarn_code
                self.state.set(f"result.{new_code}", response)
                self.state.set(OPEN_CODE_KEY, new_code)
                st.rerun()
            self._keep_result(code, "revision", response)
            self.state.set(f"warn.{code}", response.message)
            st.rerun()
        explain(why)

    def _keep_result(self, code: str, mode: str, response: PricingResultResponse) -> None:
        """Keep the result and show the checked components (with the app's Lượt) in table 1."""
        self.state.set(f"result.{code}", response)
        if response.components:
            self.state.set(f"checked.{code}.{mode}", [c.model_dump() for c in response.components])
            self.state.set(f"cver.{code}", self.state.get(f"cver.{code}", 0) + 1)

    def _after_save(self, code: str, mode: str, response: PricingResultResponse) -> None:
        self._keep_result(code, mode, response)
        if response.saved:
            self.state.pop(f"checked.{code}.{mode}")
            set_flash(self.state, response.message)
        else:
            self.state.set(f"warn.{code}", response.message)
        st.rerun()

    # ---- result ----
    def _result_block(self, code: str, result: PricingResultResponse) -> None:
        with panel("Kết quả tính giá", icon="📊"):
            warning = self.state.pop(f"warn.{code}")
            if warning:
                st.warning(warning, icon="⚠️")
            if result.check_passed:
                st.success("Kiểm tra khớp: đạt.")
            else:
                st.warning("Kiểm tra khớp: chưa đạt.\n" + "\n".join(f"- {reason}" for reason in result.reasons))
            if result.warning_stages:
                st.warning(
                    f"NSM khác sợi cùng nhóm ({result.reference_yarn_code or '-'}) ở công đoạn: "
                    f"{', '.join(result.warning_stages)}. Vui lòng nhập lý do trước khi lưu."
                )
            if result.components:
                st.markdown("**Thành phần nguyên liệu (Lượt do app đánh)**")
                data_table(
                    component_rows(result.components),
                    column_config=COMPONENT_CONFIG,
                    key=self.key(f"res_components.{code}"),
                )
            data_table(
                stage_cost_rows(result.stage_details),
                column_config=STAGE_COST_CONFIG,
                empty_message="Chưa có chi tiết tính giá.",
                key=self.key(f"res_stages.{code}"),
            )
            line = result.line
            if line is not None:
                stat_row(
                    [
                        ("Nhân công", format_number(vnd(line.labor))),
                        ("Khấu hao", format_number(vnd(line.depreciation))),
                        ("Điện", format_number(vnd(line.electricity))),
                        ("Vật tư", format_number(vnd(line.materials))),
                        ("CPQL", format_number(vnd(line.overhead))),
                    ]
                )
                trial = result.trial_line
                stat_row(
                    [
                        ("Tổng (VND/kg)", format_number(vnd(line.total_vnd))),
                        ("USD/kg", format_number(usd(line.usd_per_kg), 4)),
                        ("Giá thí nghiệm (VND/kg)", format_number(vnd(trial.total_vnd)) if trial else "-"),
                    ]
                )
                st.caption("Kết quả hiển thị đã làm tròn; Tổng được cộng từ các số chưa làm tròn.")
