"""Screen 4 - Dữ liệu mã vải: tải Peace / WFX, tra cứu, nhập nhanh mã vải và in nhãn (UC-01..UC-04, UC-26, UC-39)."""

from typing import Any

import streamlit as st

from backend.core.base import EmptyRequest
from backend.core.gateway import gateway
from backend.features.woven_costing import WovenCostingController
from backend.features.woven_costing.dto.common_dto import FabricSource, ImportResult, RoleCode
from backend.features.woven_costing.dto.fabric_dto import PreviewFabricImportRequest, SearchFabricsRequest
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, panel, stat_row
from frontend.core.formatting import format_number
from frontend.features.woven_costing.components.dialogs import confirm_dialog
from frontend.features.woven_costing.components.errors import attempt
from frontend.features.woven_costing.components.fabric_form import fabric_dialog
from frontend.features.woven_costing.components.fabric_view import spec_table, yarn_table
from frontend.features.woven_costing.components.flash import show_flash
from frontend.features.woven_costing.components.label_dialog import label_dialog
from frontend.features.woven_costing.components.labels import enum_values, num, pct_text, text, to_pct
from frontend.features.woven_costing.components.multi_upload import multi_file_upload
from frontend.features.woven_costing.components.roles import has_any

ALL = "Tất cả"
SHOWN_RESULTS = {ImportResult.NEW.value, ImportResult.CHANGED.value, ImportResult.ERROR.value}
PREVIEW = "fab.preview"


