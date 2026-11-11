"""Screen 14 (`kiem-tra-ten-soi`) - Kiểm tra tên sợi (UC-65..UC-71, bổ sung 2026-11-11)."""

from typing import Any

import streamlit as st

from backend.core.gateway import gateway
from backend.features.yarn_costing import YarnCostingController
from backend.features.yarn_costing.dto.name_dto import (
    ExportRenameListRequest,
    GetNameCheckRequest,
    ImportRenameFileRequest,
    NameCheckResponse,
    NameIssueKind,
    NamePartDTO,
    NamePartKind,
    NamePartSource,
    NameWordDTO,
    NameWordKind,
    NormalizeNamesRequest,
    NormalizeNamesResponse,
    PendingWordStatus,
    RenameImportResponse,
    RenameYarnRequest,
    ResolvePendingWordRequest,
    SaveNameDictionaryRequest,
    SaveNamePartsRequest,
)
from backend.features.yarn_costing.dto.reference_dto import GetReferenceDataRequest
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, editable_table, file_upload, panel, stat_row
from frontend.core.formatting import format_number
from frontend.features.yarn_costing.components.columns import count_col, datetime_col
from frontend.features.yarn_costing.components.dialogs import confirm_dialog
from frontend.features.yarn_costing.components.flash import show_flash
from frontend.features.yarn_costing.components.labels import factory_codes, factory_label
from frontend.features.yarn_costing.components.actions import run_save, try_call
from frontend.features.yarn_costing.components.name_input import name_input
from frontend.features.yarn_costing.components.permissions import action_state, explain

BOTH = "Cả hai"
DEFAULT_ISSUES = [k for k in NameIssueKind if k != NameIssueKind.CHU_THUONG]
KINDS = [k.value for k in NameWordKind]
FILE_KEY = "rename_file_preview"
NORMALIZE_KEY = "normalize_preview"


