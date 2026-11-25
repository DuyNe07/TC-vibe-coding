"""Screen 8 - Gia công nhuộm (2026-11-25): job orders with many item / OC lines, like the NGC file (UC-40..UC-46)."""

import hashlib
from datetime import date, timedelta
from typing import Any

import streamlit as st

from backend.core.base import EmptyRequest
from backend.core.gateway import gateway
from backend.features.woven_costing import WovenCostingController
from backend.features.woven_costing.dto.common_dto import CostsheetAction, CostsheetStatus, DyePlant
from backend.features.woven_costing.dto.dyeing_job_dto import (
    CostItemsDTO,
    CreateDyeingJobRequest,
    DyeingJobActionRequest,
    DyeingJobInputDTO,
    DyeingJobInputRequest,
    DyeingJobLineDTO,
    DyeingJobResponse,
    GetDyeingJobRequest,
    ListDyeingJobsRequest,
)
from backend.features.woven_costing.dto.list_dto import CostsheetOptionsResponse
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, editable_table, panel, section_title, stat_row
from frontend.core.formatting import format_number
from frontend.features.woven_costing.components.costsheet_dyeing import job_line_dyeing
from frontend.features.woven_costing.components.errors import attempt
from frontend.features.woven_costing.components.flash import set_flash, show_flash
from frontend.features.woven_costing.components.labels import dec, from_pct, index_of, num, pct_text, to_pct

OPEN, WORKING, REV, DIRTY, BASE = "gc.open", "gc.working", "gc.rev", "gc.dirty", "gc.base"
PLANTS = [p.value for p in DyePlant]
IDX = "_i"
LINE_COLUMNS = {
    "% B/C": "finished_bc_rate",
    "Mã hàng": "item_code",
    "Style": "style",
    "Số OC": "oc_no",
    "ODNO": "odno",
    "g/m": "g_per_m",
    "g/m2": "g_per_m2",
    "Độ co (%)": "shrinkage",
    "Số lượng (m)": "quantity_m",
    "Đơn giá GC (đ/m)": "job_price_vnd",
}
PCT_COLUMNS = ("% B/C", "Độ co (%)")
TEXT_COLUMNS = ("Mã hàng", "Style", "Số OC", "ODNO")
RESULT_COLUMNS = ("Định mức (đ/m)", "Định mức TP (đ/m)", "Chi phí (đ)", "Giá GC (đ)", "GP (đ)", "%GP")
ITEM_LABELS = {"chemical": "Hóa chất", "labor": "Nhân công", "depreciation": "Khấu hao", "power": "Điện",
               "fuel": "Nhiên liệu", "material": "Vật tư", "overhead": "CPQL"}  # fmt: skip
MONEY = st.column_config.NumberColumn(format="localized")


