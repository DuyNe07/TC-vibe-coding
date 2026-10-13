"""Screen 5 (`du-lieu-nen`) - Dữ liệu nền & định mức (UC-03..UC-09, UC-36, UC-37)."""

from collections.abc import Callable
from datetime import date
from typing import Any

import streamlit as st

from backend.core.exceptions import AppError
from backend.core.gateway import gateway
from backend.features.yarn_costing import YarnCostingController
from backend.features.yarn_costing.dto.common_dto import (
    ActorDTO,
    RateCodeSource,
    RecalcResultResponse,
    RecoveryType,
    SecondaryMethod,
    Technology,
)
from backend.features.yarn_costing.dto.master_dto import (
    AddExchangeRateRequest,
    ApplyRateVersionRequest,
    ListRecalcBatchesRequest,
    PackagingRowDTO,
    ProcessRouteRowDTO,
    RateLineRowDTO,
    RecalculateNotPricedRequest,
    RecoveryRowDTO,
    SavePackagingTypesRequest,
    SaveProcessRoutesRequest,
    SaveRecoveryRatesRequest,
    SaveStageConfigRequest,
    StageRowDTO,
    UpdateTrialFactorRequest,
)
from backend.features.yarn_costing.dto.reference_dto import (
    FactoryDTO,
    GetReferenceDataRequest,
    RateVersionDTO,
    ReferenceDataResponse,
)
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, editable_table, panel, section_title, show_error
from frontend.core.formatting import format_datetime, format_number
from frontend.features.yarn_costing.components.actor_block import render_actor_block
from frontend.features.yarn_costing.components.columns import (
    BATCH_CONFIG,
    batch_rows,
    count_col,
    date_col,
    datetime_col,
    money,
)
from frontend.features.yarn_costing.components.data_warnings import show_data_warnings
from frontend.features.yarn_costing.components.dialogs import confirm_dialog
from frontend.features.yarn_costing.components.display import (
    fmt_date,
    from_percent,
    optional_decimal,
    pct,
    plain,
    to_decimal,
)
from frontend.features.yarn_costing.components.factory_picker import factory_segment
from frontend.features.yarn_costing.components.flash import set_flash, show_flash
from frontend.features.yarn_costing.components.labels import (
    RATE_SOURCE_LABELS,
    RECOVERY_LABELS,
    SECONDARY_METHOD_LABELS,
    TECHNOLOGY_LABELS,
)
from frontend.features.yarn_costing.components.permissions import action_state, explain
from frontend.features.yarn_costing.components.recalc_diff import open_recalc_diff_dialog, render_recalc_diff

COL = st.column_config
LAST_BATCH_KEY = "last_batch_id"
RATE_ITEMS = (
    ("labor", "Nhân công"),
    ("depreciation", "Khấu hao"),
    ("electricity", "Điện"),
    ("materials", "Vật tư"),
    ("overhead", "CPQL"),
)
RECOVERY_ROWS = (RecoveryType.CHAI_THO, RecoveryType.THO, RecoveryType.CON)
STAGE_FIELDS = {
    "Thứ tự": "sequence",
    "Mã công đoạn": "stage_code",
    "Tên công đoạn": "stage_name",
    "Nhóm công đoạn": "stage_group",
    "Đóng gói": "is_packaging",
    "Hồi phế": "recovery_type",
    "Chải thô": "is_carding",
    "Số lượt tối đa": "max_passes",
    "Ô tỷ lệ pha": "blend_slot",
    "Công đoạn ghép": "is_merge_stage",
    "Cách tính thứ cấp": "secondary_method",
    "Công đoạn cộng lũy kế": "cumulative_stages",
    "NSM đổi theo chi số": "varies_with_count",
    "Nguồn định mức": "rate_code_source",
}
RATE_COLUMNS = ["Mã định mức", *[label for _, label in RATE_ITEMS], "Tổng (VND/phút)", "Ghi chú"]
PACKAGING_COLUMNS = [
    "Mã loại",
    "Mặc định",
    "Tên loại đóng gói",
    "Khối lượng (kg)",
    "Số công",
    "Phút/kg",
    "Đang dùng",
    "Có định mức",
]
ROUTE_COLUMNS = ["Nhóm sợi", "Công nghệ", "Số thành phần", "Quy trình", "Công đoạn nhận ra"]


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _batch_id(result: RecalcResultResponse) -> str | None:
    if result.batch is not None:
        return result.batch.batch_id
    return result.batches[0].batch_id if result.batches else None