class NameCheckPage(BasePage):
    title = "Kiểm tra tên sợi"
    menu_group = "Phòng SO"
    icon = "🔤"
    slug = "kiem-tra-ten-soi"
    description = (
        "Rà tên sợi sai chính tả / thiếu ngoặc / trùng tên, đổi tên (từng mã hoặc bằng Excel), từ điển tên chuẩn, nhóm sợi "
        "và từ khoá của ô ghép tên, chuẩn hoá viết hoa."
    )

    def render(self) -> None:
        disabled, why = action_state("UC-65")
        if disabled:
            st.warning("Chỉ Sales hoặc Phòng SO xem được tên sợi nghi sai.", icon="🔒")
            explain(why)
            return
        show_flash(self.state)
        feature = gateway.open(YarnCostingController)
        tabs = st.tabs(
            ["🔎 Tên nghi sai", "🆕 Chữ mới chờ duyệt", "📖 Từ điển", "🧩 Nhóm sợi & từ khoá", "🔠 Chuẩn hoá viết hoa"]
        )
        with tabs[0]:
            data = self._suspects(feature)
        with tabs[1]:
            self._pending(feature, data)
        with tabs[2]:
            self._dictionary(feature, data)
        with tabs[3]:
            self._parts(feature, data)
        with tabs[4]:
            self._normalize(feature)

    # ---- UC-65 / UC-68 / UC-69 ----
    def _suspects(self, feature: YarnCostingController) -> NameCheckResponse:
        reference = feature.get_reference_data(GetReferenceDataRequest(factory_code=None))
        c1, c2, c3 = st.columns([1, 3, 2])
        factory = c1.selectbox(
            "Xưởng",
            [BOTH, *factory_codes(reference.factories)],
            format_func=lambda c: c if c == BOTH else factory_label(reference.factories, c),
            key=self.key("factory"),
        )
        issues = c2.multiselect(
            "Loại lỗi",
            list(NameIssueKind),
            default=DEFAULT_ISSUES,
            format_func=lambda k: k.value,
            key=self.key("issues"),
        )
        keyword = c3.text_input("Tìm mã / tên", key=self.key("keyword"))
        request = GetNameCheckRequest(factory_code=None if factory == BOTH else factory, issues=issues, keyword=keyword)
        data = feature.get_name_check(request)
        stat_row([(k.value, format_number(data.counts.get(k.value, 0))) for k in NameIssueKind])
        selected = data_table(
            [
                {
                    "Xưởng": s.factory_code.value,
                    "Mã": s.yarn_code,
                    "Trạng thái": s.status.value,
                    "Tên hiện tại": s.yarn_name,
                    "Lỗi": ", ".join(i.value for i in s.issues),
                    "Chi tiết": s.detail,
                    "Gợi ý tên": s.suggested_name,
                }
                for s in data.suspects
            ],
            selection="single",
            empty_message="Không có tên nghi sai phù hợp bộ lọc.",
            key=self.key("suspects"),
        )
        picked = next((s for s in data.suspects if selected and s.yarn_code == selected[0]["Mã"]), None)
        self._rename(feature, picked)
        self._rename_file(feature, request)
        return data

    def _rename(self, feature: YarnCostingController, picked: Any) -> None:
        disabled, why = action_state("UC-68")
        with panel(
            "Đổi tên sợi", icon="✏️", description="Giá, mã tính giá, mã kế toán không đổi; tên cũ được giữ để tìm kiếm."
        ):
            code = st.text_input(
                "Mã sợi",
                value=picked.yarn_code if picked else "",
                key=self.key(f"r_code.{picked.yarn_code if picked else ''}"),
            )
            if not code.strip():
                st.caption("Chọn một dòng ở bảng trên hoặc nhập mã sợi.")
                return
            scope = self.key(f"r_name.{code}")
            initial = (picked.suggested_name or picked.yarn_name) if picked and picked.yarn_code == code else ""
            if picked and picked.yarn_code == code:
                st.caption(f"Tên hiện tại: {picked.yarn_name}")
            new_name, _, word_reason, check = name_input(
                feature, scope, initial=initial, allow_builder=False, label="Tên mới"
            )
            reason = st.text_input("Lý do đổi tên", max_chars=500, key=self.key(f"r_reason.{code}"))
            if new_name and reason.strip():
                preview = try_call(
                    lambda: feature.rename_yarn(
                        RenameYarnRequest(
                            yarn_code=code,
                            new_name=new_name,
                            reason=reason,
                            unknown_word_reason=word_reason,
                            preview=True,
                        )
                    )
                )
                if preview is not None:
                    group = (
                        f"Nhóm tiêu hao: {preview.old_loss_group} → {preview.new_loss_group}"
                        if preview.old_loss_group != preview.new_loss_group
                        else f"Nhóm tiêu hao giữ nguyên: {preview.old_loss_group or '-'}"
                    )
                    st.info(f"'{preview.old_name}' → '{preview.new_name}'. {group}.")
            request = RenameYarnRequest(
                yarn_code=code, new_name=new_name, reason=reason, unknown_word_reason=word_reason
            )
            if st.button(
                "Đổi tên",
                type="primary",
                icon="💾",
                key=self.key("r_save"),
                disabled=disabled or not new_name or bool(check and check.problem),
                help=why,
            ):
                run_save(self.state, lambda: feature.rename_yarn(request).message)
            explain(why)

    def _rename_file(self, feature: YarnCostingController, filters: GetNameCheckRequest) -> None:
        disabled, why = action_state("UC-69")
        with panel(
            "Sửa tên bằng Excel",
            icon="📤",
            description="Tải danh sách đang lọc, điền cột 'Tên mới' và 'Lý do sửa', rồi tải lên.",
        ):
            download_button(
                lambda: feature.export_rename_list(ExportRenameListRequest(**filters.model_dump())),
                label="Tải danh sách để sửa",
                key=self.key("rf_export"),
                file_name="sua-ten-soi.xlsx",
            )
            file = file_upload("File sửa tên", types=[".xlsx", ".xlsm", ".xls"], key=self.key("rf_file"))
            signature = (file.filename, len(file.content)) if file is not None else None
            if st.button(
                "Kiểm tra file", icon="🔍", key=self.key("rf_check"), disabled=disabled or file is None, help=why
            ):
                result = try_call(lambda: feature.import_rename_file(ImportRenameFileRequest(file=file)))
                if result is not None:
                    self.state.set(FILE_KEY, {"sig": signature, "result": result})
            explain(why)
            stored = self.state.get(FILE_KEY)
            if not stored or file is None or stored["sig"] != signature:
                return
            result: RenameImportResponse = stored["result"]
            st.info(result.message)
            data_table(
                [
                    {
                        "Xưởng": r.factory_code.value,
                        "Mã": r.yarn_code,
                        "Tên cũ": r.old_name,
                        "Tên mới": r.new_name,
                        "Lý do": r.reason,
                        "Nhóm tiêu hao": r.old_loss_group
                        if r.old_loss_group == r.new_loss_group
                        else f"{r.old_loss_group} → {r.new_loss_group}",
                    }
                    for r in result.valid
                ],
                empty_message="Không có dòng hợp lệ.",
                key=self.key("rf_valid"),
            )
            if result.rejected_rows:
                st.markdown("**Dòng bị loại**")
                data_table(
                    [{"Dòng": r.excel_row, "Mã": r.key, "Lý do": r.reason} for r in result.rejected_rows],
                    column_config={"Dòng": count_col("Dòng")},
                    key=self.key("rf_rejected"),
                )
            if st.button(
                f"Lưu {len(result.valid)} tên",
                type="primary",
                icon="💾",
                key=self.key("rf_commit"),
                disabled=disabled or not result.valid,
            ):
                request = ImportRenameFileRequest(file=file, commit=True)

                def action() -> str:
                    done = feature.import_rename_file(request)
                    self.state.pop(FILE_KEY)
                    return done.message

                confirm_dialog(
                    self.state,
                    self.key("dlg.rf_commit"),
                    "Xác nhận đổi tên",
                    f"Đổi tên {len(result.valid)} sợi theo file? Giá và mã không đổi; tên cũ được giữ để tìm kiếm.",
                    "Đổi tên",
                    action,
                )

    # ---- UC-67 ----
    def _pending(self, feature: YarnCostingController, data: NameCheckResponse) -> None:
        disabled, why = action_state("UC-67")
        rows = [
            {
                "Chữ": p.word,
                "Số lần": p.count,
                "Lần cuối": p.last_at,
                "Người gõ": ", ".join(dict.fromkeys(u.typed_by for u in p.uses if u.typed_by)),
                "Mã yêu cầu": ", ".join(dict.fromkeys(u.yarn_code for u in p.uses)),
                "Lý do": "; ".join(dict.fromkeys(u.reason for u in p.uses if u.reason)),
                "Trạng thái": p.status.value + (f" → {p.resolved_word}" if p.resolved_word else ""),
                "Gợi ý": p.suggestion,
            }
            for p in data.pending
        ]
        selected = data_table(
            rows,
            column_config={"Số lần": count_col("Số lần"), "Lần cuối": datetime_col("Lần cuối")},
            selection="single",
            empty_message="Chưa có chữ mới nào.",
            key=self.key("pending"),
        )
        item = next((p for p in data.pending if selected and p.word == selected[0]["Chữ"]), None)
        if item is None:
            return
        if item.status != PendingWordStatus.CHO_DUYET:
            st.caption(f"Chữ '{item.word}' đã được xử lý ({item.status.value}).")
        standard = sorted(w.word for w in data.words if w.kind == NameWordKind.CHUAN)
        c1, c2, c3 = st.columns([1, 2, 1])
        if c1.button("Thêm vào từ điển", icon="➕", key=self.key("p_add"), disabled=disabled, help=why):
            run_save(
                self.state, lambda: feature.resolve_pending_word(ResolvePendingWordRequest(pending_id=item.id)).message
            )
        right = c2.selectbox(
            "Sửa thành",
            standard,
            index=standard.index(item.suggestion) if item.suggestion in standard else None,
            placeholder="Chọn chữ đúng",
            key=self.key(f"p_right.{item.id}"),
        )
        if c3.button("Sai, sửa thành", icon="🛠️", key=self.key("p_fix"), disabled=disabled or not right, help=why):
            preview = try_call(
                lambda: feature.resolve_pending_word(
                    ResolvePendingWordRequest(pending_id=item.id, correct_word=right, preview=True)
                )
            )
            if preview is not None:
                confirm_dialog(
                    self.state,
                    self.key("dlg.p_fix"),
                    "Xác nhận sửa chữ sai",
                    preview.message + " Tiêu hao và giá không đổi.",
                    "Sửa",
                    lambda: (
                        feature.resolve_pending_word(
                            ResolvePendingWordRequest(pending_id=item.id, correct_word=right)
                        ).message
                    ),
                )
        explain(why)

    # ---- UC-66 ----
    def _dictionary(self, feature: YarnCostingController, data: NameCheckResponse) -> None:
        disabled, why = action_state("UC-66")
        standard = sorted(w.word for w in data.words if w.kind == NameWordKind.CHUAN)
        edited = editable_table(
            [
                {"Chữ": w.word, "Loại": w.kind.value, "Chữ đúng": w.correct_word or None, "Nguồn": w.source.value}
                for w in data.words
            ],
            key=self.key("words"),
            columns=["Chữ", "Loại", "Chữ đúng", "Nguồn"],
            column_config={
                "Loại": st.column_config.SelectboxColumn("Loại", options=KINDS, required=True),
                "Chữ đúng": st.column_config.SelectboxColumn("Chữ đúng", options=standard),
            },
            disabled=("Nguồn",),
            allow_add_delete=True,
        )
        if st.button("Lưu từ điển", type="primary", icon="💾", key=self.key("w_save"), disabled=disabled, help=why):
            words = [
                NameWordDTO(
                    word=str(r.get("Chữ") or ""),
                    kind=NameWordKind(r.get("Loại") or NameWordKind.CHUAN.value),
                    correct_word=str(r.get("Chữ đúng") or ""),
                )
                for r in edited
                if r.get("Chữ")
            ]
            run_save(self.state, lambda: feature.save_name_dictionary(SaveNameDictionaryRequest(words=words)).message)
        explain(why)

    # ---- UC-70 ----
    def _parts(self, feature: YarnCostingController, data: NameCheckResponse) -> None:
        disabled, why = action_state("UC-70")
        only_new = st.toggle("Chỉ hiện nhóm Sales mới thêm", key=self.key("only_new"))
        shown = [g for g in data.groups if not only_new or not g.reviewed]
        hidden = [g for g in data.groups if g not in shown]
        st.markdown("**Nhóm sợi**")
        groups = editable_table(
            [
                {"_id": g.id, "Nhóm": g.text, "Số xơ": g.fiber_count, "Nguồn": g.source.value, "Đã xem": g.reviewed}
                for g in shown
            ],
            key=self.key(f"groups.{only_new}"),
            columns=["_id", "Nhóm", "Số xơ", "Nguồn", "Đã xem"],
            column_order=["Nhóm", "Số xơ", "Nguồn", "Đã xem"],
            column_config={"Số xơ": st.column_config.NumberColumn("Số xơ", min_value=1, max_value=5, step=1)},
            disabled=("Nguồn",),
            allow_add_delete=True,
        )
        st.markdown("**Từ khoá** (ghép theo Thứ tự tăng dần)")
        keywords = editable_table(
            [{"_id": k.id, "Từ khoá": k.text, "Thứ tự": k.sequence, "Nguồn": k.source.value} for k in data.keywords],
            key=self.key("keywords"),
            columns=["_id", "Từ khoá", "Thứ tự", "Nguồn"],
            column_order=["Từ khoá", "Thứ tự", "Nguồn"],
            column_config={"Thứ tự": st.column_config.NumberColumn("Thứ tự", step=1)},
            disabled=("Nguồn",),
            allow_add_delete=True,
        )
        if st.button("Lưu", type="primary", icon="💾", key=self.key("parts_save"), disabled=disabled, help=why):
            parts = [NamePartDTO(**h.model_dump()) for h in hidden]  # rows hidden by the filter are kept as they are
            parts += [
                NamePartDTO(
                    id=r.get("_id") or "",
                    kind=NamePartKind.NHOM,
                    text=str(r.get("Nhóm") or ""),
                    fiber_count=int(r.get("Số xơ") or 1),
                    source=NamePartSource.PHONG_SO,
                    reviewed=bool(r.get("Đã xem")),
                )
                for r in groups
                if r.get("Nhóm")
            ]
            parts += [
                NamePartDTO(
                    id=r.get("_id") or "",
                    kind=NamePartKind.TU_KHOA,
                    text=str(r.get("Từ khoá") or ""),
                    sequence=int(r.get("Thứ tự") or 0),
                )
                for r in keywords
                if r.get("Từ khoá")
            ]
            run_save(self.state, lambda: feature.save_name_parts(SaveNamePartsRequest(parts=parts)).message)
        explain(why)

    # ---- UC-71 ----
    def _normalize(self, feature: YarnCostingController) -> None:
        disabled, why = action_state("UC-71")
        st.caption(
            "Viết hoa mọi tên sợi một lượt; nhóm tên trùng (sau khi viết hoa) giữ 1 mã, mã còn lại được đánh dấu Không sản xuất "
            "(mã đang Chờ xưởng xem: Từ chối), tên theo khách và mã kế toán chuyển sang mã giữ. Không xoá dữ liệu."
        )
        if st.button("Xem trước", icon="🔍", key=self.key("n_preview"), disabled=disabled, help=why):
            self.state.set(NORMALIZE_KEY, try_call(lambda: feature.normalize_names(NormalizeNamesRequest())))
        explain(why)
        preview: NormalizeNamesResponse | None = self.state.get(NORMALIZE_KEY)
        if preview is None:
            return
        if preview.message:
            st.success(preview.message)
            return
        stat_row(
            [
                ("Tên sẽ đổi", format_number(preview.rename_count)),
                ("Nhóm trùng", format_number(preview.group_count)),
                ("Mã giữ", format_number(preview.keep_count)),
                ("Mã loại", format_number(preview.drop_count)),
                ("Mã loại có mã kế toán", format_number(preview.drop_with_code_count)),
            ]
        )
        if preview.plan_file is not None:
            download_button(preview.plan_file, label="Tải đề xuất (Excel)", key=self.key("n_plan"))
        with panel("Đề xuất giữ / loại", icon="⚖️"):
            data_table(
                [
                    {
                        "Xưởng": d.factory_code.value,
                        "Tên sau khi viết hoa": d.upper_name,
                        "Đề xuất": "GIỮ" if d.keep else "LOẠI",
                        "Mã": d.yarn_code,
                        "Trạng thái": d.status.value,
                        "Mã kế toán": ", ".join(d.accounting_codes),
                        "Lý do": d.reason,
                    }
                    for d in preview.decisions
                ],
                empty_message="Không có tên trùng.",
                key=self.key("n_decisions"),
            )
        with panel("Tên sẽ đổi", icon="🔠"):
            data_table(
                [
                    {"Xưởng": c.factory_code.value, "Mã": c.yarn_code, "Tên cũ": c.old_name, "Tên mới": c.new_name}
                    for c in preview.changes
                ],
                empty_message="Mọi tên đã viết hoa.",
                key=self.key("n_changes"),
            )
        if st.button("Chuẩn hoá", type="primary", icon="🔠", key=self.key("n_commit"), disabled=disabled, help=why):

            def action() -> str:
                done = feature.normalize_names(NormalizeNamesRequest(commit=True))
                self.state.pop(NORMALIZE_KEY)
                return done.message

            confirm_dialog(
                self.state,
                self.key("dlg.n_commit"),
                "Xác nhận chuẩn hoá tên sợi",
                f"Viết hoa {preview.rename_count} tên và loại {preview.drop_count} mã trùng tên "
                f"({preview.drop_with_code_count} mã có mã kế toán, mã kế toán chuyển sang mã giữ)?",
                "Chuẩn hoá",
                action,
            )
