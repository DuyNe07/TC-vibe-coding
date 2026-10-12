"""UC-21 / UC-23 / UC-24 workflow: check the entered NSM (BR-09..BR-12, BR-32, BR-33), compare with the reference yarn
(BR-37, BR-38) and calculate (BR-14..BR-21) without storing anything."""

from collections.abc import Sequence
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.yarn_costing.business.analysis_business import AnalysisBusiness
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.business.display_business import format_usd, format_vnd
from backend.features.yarn_costing.business.nsm_business import COMPACT_STAGE, NsmInputBusiness, number_passes
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.costing import FactoryData, NsmInput, PricingPreview
from backend.features.yarn_costing.models.enums import LossGroupLevel, YarnStatus
from backend.features.yarn_costing.models.yarn import Yarn, YarnComponent

EDITABLE_STATUSES = (
    YarnStatus.CHO_XUONG_XEM,
    YarnStatus.CHUA_TINH_DUOC,
    YarnStatus.DA_TINH_GIA,
    YarnStatus.CO_MA_KE_TOAN,
)
PRICED = (YarnStatus.DA_TINH_GIA, YarnStatus.CO_MA_KE_TOAN)


class PricingBusiness(BaseBusiness[Yarn]):
    def __init__(self) -> None:
        self.inputs = NsmInputBusiness()
        self.analysis = AnalysisBusiness()
        self.costing = CostingBusiness()

    def packaging_valid(self, yarn: Yarn, data: FactoryData) -> bool:
        """BR-12: loại đóng gói có ở xưởng, đang hoạt động và có định mức."""
        packaging = data.packaging.get(yarn.packaging_code or "")
        return packaging is not None and packaging.active and packaging.code in data.rates

    def ensure_status(self, yarn: Yarn) -> None:
        if yarn.status not in EDITABLE_STATUSES:
            raise YarnValidationError(
                f"Mã {yarn.yarn_code} đang ở trạng thái '{yarn.status.value}' nên không nhập NSM được."
            )

    def material_options(self, yarn: Yarn, data: FactoryData) -> list[str]:
        """BR-57: nhóm Thứ cấp → material_tech_key của các thành phần; nhóm Sơ cấp (một nguyên liệu) → nguyên liệu của
        nhóm; nhóm chưa có / chưa khai báo thành phần → nhập tự do (danh sách rỗng)."""
        group = data.loss_groups.get(yarn.loss_group_key)
        if group is None:
            return []
        if group.components:
            options = []
            for component in group.components:
                source = data.loss_groups.get(component.component_group_key)
                options.append(source.material_label if source else component.component_group_key)
            return options
        single = len(group.carding_lines_with_loss(data.carding_codes)) <= 1
        if group.level == LossGroupLevel.SO_CAP and group.material.strip() and single:
            return [group.material_label]
        return []

    def default_components(self, yarn: Yarn, data: FactoryData) -> list[YarnComponent]:
        """4.12.1 / UC-21: dòng điền sẵn theo thành phần của nhóm tiêu hao (Thứ cấp: mỗi thành phần một dòng; Sơ cấp: một
        dòng); dây chuyền mặc định = dây chuyền có tiêu hao chải thô (nhiều: sequence nhỏ nhất)."""
        group = data.loss_groups.get(yarn.loss_group_key)
        if group is None:
            return []
        codes = data.carding_codes
        rows: list[YarnComponent] = []
        if group.components:
            for component in group.components:
                source = data.loss_groups.get(component.component_group_key)
                lines = source.carding_lines_with_loss(codes) if source else []
                rows.append(
                    YarnComponent(
                        material_label=(source.material_label if source else component.component_group_key)[:200],
                        ratio=component.ratio,
                        carding_stage=lines[0] if lines else "",
                    )
                )
        elif options := self.material_options(yarn, data):
            lines = group.carding_lines_with_loss(codes)
            rows.append(
                YarnComponent(
                    material_label=options[0][:200], ratio=Decimal(1), carding_stage=lines[0] if lines else ""
                )
            )
        return number_passes(rows)

    def nsm_input(self, yarn: Yarn, data: FactoryData, **extra: object) -> NsmInput:
        return NsmInput(
            yarn_code=yarn.yarn_code,
            components=yarn.components,
            nsm=yarn.nsm,
            max_passes={s.stage_code: s.pass_limit for s in data.carding_stages},
            group_key=yarn.loss_group_key,
            material_options=self.material_options(yarn, data),
            is_compact=yarn.is_compact,
            has_compact_stage=data.stage(COMPACT_STAGE) is not None,
            packaging_valid=self.packaging_valid(yarn, data),
            is_locked=yarn.is_locked,
            **extra,  # type: ignore[arg-type]
        )

    def ensure_carding_lines(self, components: Sequence[YarnComponent], data: FactoryData) -> None:
        codes = set(data.carding_codes)
        wrong = next((c.carding_stage for c in components if c.carding_stage and c.carding_stage not in codes), None)
        if wrong is not None:
            raise YarnValidationError(f"Dây chuyền chải thô '{wrong}' không có ở xưởng {data.factory_code.value}.")

    def preview(
        self,
        yarn: Yarn,
        components: Sequence[YarnComponent],
        nsm: dict[str, Decimal],
        data: FactoryData,
        yarns: Sequence[Yarn],
        reference_code: str | None = None,
        adjust_reason: str | None = None,
    ) -> PricingPreview:
        """Checks of UC-21 (BR-32 unless it is a ĐCNSM, BR-09..BR-12, BR-56, BR-57, BR-33 for ĐCNSM) then the
        calculation (BR-14..BR-21, BR-58)."""
        self.ensure_carding_lines(components, data)
        numbered = number_passes(components)
        carding = set(data.carding_codes)
        values = {k: v for k, v in nsm.items() if v is not None and k not in carding}
        candidate = yarn.model_copy(update={"components": numbered, "nsm": {k: v for k, v in values.items() if v != 0}})
        check = self.nsm_input(candidate, data, adjust_reason=adjust_reason or "")
        check = check.model_copy(update={"nsm": values})
        if adjust_reason is None:
            self.inputs.ensure_editable(check)
        else:
            self.inputs.ensure_adjust_reason(check)
        self.inputs.ensure_valid(check)
        reference = None
        if reference_code:
            reference = next(
                (
                    y
                    for y in yarns
                    if y.yarn_code == reference_code and y.status in PRICED and y.yarn_code != yarn.yarn_code
                ),
                None,
            )
        reference = reference or self.analysis.reference_yarn(candidate, yarns)
        warnings = self.analysis.warning_stages(candidate, reference, data.stages)
        return PricingPreview(
            candidate=candidate,
            result=self.costing.calculate(candidate, data),
            reference_yarn_code=reference.yarn_code if reference else None,
            warning_stages=warnings,
        )

    def message(self, preview: PricingPreview, rate: Decimal | None, saved: bool, code: str | None = None) -> str:
        """UC-21 / UC-24 outputs with VND / USD rounded for display (BR-23)."""
        code = code or preview.candidate.yarn_code
        result = preview.result
        if not result.passed:
            reasons = " ".join(result.reasons)
            return (
                f"Đã lưu NSM {code} nhưng chưa tính được giá: {reasons}" if saved else f"Chưa tính được giá: {reasons}"
            )
        total = result.cost.total
        usd = f" ({format_usd(total / rate)} USD/kg)" if rate else ""
        if saved:
            return f"Đã lưu giá {code}: {format_vnd(total)} VND/kg{usd}."
        warning = ""
        if preview.warning_stages:
            warning = (
                f" NSM khác sợi cùng nhóm ({preview.reference_yarn_code}) ở công đoạn: {', '.join(preview.warning_stages)}. "
                "Vui lòng nhập lý do trước khi lưu."
            )
        return f"Kiểm tra đạt: {format_vnd(total)} VND/kg{usd}.{warning}"

    def ensure_can_save(self, preview: PricingPreview, warning_reason: str) -> None:
        """BR-38: NSM khác sợi so sánh → phải nhập lý do mới lưu được."""
        self.inputs.ensure_warning_reason(
            NsmInput(
                yarn_code=preview.candidate.yarn_code,
                warning_stages=preview.warning_stages,
                reference_yarn_code=preview.reference_yarn_code or "",
                warning_reason=warning_reason,
            )
        )