def _rate_rows(lines: list[RateLineRowDTO]) -> list[dict[str, Any]]:
    return [
        {
            "Mã định mức": line.rate_code,
            **{label: plain(getattr(line, field)) for field, label in RATE_ITEMS},
            "Tổng (VND/phút)": plain(line.total_rate),
            "Ghi chú": line.note,
        }
        for line in lines
    ]


RATE_CONFIG = {
    "Mã định mức": COL.TextColumn("Mã định mức", required=True, max_chars=20),
    **{label: COL.NumberColumn(label, min_value=0.0, step=0.0001, format="%.4f") for _, label in RATE_ITEMS},
    "Tổng (VND/phút)": COL.NumberColumn("Tổng (VND/phút)", format="%.2f"),
    "Ghi chú": COL.TextColumn("Ghi chú", max_chars=200),
}


class MasterDataPage(BasePage):
    title = "Dữ liệu nền & định mức"
    menu_group = "Phòng SO"
    icon = "⚙️"
    slug = "du-lieu-nen"
    description = (
        "Phòng SO quản lý cấu hình công đoạn, định mức chi phí/phút, đóng gói, hồi phế, quy trình, tỷ giá, "
        "hệ số thí nghiệm và xem các lần tính lại."
    )

    def render(self) -> None:
        feature = gateway.open(YarnCostingController)
        reference = feature.get_reference_data(GetReferenceDataRequest(factory_code=None))
        show_data_warnings(reference)
        actor = render_actor_block(feature, self.state, reference)
        show_flash(self.state)

        top_left, top_right = st.columns([3, 2], vertical_alignment="bottom")
        with top_left:
            factory = factory_segment(reference.factories, self.key("factory"))
        if factory is None:
            return
        self._last_batch(feature, top_right)
        ref = feature.get_reference_data(GetReferenceDataRequest(factory_code=factory))
        factory_dto = next((f for f in reference.factories if str(f.code) == factory), None)

        tabs = st.tabs(
            ["Công đoạn", "Định mức", "Đóng gói", "Hồi phế", "Quy trình", "Tỷ giá & hệ số TN", "Các lần tính lại"]
        )
        with tabs[0]:
            self._stages_tab(feature, actor, factory, ref, factory_dto)
        with tabs[1]:
            self._rates_tab(feature, actor, factory, ref)
        with tabs[2]:
            self._packaging_tab(feature, actor, factory, ref)
        with tabs[3]:
            self._recovery_tab(feature, actor, factory, ref)
        with tabs[4]:
            self._routes_tab(feature, actor, factory, ref)
        with tabs[5]:
            self._exchange_tab(feature, actor, reference)
        with tabs[6]:
            self._batches_tab(feature, actor, factory)

    # ---- shared pieces ----
    def _last_batch(self, feature: YarnCostingController, container: Any) -> None:
        batch_id = self.state.get(LAST_BATCH_KEY)
        if not batch_id:
            return
        left, right = container.columns([2, 1])
        if left.button("Xem chênh lệch", icon="🔍", key=self.key("last_diff_btn")):
            open_recalc_diff_dialog(feature, batch_id, self.key(f"last_diff.{batch_id}"))
        if right.button("Ẩn", type="tertiary", key=self.key("last_diff_hide")):
            self.state.pop(LAST_BATCH_KEY)
            st.rerun()

    def _effective_inputs(self, tab: str, factory: str) -> tuple[date, str]:
        left, right = st.columns([1, 3])
        effective = left.date_input(
            "Ngày hiệu lực", value=date.today(), format="DD/MM/YYYY", key=self.key(f"{tab}.eff.{factory}")
        )
        reason = right.text_input("Lý do", max_chars=500, key=self.key(f"{tab}.reason.{factory}"))
        return effective, reason

    def _recalc_button(
        self,
        label: str,
        key: str,
        dialog_title: str,
        work: str,
        factory: str,
        effective: date,
        call: Callable[[], RecalcResultResponse],
        uc: str,
    ) -> None:
        disabled, why = action_state(self.state, uc)
        if st.button(label, type="primary", key=self.key(key), disabled=disabled, help=why):

            def action() -> str:
                result = call()
                batch_id = _batch_id(result)
                if batch_id:
                    self.state.set(LAST_BATCH_KEY, batch_id)
                return result.message

            confirm_dialog(
                self.state,
                self.key(f"dlg.{key}.{factory}"),
                dialog_title,
                f"{work} {factory} và tính lại toàn bộ giá của xưởng với ngày hiệu lực {fmt_date(effective)}? "
                "Mọi mã (kể cả mã đã có mã kế toán) sẽ được tính lại.",
                "Lưu và tính lại" if not key.startswith("rates") else "Áp dụng và tính lại",
                action,
            )
        explain(why)

    # ---- UC-03 ----
    def _stages_tab(
        self,
        feature: YarnCostingController,
        actor: ActorDTO | None,
        factory: str,
        ref: ReferenceDataResponse,
        factory_dto: FactoryDTO | None,
    ) -> None:
        carding = factory_dto.carding_stages if factory_dto else []
        slots = ["Không", "Tỷ lệ của lượt", *[f"Tỷ lệ dây chuyền {line}" for line in carding]]
        slots += [s.blend_slot for s in ref.stages if s.blend_slot and s.blend_slot not in slots]
        stage_codes = [s.stage_code for s in ref.stages]
        rows = [
            {
                "Thứ tự": s.sequence,
                "Mã công đoạn": s.stage_code,
                "Tên công đoạn": s.stage_name,
                "Nhóm công đoạn": s.stage_group,
                "Đóng gói": s.is_packaging,
                "Hồi phế": s.recovery_type.value,
                "Chải thô": s.is_carding,
                "Số lượt tối đa": s.max_passes,
                "Ô tỷ lệ pha": s.blend_slot,
                "Công đoạn ghép": s.is_merge_stage,
                "Cách tính thứ cấp": s.secondary_method.value,
                "Công đoạn cộng lũy kế": list(s.cumulative_stages),
                "NSM đổi theo chi số": s.varies_with_count,
                "Nguồn định mức": s.rate_code_source.value,
            }
            for s in ref.stages
        ]
        edited = editable_table(
            rows,
            key=self.key(f"stages_grid.{factory}"),
            columns=list(STAGE_FIELDS),
            allow_add_delete=True,
            column_config={
                "Thứ tự": COL.NumberColumn("Thứ tự", min_value=1, step=1, format="%d", required=True),
                "Mã công đoạn": COL.TextColumn("Mã công đoạn", max_chars=20, required=True),
                "Tên công đoạn": COL.TextColumn("Tên công đoạn", max_chars=100),
                "Nhóm công đoạn": COL.TextColumn("Nhóm công đoạn", max_chars=20),
                "Đóng gói": COL.CheckboxColumn("Đóng gói", default=False),
                "Hồi phế": COL.SelectboxColumn("Hồi phế", options=list(RECOVERY_LABELS.values())),
                "Chải thô": COL.CheckboxColumn("Chải thô", default=False),
                "Số lượt tối đa": COL.NumberColumn("Số lượt tối đa", min_value=1, max_value=3, step=1, format="%d"),
                "Ô tỷ lệ pha": COL.SelectboxColumn("Ô tỷ lệ pha", options=list(dict.fromkeys(slots))),
                "Công đoạn ghép": COL.CheckboxColumn("Công đoạn ghép", default=False),
                "Cách tính thứ cấp": COL.SelectboxColumn(
                    "Cách tính thứ cấp", options=list(SECONDARY_METHOD_LABELS.values())
                ),
                "Công đoạn cộng lũy kế": COL.MultiselectColumn("Công đoạn cộng lũy kế", options=stage_codes),
                "NSM đổi theo chi số": COL.CheckboxColumn("NSM đổi theo chi số", default=False),
                "Nguồn định mức": COL.SelectboxColumn("Nguồn định mức", options=list(RATE_SOURCE_LABELS.values())),
            },
        )
        effective, reason = self._effective_inputs("stages", factory)
        stage_rows = [self._stage_row(row) for row in edited if _text(row.get("Mã công đoạn"))]
        self._recalc_button(
            "Lưu cấu hình và tính lại",
            "stages_save",
            "Xác nhận lưu cấu hình công đoạn",
            "Lưu cấu hình công đoạn của xưởng",
            factory,
            effective,
            lambda: feature.save_stage_config(
                SaveStageConfigRequest(
                    actor=actor or ActorDTO(),
                    factory_code=factory,
                    rows=stage_rows,
                    effective_date=effective,
                    reason=reason,
                )
            ),
            "UC-03",
        )

    @staticmethod
    def _stage_row(row: dict[str, Any]) -> StageRowDTO:
        values: dict[str, Any] = {
            "sequence": _int(row.get("Thứ tự")),
            "stage_code": _text(row.get("Mã công đoạn")),
            "stage_name": _text(row.get("Tên công đoạn")),
            "stage_group": _text(row.get("Nhóm công đoạn")),
            "is_packaging": bool(row.get("Đóng gói")),
            "is_carding": bool(row.get("Chải thô")),
            "max_passes": _int(row.get("Số lượt tối đa")),
            "is_merge_stage": bool(row.get("Công đoạn ghép")),
            "varies_with_count": bool(row.get("NSM đổi theo chi số")),
            "cumulative_stages": row.get("Công đoạn cộng lũy kế") or [],
        }
        if row.get("Hồi phế"):
            values["recovery_type"] = RecoveryType(row["Hồi phế"])
        if row.get("Ô tỷ lệ pha"):
            values["blend_slot"] = str(row["Ô tỷ lệ pha"])
        if row.get("Cách tính thứ cấp"):
            values["secondary_method"] = SecondaryMethod(row["Cách tính thứ cấp"])
        if row.get("Nguồn định mức"):
            values["rate_code_source"] = RateCodeSource(row["Nguồn định mức"])
        return StageRowDTO(**values)

    # ---- UC-04 ----
    def _rates_tab(
        self, feature: YarnCostingController, actor: ActorDTO | None, factory: str, ref: ReferenceDataResponse
    ) -> None:
        current = ref.current_rate
        if current is not None:
            st.caption(
                f"Phiên bản đang dùng: {current.version_code} · hiệu lực {fmt_date(current.effective_date)} · áp dụng "
                f"bởi {current.created_by or '-'} lúc {format_datetime(current.created_at)} · Lý do: {current.reason}"
            )
            lines = current.lines
        else:
            st.caption("Chưa có định mức.")
            codes = [s.stage_code for s in ref.stages if not s.is_packaging]
            codes += [p.code for p in ref.packaging if p.active and p.code not in codes]
            lines = [
                RateLineRowDTO(
                    rate_code=code,
                    labor=0,
                    depreciation=0,
                    electricity=0,
                    materials=0,
                    overhead=0,
                )
                for code in codes
            ]
        edited = editable_table(
            _rate_rows(lines),
            key=self.key(f"rates_grid.{factory}"),
            columns=RATE_COLUMNS,
            allow_add_delete=True,
            disabled=["Tổng (VND/phút)"],
            column_config=RATE_CONFIG,
        )
        st.caption("Đơn vị VND/phút. Cột Tổng do app tính sau khi áp dụng.")
        effective, reason = self._effective_inputs("rates", factory)
        rate_rows = [
            RateLineRowDTO(
                rate_code=_text(row.get("Mã định mức")),
                note=_text(row.get("Ghi chú")),
                **{field: optional_decimal(row.get(label)) for field, label in RATE_ITEMS},
            )
            for row in edited
            if _text(row.get("Mã định mức"))
        ]
        self._recalc_button(
            "Áp dụng định mức và tính lại toàn bộ",
            "rates_save",
            "Xác nhận áp dụng định mức mới",
            "Áp dụng định mức mới cho xưởng",
            factory,
            effective,
            lambda: feature.apply_rate_version(
                ApplyRateVersionRequest(
                    actor=actor or ActorDTO(),
                    factory_code=factory,
                    rows=rate_rows,
                    effective_date=effective,
                    reason=reason,
                )
            ),
            "UC-04",
        )
        section_title("Các phiên bản định mức")
        versions: list[RateVersionDTO] = ref.rate_versions
        picked = data_table(
            [
                {
                    "Mã phiên bản": v.version_code,
                    "Ngày hiệu lực": v.effective_date,
                    "Lý do": v.reason,
                    "Người áp dụng": v.created_by,
                    "Lúc áp dụng": v.created_at,
                    "Số dòng": len(v.lines),
                }
                for v in versions
            ],
            column_config={
                "Ngày hiệu lực": date_col("Ngày hiệu lực"),
                "Lúc áp dụng": datetime_col("Lúc áp dụng"),
                "Số dòng": count_col("Số dòng"),
            },
            selection="single",
            key=self.key(f"versions.{factory}"),
            empty_message="Chưa có phiên bản định mức nào.",
        )
        if picked:
            version = next((v for v in versions if v.version_code == picked[0]["Mã phiên bản"]), None)
            if version is not None:
                st.markdown(f"**Các dòng của phiên bản {version.version_code}**")
                data_table(
                    _rate_rows(version.lines),
                    column_config=RATE_CONFIG,
                    empty_message="Phiên bản này không có dòng nào.",
                    key=self.key(f"version_lines.{version.version_code}"),
                )

    # ---- UC-05 ----
    def _packaging_tab(
        self, feature: YarnCostingController, actor: ActorDTO | None, factory: str, ref: ReferenceDataResponse
    ) -> None:
        rows = [
            {
                "Mã loại": p.code,
                "Mặc định": p.is_default,
                "Tên loại đóng gói": p.name,
                "Khối lượng (kg)": plain(p.weight_kg),
                "Số công": plain(p.man_days),
                "Phút/kg": plain(p.minutes_per_kg),
                "Đang dùng": p.active,
                "Có định mức": p.has_rate,
            }
            for p in ref.packaging
        ]
        edited = editable_table(
            rows,
            key=self.key(f"packaging_grid.{factory}"),
            columns=PACKAGING_COLUMNS,
            allow_add_delete=True,
            disabled=["Có định mức"],
            column_config={
                "Mã loại": COL.TextColumn("Mã loại", required=True, max_chars=20),
                "Mặc định": COL.CheckboxColumn("Mặc định", default=False),
                "Tên loại đóng gói": COL.TextColumn("Tên loại đóng gói", max_chars=200),
                "Khối lượng (kg)": COL.NumberColumn("Khối lượng (kg)", min_value=0.0, format="localized"),
                "Số công": COL.NumberColumn("Số công", min_value=0.0, format="%.4f"),
                "Phút/kg": COL.NumberColumn("Phút/kg", min_value=0.0, format="%.4f", required=True),
                "Đang dùng": COL.CheckboxColumn("Đang dùng", default=True),
                "Có định mức": COL.CheckboxColumn("Có định mức"),
            },
        )
        st.caption(
            "Loại đóng gói mới cần có định mức chi phí/phút (thẻ Định mức) trước khi Sales chọn được. "
            'Tick "Mặc định" cho tối đa một loại: loại này được điền sẵn khi Sales tạo yêu cầu.'
        )
        effective, reason = self._effective_inputs("packaging", factory)
        packaging_rows = [
            PackagingRowDTO(
                code=_text(row.get("Mã loại")),
                name=_text(row.get("Tên loại đóng gói")),
                weight_kg=optional_decimal(row.get("Khối lượng (kg)")),
                man_days=optional_decimal(row.get("Số công")),
                minutes_per_kg=optional_decimal(row.get("Phút/kg")),
                active=row.get("Đang dùng") is not False,
                is_default=bool(row.get("Mặc định")),
            )
            for row in edited
            if _text(row.get("Mã loại"))
        ]
        st.caption(
            "Ngày hiệu lực và lý do chỉ bắt buộc khi Phút/kg của loại đang có mã sợi dùng thay đổi (app sẽ tính lại)."
        )
        self._packaging_save_button(feature, actor, factory, packaging_rows, effective, reason)

    def _packaging_save_button(
        self,
        feature: YarnCostingController,
        actor: ActorDTO | None,
        factory: str,
        rows: list[PackagingRowDTO],
        effective: date,
        reason: str,
    ) -> None:
        """UC-05 / BR-62: xem trước để hộp xác nhận ghi đúng có tính lại hay "Giá các mã không thay đổi."."""
        disabled, why = action_state(self.state, "UC-05")

        def request(preview: bool) -> SavePackagingTypesRequest:
            return SavePackagingTypesRequest(
                actor=actor or ActorDTO(),
                factory_code=factory,
                rows=rows,
                effective_date=effective,
                reason=reason,
                preview=preview,
            )

        if st.button("Lưu đóng gói", type="primary", key=self.key("packaging_save"), disabled=disabled, help=why):
            try:
                preview = feature.save_packaging_types(request(preview=True))
            except AppError as exc:
                show_error(exc)
            else:

                def action() -> str:
                    result = feature.save_packaging_types(request(preview=False))
                    batch_id = _batch_id(result)
                    if batch_id:
                        self.state.set(LAST_BATCH_KEY, batch_id)
                    return result.message

                confirm_dialog(
                    self.state,
                    self.key(f"dlg.packaging_save.{factory}"),
                    "Xác nhận lưu loại đóng gói",
                    f"Lưu loại đóng gói của xưởng {factory}? {preview.confirm_text}",
                    "Lưu và tính lại" if preview.will_recalculate else "Lưu đóng gói",
                    action,
                )
        explain(why)

    # ---- UC-06 ----
    def _recovery_tab(
        self, feature: YarnCostingController, actor: ActorDTO | None, factory: str, ref: ReferenceDataResponse
    ) -> None:
        by_type = {r.recovery_type: r.rate for r in ref.recovery}
        edited = editable_table(
            [{"Loại hồi phế": t.value, "Tỷ lệ (%)": pct(by_type.get(t))} for t in RECOVERY_ROWS],
            key=self.key(f"recovery_grid.{factory}"),
            columns=["Loại hồi phế", "Tỷ lệ (%)"],
            disabled=["Loại hồi phế"],
            column_config={
                "Tỷ lệ (%)": COL.NumberColumn("Tỷ lệ (%)", min_value=0.0, max_value=100.0, step=0.01, format="%.2f")
            },
        )
        effective, reason = self._effective_inputs("recovery", factory)
        recovery_rows = [
            RecoveryRowDTO(
                recovery_type=RecoveryType(row["Loại hồi phế"]),
                rate=None if row.get("Tỷ lệ (%)") is None else from_percent(row.get("Tỷ lệ (%)")),
            )
            for row in edited
            if row.get("Loại hồi phế")
        ]
        self._recalc_button(
            "Lưu hồi phế và tính lại",
            "recovery_save",
            "Xác nhận lưu hồi phế",
            "Lưu hồi phế của xưởng",
            factory,
            effective,
            lambda: feature.save_recovery_rates(
                SaveRecoveryRatesRequest(
                    actor=actor or ActorDTO(),
                    factory_code=factory,
                    rows=recovery_rows,
                    effective_date=effective,
                    reason=reason,
                )
            ),
            "UC-06",
        )

    # ---- UC-07 ----
    def _routes_tab(
        self, feature: YarnCostingController, actor: ActorDTO | None, factory: str, ref: ReferenceDataResponse
    ) -> None:
        rows = [
            {
                "Nhóm sợi": r.yarn_group,
                "Công nghệ": r.technology.value if r.technology else None,
                "Số thành phần": r.component_count,
                "Quy trình": r.route_text,
                "Công đoạn nhận ra": ", ".join(r.route_stages),
            }
            for r in ref.routes
        ]
        edited = editable_table(
            rows,
            key=self.key(f"routes_grid.{factory}"),
            columns=ROUTE_COLUMNS,
            allow_add_delete=True,
            disabled=["Công đoạn nhận ra"],
            column_config={
                "Nhóm sợi": COL.TextColumn("Nhóm sợi", required=True, max_chars=200),
                "Công nghệ": COL.SelectboxColumn("Công nghệ", options=list(TECHNOLOGY_LABELS.values()), required=True),
                "Số thành phần": COL.NumberColumn("Số thành phần", min_value=1, max_value=5, step=1, format="%d"),
                "Quy trình": COL.TextColumn(
                    "Quy trình",
                    max_chars=500,
                    help="Ví dụ: B2 - C1 - C2 - SBD - PD - LF - CM - MD1 - MD2 - MD3 - R - S - W - F",
                ),
                "Công đoạn nhận ra": COL.TextColumn("Công đoạn nhận ra"),
            },
        )
        disabled, why = action_state(self.state, "UC-07")
        if st.button("Lưu quy trình", type="primary", key=self.key("routes_save"), disabled=disabled, help=why):
            result = feature.save_process_routes(
                SaveProcessRoutesRequest(
                    actor=actor or ActorDTO(),
                    factory_code=factory,
                    rows=[
                        ProcessRouteRowDTO(
                            yarn_group=_text(row.get("Nhóm sợi")),
                            technology=Technology(row["Công nghệ"]) if row.get("Công nghệ") else None,
                            component_count=_int(row.get("Số thành phần")),
                            route_text=_text(row.get("Quy trình")),
                        )
                        for row in edited
                        if _text(row.get("Nhóm sợi")) or _text(row.get("Quy trình"))
                    ],
                )
            )
            set_flash(self.state, result.message)
            st.rerun()
        explain(why)

    # ---- UC-08 / UC-09 ----
    def _exchange_tab(
        self, feature: YarnCostingController, actor: ActorDTO | None, reference: ReferenceDataResponse
    ) -> None:
        st.caption("Tỷ giá và hệ số thí nghiệm dùng chung cho S1 và S4.")
        current = reference.current_exchange_rate
        with panel("Tỷ giá", icon="💱"):
            if current is not None:
                st.info(
                    f"Tỷ giá đang dùng: {format_number(current.rate)} VND/USD từ {fmt_date(current.effective_date)}"
                )
            else:
                st.info("Chưa có tỷ giá.")
            data_table(
                [
                    {
                        "Ngày áp dụng": r.effective_date,
                        "Tỷ giá": plain(r.rate),
                        "Ghi chú": r.note,
                        "Người nhập": r.created_by,
                        "Lúc nhập": r.created_at,
                    }
                    for r in reference.exchange_rates
                ],
                column_config={
                    "Ngày áp dụng": date_col("Ngày áp dụng"),
                    "Tỷ giá": money("Tỷ giá"),
                    "Lúc nhập": datetime_col("Lúc nhập"),
                },
                empty_message="Chưa có tỷ giá nào.",
                key=self.key("rates_table"),
            )
            disabled, why = action_state(self.state, "UC-08")
            with st.form(self.key("rate_form")):
                c1, c2, c3 = st.columns([1, 1, 2])
                effective = c1.date_input(
                    "Ngày áp dụng", value=date.today(), format="DD/MM/YYYY", key=self.key("rate.eff")
                )
                rate = c2.number_input(
                    "Tỷ giá (VND/USD)",
                    min_value=0.0,
                    value=float(current.rate) if current else 0.0,
                    step=100.0,
                    format="%.2f",
                    key=self.key("rate.value"),
                )
                note = c3.text_input("Ghi chú", max_chars=200, key=self.key("rate.note"))
                if st.form_submit_button("Thêm tỷ giá", type="primary", disabled=disabled, help=why):
                    result = feature.add_exchange_rate(
                        AddExchangeRateRequest(
                            actor=actor or ActorDTO(), effective_date=effective, rate=to_decimal(rate), note=note
                        )
                    )
                    set_flash(self.state, result.message)
                    st.rerun()
            explain(why)

        with panel("Hệ số thí nghiệm", icon="🧪"):
            old_factor = float(reference.trial_factor)
            c1, c2, c3 = st.columns([1, 1, 2])
            factor = c1.number_input(
                "Hệ số thí nghiệm",
                min_value=0.0,
                value=old_factor,
                step=0.1,
                format="%.2f",
                key=self.key("trial_factor"),
            )
            effective = c2.date_input(
                "Ngày hiệu lực", value=date.today(), format="DD/MM/YYYY", key=self.key("trial.eff")
            )
            reason = c3.text_input("Lý do", max_chars=500, key=self.key("trial.reason"))
            disabled, why = action_state(self.state, "UC-09")
            if st.button("Lưu hệ số", type="primary", key=self.key("trial_save"), disabled=disabled, help=why):
                request = UpdateTrialFactorRequest(
                    actor=actor or ActorDTO(), trial_factor=to_decimal(factor), effective_date=effective, reason=reason
                )

                def action() -> str:
                    result = feature.update_trial_factor(request)
                    batch_id = _batch_id(result)
                    if batch_id:
                        self.state.set(LAST_BATCH_KEY, batch_id)
                    return result.message

                confirm_dialog(
                    self.state,
                    self.key("dlg.trial"),
                    "Xác nhận đổi hệ số thí nghiệm",
                    f"Đổi hệ số thí nghiệm từ {format_number(old_factor, 2)} thành {format_number(factor, 2)}? App sẽ "
                    "cập nhật dòng thí nghiệm của mọi mã ở cả hai xưởng (kể cả mã đã có mã kế toán).",
                    "Lưu hệ số",
                    action,
                )
            explain(why)

    # ---- UC-36 / UC-37 ----
    # ---- UC-43 ----
    def _not_priced_block(self, feature: YarnCostingController, actor: ActorDTO | None, factory: str) -> None:
        section_title("Tính lại các mã chưa tính được", "🔄")
        st.caption(
            "Tính lại ngay các mã đang 'Chưa tính được' của xưởng (ví dụ sau khi app dùng được tiêu hao của dây chuyền "
            "tương đương C2 ↔ C3 / C1 ↔ C2). Các mã đã có giá không bị tính lại."
        )
        effective, reason = self._effective_inputs("not_priced", factory)
        disabled, why = action_state(self.state, "UC-43")
        if st.button(
            "Tính lại các mã chưa tính được",
            type="primary",
            key=self.key(f"not_priced.{factory}"),
            disabled=disabled,
            help=why,
        ):

            def action() -> str:
                result = feature.recalculate_not_priced(
                    RecalculateNotPricedRequest(
                        actor=actor or ActorDTO(), factory_code=factory, effective_date=effective, reason=reason
                    )
                )
                batch_id = _batch_id(result)
                if batch_id:
                    self.state.set(LAST_BATCH_KEY, batch_id)
                return result.message

            confirm_dialog(
                self.state,
                self.key(f"dlg.not_priced.{factory}"),
                "Xác nhận tính lại các mã chưa tính được",
                f"Tính lại các mã đang 'Chưa tính được' của xưởng {factory} với ngày hiệu lực {fmt_date(effective)}? "
                "Các mã đã có giá không bị tính lại.",
                "Tính lại",
                action,
            )
        explain(why)

    def _batches_tab(self, feature: YarnCostingController, actor: ActorDTO | None, factory: str) -> None:
        self._not_priced_block(feature, actor, factory)
        batches = feature.list_recalc_batches(ListRecalcBatchesRequest(factory_code=factory))
        picked = data_table(
            batch_rows(batches.items),
            column_config=BATCH_CONFIG,
            selection="single",
            key=self.key(f"batches.{factory}"),
            empty_message="Chưa có lần tính lại nào.",
        )
        if picked:
            batch_id = str(picked[0]["Mã lần tính lại"])
            section_title(f"Chênh lệch lần tính lại {batch_id}", "🔁")
            render_recalc_diff(feature, batch_id, self.key(f"diff.{batch_id}"))