class FabricDataPage(BasePage):
    title = "Dữ liệu mã vải"
    icon = "🧶"
    slug = "ma-vai"
    menu_group = "Phòng SO"
    description = "Tải dữ liệu vải Peace / WFX, tra cứu, nhập nhanh mã vải và in nhãn."

    def render(self) -> None:
        show_flash(self.state)
        feature = gateway.open(WovenCostingController)
        is_so = has_any(RoleCode.SO.value)
        labels = ["Tải Peace/WFX", "Tra cứu & nhập tay"] if is_so else ["Tra cứu & nhập tay"]
        tabs = st.tabs(labels, key=self.key(f"tabs.{len(labels)}"), on_change="rerun")
        if is_so:
            with tabs[0]:
                if tabs[0].open:
                    self._import_tab(feature)
        with tabs[-1]:
            if tabs[-1].open:
                self._search_tab(feature)

    # ---- Tải Peace/WFX (SO) -------------------------------------------------------------------------------------
    def _import_tab(self, feature: WovenCostingController) -> None:
        with panel(
            "Chọn file",
            icon="📤",
            description="Chọn 1-4 file: Peace Weaving control, Peace TCFNO STANDARD, WFX Weaving_Control_Report, "
            "WFX TCFNO_Standard_Report (.xlsx / .xls).",
        ):
            files = multi_file_upload("File dữ liệu vải", types=[".xlsx", ".xls"], key=self.key("files"))
            check = st.button(
                "Kiểm tra", type="primary", icon=":material/fact_check:", disabled=not files, key=self.key("check")
            )
        names = sorted(f.filename for f in files)
        preview = self.state.get(PREVIEW)
        if preview is not None and sorted(preview.file_names) != names:
            self.state.pop(PREVIEW)
            preview = None
        if check and files:
            preview = attempt(lambda: feature.preview_fabric_import(PreviewFabricImportRequest(files=files)))
            if preview is not None:
                self.state.set(PREVIEW, preview)
        if preview is not None:
            self._preview(feature, preview, files)
        with panel("5 lần cập nhật gần nhất", icon="🕘"):
            logs = feature.list_fabric_imports(EmptyRequest())
            data_table(
                [
                    {
                        "Thời điểm": r.imported_at,
                        "Người tải": r.imported_by,
                        "Tên file": r.file_names,
                        "Mới": r.new_count,
                        "Thay đổi": r.changed_count,
                        "Không đổi": r.unchanged_count,
                        "Thiếu sợi": r.missing_yarn_count,
                        "Lỗi": r.error_count,
                    }
                    for r in logs.rows
                ],
                column_config={"Thời điểm": st.column_config.DatetimeColumn("Thời điểm", format="DD/MM/YYYY HH:mm")},
                empty_message="Chưa có lần cập nhật nào.",
            )

    def _preview(self, feature: WovenCostingController, p: Any, files: list[Any]) -> None:
        with panel("Kết quả kiểm tra", icon="🔍"):
            if p.file_counts:
                st.caption(" · ".join(f"{c.file_name} ({c.kind}): {format_number(c.count)} mã" for c in p.file_counts))
            stat_row(
                [
                    ("Mới", format_number(p.new_count)),
                    ("Thay đổi", format_number(p.changed_count)),
                    ("Không đổi", format_number(p.unchanged_count)),
                    ("Thiếu sợi", format_number(p.missing_yarn_count)),
                    ("Lỗi", format_number(p.error_count)),
                ]
            )
            only = st.toggle("Chỉ hiện mã mới / thay đổi / lỗi", value=True, key=self.key("only_changes"))
            rows = [r for r in p.rows if not only or text(r.result) in SHOWN_RESULTS]
            data_table(
                [
                    {"Mã vải": r.tcfno, "Tên vải": r.fabric_name, "Nguồn": r.source, "Kết quả": text(r.result),
                     "Lý do": r.reason}
                    for r in rows
                ],
                empty_message="Không có mã mới / thay đổi / lỗi.",
            )  # fmt: skip
            count = p.new_count + p.changed_count
            if st.button(
                f"Lưu {count} mã", type="primary", icon=":material/save:", disabled=count == 0, key=self.key("save")
            ):
                confirm_dialog(
                    self.state,
                    self.key("save_dialog"),
                    "Lưu dữ liệu vải",
                    f"Lưu {p.new_count} mã mới và cập nhật {p.changed_count} mã? "
                    "Mã đang lưu nhưng không có trong file được giữ nguyên.",
                    "Lưu",
                    lambda _: (feature.save_fabric_import(PreviewFabricImportRequest(files=files)).message, []),
                    on_done=lambda: self.state.pop(PREVIEW),
                )

    # ---- Tra cứu & nhập tay -------------------------------------------------------------------------------------
    def _search_tab(self, feature: WovenCostingController) -> None:
        can_edit = has_any(RoleCode.SO.value, RoleCode.PD.value)
        with panel("Bộ lọc", icon="🔎"):
            c1, c2, c3 = st.columns([3, 2, 1], vertical_alignment="bottom")
            keyword = c1.text_input(
                "Từ khóa", placeholder="Mã vải hoặc tên vải", key=self.key("keyword"), persist_state="session"
            )
            with c2:
                source = st.segmented_control(
                    "Nguồn",
                    [ALL, *enum_values(FabricSource)],
                    default=ALL,
                    required=True,
                    key=self.key("source"),
                    persist_state="session",
                )
            missing = c3.toggle("Chỉ mã thiếu sợi", key=self.key("missing"), persist_state="session")
        base = {
            "keyword": (keyword or "").strip(),
            "source": None if source in (None, ALL) else source,
            "missing_yarn_only": missing,
        }
        data = feature.search_fabrics(SearchFabricsRequest(**base))
        stat_row([("Số mã", format_number(data.total))])
        picked = data_table(
            [
                {
                    "Mã vải": r.tcfno,
                    "Tên vải": r.fabric_name,
                    "Nguồn": text(r.source),
                    "Khổ mộc": num(r.greige_width_cm),
                    "Mật độ dọc mộc": num(r.greige_warp_density),
                    "Mật độ ngang mộc": num(r.greige_weft_density),
                    "g/m mộc": num(r.greige_g_per_m),
                    "Khổ TP": num(r.finished_width_cm),
                    "g/m TP": num(r.finished_g_per_m),
                    "Độ co (%)": to_pct(r.shrinkage),
                    "Độ co mắc (%)": to_pct(r.warping_loss_rate),
                    "Ngày tạo": r.created_date,
                    "Cập nhật lúc": r.updated_at,
                }
                for r in data.rows
            ],
            column_config={
                "Độ co (%)": st.column_config.NumberColumn("Độ co (%)", format="%.2f"),
                "Độ co mắc (%)": st.column_config.NumberColumn("Độ co mắc (%)", format="%.2f"),
                "Ngày tạo": st.column_config.DateColumn("Ngày tạo", format="DD/MM/YYYY"),
                "Cập nhật lúc": st.column_config.DatetimeColumn("Cập nhật lúc", format="DD/MM/YYYY HH:mm"),
            },
            selection="single",
            key=self.key("grid"),
            empty_message="Không tìm thấy mã vải.",
        )
        tcfno = str(picked[0]["Mã vải"]) if picked else None
        detail = feature.search_fabrics(SearchFabricsRequest(**base, selected_tcfno=tcfno)).detail if tcfno else None
        with st.container(horizontal=True, gap="small"):
            add = can_edit and st.button("Thêm mã vải", icon=":material/add:", key=self.key("add"))
            edit = can_edit and st.button("Sửa", icon=":material/edit:", key=self.key("edit"), disabled=detail is None)
            label = st.button("In nhãn", icon=":material/print:", key=self.key("label"))
        if add:
            fabric_dialog(self, feature, None)
        if edit and detail is not None:
            fabric_dialog(self, feature, detail)
        if label:
            label_dialog(feature, [tcfno] if tcfno else [], self.key(f"label.{tcfno or 'none'}"))
        if detail is None:
            st.caption("Chọn 1 mã vải trong bảng để xem thông số và các dòng sợi.")
            return
        with panel(f"{detail.tcfno} - {detail.fabric_name}", icon="📄"):
            with st.container(horizontal=True, gap="small"):
                source_text = text(detail.source)
                st.badge(f"Nguồn: {source_text}", color="orange" if source_text == "Nhập tay" else "blue")
                st.caption(f"Độ co mắc: {pct_text(detail.warping_loss_rate)}")
            spec_table(detail)
            if detail.remark:
                st.caption(f"Remark: {detail.remark}")
            yarn_table(detail.yarns, full=True, empty_message="Mã vải chưa có dòng sợi.")