class DyeingJobPage(BasePage):
    title = "Gia công nhuộm"
    icon = "🎨"
    slug = "gia-cong-nhuom"
    menu_group = "Sales"
    description = "Phiếu tính giá hàng nhận gia công nhuộm: nhiều mã hàng / OC trên một phiếu, duyệt một lần."

    def render(self) -> None:
        show_flash(self.state)
        feature = gateway.open(WovenCostingController)
        options = feature.get_costsheet_options(EmptyRequest())
        self._list(feature, options)
        working = self._working(feature)
        if working is None:
            return
        sfx = f"{working.id}.{self.state.get(REV, 0)}"
        typed = self._editor(working, options, sfx)
        self._results(working)
        self._toolbar(feature, working, typed)
        if typed is not None:
            self._auto_calculate(feature, working, typed)

    # ---- list + create (UC-44, UC-40) ------------------------------------------------------------------------------
    def _list(self, feature: WovenCostingController, options: CostsheetOptionsResponse) -> None:
        today = date.today()
        with st.expander("📋 Danh sách phiếu gia công", expanded=self.state.get(OPEN) is None, key=self.key("list")):
            c1, c2, c3 = st.columns([2, 2, 2])
            keyword = c1.text_input("Từ khóa", placeholder="Số phiếu, hợp đồng, mã hàng, OC", key=self.key("kw"))
            statuses = c2.multiselect("Trạng thái", [s.value for s in CostsheetStatus], key=self.key("st"))
            period = c3.date_input("Ngày tính giá", value=(today - timedelta(days=90), today), format="DD/MM/YYYY",
                                   key=self.key("period"))  # fmt: skip
            start, end = (period[0], period[-1]) if isinstance(period, (list, tuple)) and period else (None, None)
            request = ListDyeingJobsRequest(keyword=keyword, statuses=[CostsheetStatus(s) for s in statuses],
                                            date_from=start, date_to=end)  # fmt: skip
            rows = feature.list_dyeing_jobs(request).rows
            picked = data_table(
                [
                    {
                        "id": r.id,
                        "Số phiếu": r.job_no,
                        "Trạng thái": r.status.value,
                        "Ngày tính giá": r.costing_date,
                        "Khách hàng": r.customer_name,
                        "Số hợp đồng": r.contract_no,
                        "Đơn vị GC": r.dye_plant.value,
                        "Số dòng": r.line_count,
                        "Tổng SL (m)": num(r.total_quantity),
                        "Tổng giá GC (đ)": num(r.total_revenue),
                        "GP (đ)": num(r.gp),
                        "%GP": to_pct(r.gp_pct),
                        "Sales": r.sales_name,
                        "Người duyệt": r.approved_by_name,
                    }
                    for r in rows
                ],  # fmt: skip
                column_config={
                    "Ngày tính giá": st.column_config.DateColumn("Ngày tính giá", format="DD/MM/YYYY"),
                    "Tổng SL (m)": MONEY,
                    "Tổng giá GC (đ)": MONEY,
                    "GP (đ)": MONEY,
                    "%GP": st.column_config.NumberColumn("%GP", format="%.2f %%"),
                },  # fmt: skip
                column_order=[
                    "Số phiếu",
                    "Trạng thái",
                    "Ngày tính giá",
                    "Khách hàng",
                    "Số hợp đồng",
                    "Đơn vị GC",
                    "Số dòng",
                    "Tổng SL (m)",
                    "Tổng giá GC (đ)",
                    "GP (đ)",
                    "%GP",
                    "Sales",
                    "Người duyệt",
                ],  # fmt: skip
                empty_message="Chưa có phiếu gia công nào phù hợp bộ lọc.",
                selection="single",
                key=self.key("grid"),
            )
            if st.button("Mở phiếu đã chọn", icon=":material/folder_open:", key=self.key("open"), disabled=not picked):
                self._open(str(picked[0]["id"]))
        with st.expander("➕ Tạo phiếu gia công (đơn vị gia công mặc định TCDN)", key=self.key("create")):
            with st.form(self.key("new"), border=False):
                c1, c2, c3, c4 = st.columns(4)
                names = [c.name for c in options.customers]
                customer = c1.selectbox("Khách hàng", names, index=None, placeholder="Chọn khách hàng",
                                        key=self.key("new.customer"))  # fmt: skip
                contract = c2.text_input("Số hợp đồng", max_chars=60, key=self.key("new.contract"))
                with c3:
                    plant = st.segmented_control("Đơn vị gia công", PLANTS, default=DyePlant.TCDN.value, required=True,
                                                 key=self.key("new.plant"))  # fmt: skip
                costing = c4.date_input("Ngày tính giá", value=today, format="DD/MM/YYYY", key=self.key("new.date"))
                submitted = st.form_submit_button("Tạo phiếu gia công", type="primary", icon=":material/add:")
            if submitted:
                created = attempt(lambda: feature.create_dyeing_job(CreateDyeingJobRequest(
                    customer_name=customer or "", contract_no=contract or "",
                    dye_plant=DyePlant(plant or DyePlant.TCDN.value), costing_date=costing)))  # fmt: skip
                if created is not None:
                    self._replace(created)
                    set_flash(self.state, created.message)
                    st.rerun()

    def _open(self, job_id: str) -> None:
        self.state.set(OPEN, job_id)
        self.state.pop(WORKING)
        st.rerun()

    def _replace(self, response: DyeingJobResponse, dirty: bool = False) -> None:
        self.state.set(WORKING, response)
        self.state.set(OPEN, response.id)
        self.state.set(REV, int(self.state.get(REV, 0)) + 1)
        self.state.set(DIRTY, dirty)

    def _working(self, feature: WovenCostingController) -> DyeingJobResponse | None:
        job_id = self.state.get(OPEN)
        if not job_id:
            return None
        working = self.state.get(WORKING)
        if working is not None and working.id == job_id:
            return working
        loaded = attempt(lambda: feature.get_dyeing_job(GetDyeingJobRequest(job_id=job_id)))
        if loaded is None:
            self.state.pop(OPEN)
            return None
        self._replace(loaded)
        return loaded

    # ---- header + lines (UC-41) ------------------------------------------------------------------------------------
    def _editor(self, w: DyeingJobResponse, options: CostsheetOptionsResponse, sfx: str) -> DyeingJobInputDTO | None:
        data, off = w.input, not w.editable
        badge = " · :orange-badge[Có thay đổi chưa lưu]" if self.state.get(DIRTY) else ""
        st.subheader(f"{w.job_no} · {w.status.value}{badge}")
        st.caption(f"Người lập: {w.sales_name} ({w.team}) · Người duyệt: {w.approved_by_name or '-'} · Tỷ giá "
                   f"{format_number(w.exchange_rate)} · Bộ định mức {w.norm_set_code or '-'} · Bộ tham số "
                   f"{w.parameter_set_date:%d/%m/%Y}" if w.parameter_set_date else "")  # fmt: skip
        if w.return_reason and w.status == CostsheetStatus.TRA_LAI:
            st.warning(f"Lý do trả lại: {w.return_reason}", icon="↩️")
        if w.copied_from:
            st.caption(f"Sao chép từ {w.copied_from}.")
        with panel("Thông tin phiếu", icon="📝"):
            c1, c2, c3, c4 = st.columns(4)
            names = list(dict.fromkeys([*(c.name for c in options.customers), data.customer_name]))
            customer = c1.selectbox("Khách hàng", names, index=index_of(names, data.customer_name),
                                    key=self.key(f"customer.{sfx}"), disabled=off)  # fmt: skip
            contract = c2.text_input("Số hợp đồng", value=data.contract_no, max_chars=60, key=self.key(f"contract.{sfx}"),
                                     disabled=off)  # fmt: skip
            with c3:
                plant = st.segmented_control("Đơn vị gia công", PLANTS, default=data.dye_plant.value, required=True,
                                             key=self.key(f"plant.{sfx}"), disabled=off)  # fmt: skip
            costing = c4.date_input("Ngày tính giá", value=data.costing_date, format="DD/MM/YYYY",
                                    key=self.key(f"date.{sfx}"), disabled=off)  # fmt: skip
            note = st.text_area("Ghi chú", value=data.note, max_chars=1000, height=68, key=self.key(f"note.{sfx}"),
                                disabled=off)  # fmt: skip
        stat_row([
            ("Tổng số lượng (m)", format_number(w.total_quantity)),
            ("Tổng chi phí (đ)", format_number(w.total_cost)),
            ("Tổng giá GC (đ)", format_number(w.total_revenue)),
            ("GP (đ)", format_number(w.gp)),
            ("%GP", pct_text(w.gp_pct) + (" ⚠️" if w.gp_below else ""),
             f"Ngưỡng cảnh báo {pct_text(w.gp_threshold)}"),
        ])  # fmt: skip
        for warning in w.warnings:
            st.warning(warning.message, icon="⚠️")
        section_title("Dòng mã hàng")
        lines = self._lines_table(w, sfx)
        plant_value = plant or data.dye_plant.value
        lines = self._line_detail(w, lines, options, sfx, plant_value)
        if off:
            return None
        return DyeingJobInputDTO(contract_no=contract or "", customer_name=customer or "", note=note or "",
                                 dye_plant=DyePlant(plant_value), costing_date=costing, lines=lines)  # fmt: skip

    def _lines_table(self, w: DyeingJobResponse, sfx: str) -> list[DyeingJobLineDTO]:
        rows = []
        for index, line in enumerate(w.input.lines):
            res = w.lines[index] if index < len(w.lines) else None
            row: dict[str, Any] = {IDX: index}
            for label, field in LINE_COLUMNS.items():
                value = getattr(line, field)
                row[label] = to_pct(value) if label in PCT_COLUMNS else (value or "" if label in TEXT_COLUMNS
                                                                          else num(value))  # fmt: skip
            row |= {
                "Định mức (đ/m)": num(res.cost_per_m) if res else None,
                "Định mức TP (đ/m)": num(res.cost_per_m_finished) if res else None,
                "Chi phí (đ)": num(res.total_cost) if res else None,
                "Giá GC (đ)": num(res.revenue) if res else None,
                "GP (đ)": num(res.gp) if res else None,
                "%GP": to_pct(res.gp_pct) if res else None,
            }
            rows.append(row)
        config: dict[str, Any] = {label: MONEY for label in RESULT_COLUMNS if label != "%GP"}
        config |= {
            "%GP": st.column_config.NumberColumn("%GP", format="%.2f %%"),
            "% B/C": st.column_config.NumberColumn("% B/C", min_value=0.0, max_value=99.99, format="%.2f"),
            "Độ co (%)": st.column_config.NumberColumn("Độ co (%)", min_value=0.0, max_value=99.99, format="%.2f"),
            "Mã hàng": st.column_config.TextColumn("Mã hàng", max_chars=40, help="Mã hàng do khách đặt, gõ tự do"),
            "g/m": st.column_config.NumberColumn("g/m", min_value=0.0, format="%.2f"),
            "g/m2": st.column_config.NumberColumn("g/m2", min_value=0.0, format="%.2f"),
            "Số lượng (m)": st.column_config.NumberColumn("Số lượng (m)", min_value=0.0, format="localized"),
            "Đơn giá GC (đ/m)": st.column_config.NumberColumn("Đơn giá GC (đ/m)", min_value=0.0, format="%.3f"),
        }
        order = [*LINE_COLUMNS, *RESULT_COLUMNS]
        if not w.editable:
            data_table(rows, column_config=config, column_order=order, empty_message="Chưa có dòng mã hàng.")
            return list(w.input.lines)
        edited = editable_table(rows, key=self.key(f"lines.{sfx}"), columns=[IDX, *order], column_config=config,
                                column_order=order, disabled=RESULT_COLUMNS, allow_add_delete=True)  # fmt: skip
        st.caption("Thêm dòng ở cuối bảng; mỗi dòng 1 mã hàng / 1 OC (tối đa 30). Công đoạn của từng dòng sửa ở "
                   "\"Chi tiết dòng\" bên dưới.")  # fmt: skip
        lines = []
        for row in edited:
            if all(row.get(label) in (None, "") for label in LINE_COLUMNS):
                continue
            old = row.get(IDX)
            base = w.input.lines[int(old)] if old is not None and 0 <= int(old) < len(w.input.lines) else None
            values = {}
            for label, field in LINE_COLUMNS.items():
                cell = row.get(label)
                if label in PCT_COLUMNS:
                    values[field] = from_pct(cell) or dec(0)
                elif label in TEXT_COLUMNS:
                    values[field] = str(cell or "").strip()
                else:
                    values[field] = dec(cell)
            lines.append((base or DyeingJobLineDTO()).model_copy(update=values))
        return lines

    def _line_detail(self, w: DyeingJobResponse, lines: list[DyeingJobLineDTO], options: CostsheetOptionsResponse,
                     sfx: str, plant: str) -> list[DyeingJobLineDTO]:  # fmt: skip
        if not lines:
            return lines
        with panel("Chi tiết dòng", icon="🧪", description="Công đoạn, tính năng, báo giá riêng của 1 dòng."):
            labels = [f"{i + 1}. {ln.item_code or '(chưa có mã)'} {ln.oc_no}".strip() for i, ln in enumerate(lines)]
            chosen = st.selectbox("Dòng", range(len(lines)), format_func=lambda i: labels[i], key=self.key("pick"))
            index = int(chosen or 0) if chosen is not None and chosen < len(lines) else 0
            line = lines[index]
            dsfx = f"{sfx}.{index}.{plant}"
            dyeing = job_line_dyeing(self, line, w.editable, options, dsfx, plant)
            quoted = self._quoted(line, w.editable, dsfx)
            if index < len(w.lines):
                self._cost_lines(w, index)
        if dyeing is not None:
            key = "tcdn_dyeing" if plant == DyePlant.TCDN.value else "hcm_dyeing"
            current = getattr(line, key)
            line = line.model_copy(update={key: current.model_validate(current.model_dump() | dyeing)})
        if quoted is not None:
            line = line.model_copy(update={"quoted_items": quoted})
        return [line if i == index else ln for i, ln in enumerate(lines)]

    def _quoted(self, line: DyeingJobLineDTO, editable: bool, sfx: str) -> CostItemsDTO | None:
        with st.expander("Báo giá riêng từng mặt hàng (thay cho phần tự tính)",
                         expanded=line.quoted_items.model_dump() != CostItemsDTO().model_dump(),
                         key=self.key(f"quoted.{sfx}")):  # fmt: skip
            values = {}
            for column, (field, label) in zip(st.columns(7), ITEM_LABELS.items(), strict=True):
                values[field] = dec(column.number_input(f"{label} (đ/m)", min_value=0.0,
                                                        value=num(getattr(line.quoted_items, field)) or 0.0,
                                                        key=self.key(f"q.{field}.{sfx}"), disabled=not editable))  # fmt: skip
            st.caption("Để 0 hết thì app tự tính theo công đoạn.")
        return CostItemsDTO(**{k: v or dec(0) for k, v in values.items()}) if editable else None

    def _cost_lines(self, w: DyeingJobResponse, index: int) -> None:
        res = w.lines[index]
        section_title("Chi phí của dòng (đ/m)")
        data_table(
            [
                {
                    "Dòng": c.name,
                    **{label: num(getattr(c, field)) for field, label in ITEM_LABELS.items()},
                    "Hệ số": num(c.factor),
                    "Chi phí/m (đ)": num(c.per_m),
                }
                for c in res.cost_lines
            ],  # fmt: skip
            column_config={label: MONEY for label in [*ITEM_LABELS.values(), "Chi phí/m (đ)"]},
            empty_message="Chưa có chi phí (chọn nguyên liệu + cấp màu hoặc công đoạn).",
        )
        stat_row([
            ("Tổng định mức (đ/m)", format_number(res.cost_per_m)),
            ("Định mức TP (đ/m)", format_number(res.cost_per_m_finished)),
            ("Chi phí (đ)", format_number(res.total_cost)),
            ("GP (đ)", format_number(res.gp)),
            ("%GP", pct_text(res.gp_pct)),
        ])  # fmt: skip

    def _results(self, w: DyeingJobResponse) -> None:
        if not w.lines:
            return
        with st.expander("📊 Bảng giá (như sheet Output)", key=self.key("output")):
            data_table(
                [
                    {
                        "STT": i + 1,
                        "Mã vải": ln.item_code,
                        "Số OC": ln.oc_no,
                        "ODNO": ln.odno,
                        "Tổng các quy trình": r.process_text,
                        "Số lượng": num(ln.quantity_m),
                        "Tổng định mức (đ)": num(r.cost_per_m),
                        "Định mức TP (đ)": num(r.cost_per_m_finished),
                        "Đơn giá GC (đ)": num(ln.job_price_vnd),
                        "Chi phí (đ)": num(r.total_cost),
                        "Giá GC (đ)": num(r.revenue),
                        "GP (đ)": num(r.gp),
                        "%GP": to_pct(r.gp_pct),
                        **{label: num(getattr(r.items, f)) for f, label in ITEM_LABELS.items()},
                    }
                    for i, (ln, r) in enumerate(zip(w.input.lines, w.lines, strict=False))
                ],  # fmt: skip
                column_config={"%GP": st.column_config.NumberColumn("%GP", format="%.2f %%")}
                | {
                    k: MONEY
                    for k in [
                        "Số lượng",
                        "Tổng định mức (đ)",
                        "Định mức TP (đ)",
                        "Chi phí (đ)",
                        "Giá GC (đ)",
                        "GP (đ)",
                        *ITEM_LABELS.values(),
                    ]
                },  # fmt: skip
            )

    # ---- actions (UC-42, UC-43, UC-45, UC-46) ----------------------------------------------------------------------
    def _toolbar(self, feature: WovenCostingController, w: DyeingJobResponse, typed: DyeingJobInputDTO | None) -> None:
        allowed = set(w.allowed_actions)
        st.space("small")
        with st.container(horizontal=True, gap="small"):
            save = CostsheetAction.SAVE_DRAFT in allowed and st.button(
                "Lưu nháp", type="primary", icon=":material/save:", key=self.key("save"))  # fmt: skip
            submit = CostsheetAction.SUBMIT in allowed and st.button(
                "Gửi duyệt", icon=":material/send:", key=self.key("submit"))  # fmt: skip
            approve = CostsheetAction.APPROVE in allowed and st.button(
                "Duyệt", type="primary", icon=":material/check:", key=self.key("approve"))  # fmt: skip
            copy = CostsheetAction.COPY in allowed and st.button(
                "Sao chép", icon=":material/content_copy:", key=self.key("copy"))  # fmt: skip
            download_button(lambda: feature.export_dyeing_job(GetDyeingJobRequest(job_id=w.id)), label="Xuất Excel",
                            key=self.key("export"), file_name=f"gia-cong-{w.job_no}.xlsx")  # fmt: skip
            close = st.button("Đóng phiếu", icon=":material/close:", key=self.key("close"))
        reason_actions = [a for a in (CostsheetAction.RETURN, CostsheetAction.CANCEL) if a in allowed]
        returned = cancelled = False
        reason = ""
        if reason_actions:
            with st.expander("Trả lại / Hủy phiếu", key=self.key("reason.box")):
                reason = st.text_input("Lý do", max_chars=300, key=self.key("reason"))
                with st.container(horizontal=True, gap="small"):
                    returned = CostsheetAction.RETURN in allowed and st.button(
                        "Trả lại", icon=":material/undo:", key=self.key("return"))  # fmt: skip
                    cancelled = CostsheetAction.CANCEL in allowed and st.button(
                        "Hủy phiếu", icon=":material/block:", key=self.key("cancel"))  # fmt: skip
        done: DyeingJobResponse | None = None
        if save and typed is not None:
            done = attempt(lambda: feature.save_dyeing_job(DyeingJobInputRequest(job_id=w.id, **typed.model_dump())))
        elif submit:
            done = attempt(lambda: feature.submit_dyeing_job(DyeingJobActionRequest(job_id=w.id, input=typed)))
        elif approve:
            done = attempt(lambda: feature.approve_dyeing_job(DyeingJobActionRequest(job_id=w.id)))
        elif copy:
            done = attempt(lambda: feature.copy_dyeing_job(DyeingJobActionRequest(job_id=w.id)))
        elif returned:
            done = attempt(lambda: feature.return_dyeing_job(DyeingJobActionRequest(job_id=w.id, reason=reason)))
        elif cancelled:
            done = attempt(lambda: feature.cancel_dyeing_job(DyeingJobActionRequest(job_id=w.id, reason=reason)))
        elif close:
            self.state.pop(OPEN)
            self.state.pop(WORKING)
            st.rerun()
        if done is not None:
            self._replace(done)
            set_flash(self.state, done.message)
            st.rerun()

    def _auto_calculate(self, feature: WovenCostingController, w: DyeingJobResponse, typed: DyeingJobInputDTO) -> None:
        """Like Excel (UC-41): recalculate (not saved) when a cell differs from the cells of the current results."""
        if CostsheetAction.RECALCULATE not in w.allowed_actions:
            return
        fingerprint = hashlib.sha256(typed.model_dump_json().encode()).hexdigest()
        seen = (w.id, int(self.state.get(REV, 0)))
        base = self.state.get(BASE)
        if base is None or tuple(base[0]) != seen:
            self.state.set(BASE, (seen, fingerprint))
            return
        if base[1] == fingerprint:
            return
        response = attempt(lambda: feature.calculate_dyeing_job(DyeingJobInputRequest(job_id=w.id,
                                                                                       **typed.model_dump())))  # fmt: skip
        if response is not None:
            self._replace(response, dirty=True)
            st.rerun()
