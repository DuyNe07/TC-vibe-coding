"""Công thức tính giá: BR-13 công đoạn hiển thị, BR-14..BR-16 kiểm tra khớp, BR-17..BR-21 chi phí, BR-22 USD,
BR-58 tiêu hao của lượt chải thô, BR-64 dây chuyền tương đương."""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.yarn_costing.constants import EQUIVALENT_CARDING
from backend.features.yarn_costing.models.costing import CostResult, FactoryData
from backend.features.yarn_costing.models.enums import RateCodeSource, RecoveryType, SecondaryMethod, Technology
from backend.features.yarn_costing.models.exchange_rate import ExchangeRate
from backend.features.yarn_costing.models.loss_group import LossComponent, LossGroup
from backend.features.yarn_costing.models.packaging_type import PackagingType
from backend.features.yarn_costing.models.rate_version import RateLine
from backend.features.yarn_costing.models.stage import Stage
from backend.features.yarn_costing.models.yarn import CostBreakdown, StageCostDetail, Yarn, YarnComponent
from backend.shared.utils import normalize_key

ZERO = Decimal(0)
ONE = Decimal(1)
MINUTES_PER_HOUR = Decimal(60)


def same_material(a: str, b: str) -> bool:
    return normalize_key(a) == normalize_key(b)


class CostingBusiness(BaseBusiness[Yarn]):
    # ---- BR-13 ---------------------------------------------------------------------------------------------------
    def route_stage_codes(self, route_text: str, stages: Sequence[Stage]) -> list[str]:
        """BR-13: tách quy trình theo '-', khớp mã công đoạn (C3.1 / C3.2 / C3.3 → C3, S → S và S Compact), bỏ bước
        lạ, F luôn có."""
        steps = [step.strip().upper() for step in (route_text or "").split("-") if step.strip()]
        matched: set[str] = set()
        for step in steps:
            for stage in stages:
                code = stage.stage_code.upper()
                if (
                    code == step
                    or step.startswith(code + ".")
                    or code.startswith(step + ".")
                    or code == f"{step} COMPACT"
                ):
                    matched.add(stage.stage_code)
        matched |= {s.stage_code for s in stages if s.is_packaging}
        return [s.stage_code for s in sorted(stages, key=lambda s: s.sequence) if s.stage_code in matched]

    def visible_stages(
        self, data: FactoryData, yarn_group: str, technology: Technology, nsm: dict[str, Decimal]
    ) -> list[Stage]:
        """BR-13: công đoạn hiển thị để nhập NSM (theo quy trình; không có quy trình → mọi công đoạn; + công đoạn có NSM)."""
        route = next(
            (r for r in data.routes if r.yarn_group.upper() == yarn_group.upper() and r.technology == technology), None
        )
        stages = sorted(data.stages, key=lambda s: s.sequence)
        if route is None or not route.route_text.strip():
            return stages
        codes = set(self.route_stage_codes(route.route_text, stages))
        codes |= {code for code, value in nsm.items() if value > 0}
        return [s for s in stages if s.stage_code in codes]

    # ---- BR-58 ---------------------------------------------------------------------------------------------------
    def group_component(
        self, group: LossGroup, material_label: str, groups: dict[str, LossGroup]
    ) -> tuple[LossComponent, LossGroup | None] | None:
        """The component of a secondary loss group whose material is ``material_label`` (4.12.1 / BR-57)."""
        for component in group.components:
            source = groups.get(component.component_group_key)
            names = [component.component_group_key]
            if source is not None:
                names += [source.material_label, source.material_tech_key, source.group_key]
            if any(same_material(material_label, n) for n in names):
                return component, source
        return None

    def equivalent_line(self, factory_code: str, stage_code: str) -> str | None:
        """BR-64: dây chuyền tương đương (S4 C2 ↔ C3; S1 C1 ↔ C2; S4 C1 không có)."""
        return EQUIVALENT_CARDING.get(factory_code, {}).get(stage_code)

    def declared_carding_loss(self, group: LossGroup, stage_code: str, factory_code: str) -> tuple[Decimal, str]:
        """BR-64: tiêu hao khai báo tại X; nếu X = 0 / trống và dây chuyền tương đương Y có tiêu hao > 0 → dùng số của Y.

        Trả về (tiêu hao, dây chuyền nguồn); dây chuyền nguồn = "" khi lấy đúng X."""
        loss = group.loss_at(stage_code)
        if loss > 0:
            return loss, ""
        other = self.equivalent_line(factory_code, stage_code)
        if other is not None and group.loss_at(other) > 0:
            return group.loss_at(other), other
        return loss, ""

    def pass_loss_with_source(
        self, yarn: Yarn, component: YarnComponent, stage: Stage, data: FactoryData
    ) -> tuple[Decimal | None, str]:
        """BR-58: tiêu hao của lượt (nguyên liệu M chạy dây chuyền X): M là thành phần của nhóm tiêu hao → tiêu hao của
        nhóm thành phần M tại X (Cộng thẳng) hoặc × tỷ lệ của M trong nhóm (Bình quân); nhóm không có thành phần → tiêu
        hao của nhóm tại X, chỉ khi X có đúng 1 lượt (None = chưa xác định được). "Tiêu hao tại X" theo BR-64."""
        group = data.loss_groups.get(yarn.loss_group_key)
        if group is None:
            return None, ""
        factory = data.factory_code.value
        if group.components:
            match = self.group_component(group, component.material_label, data.loss_groups)
            if match is None or match[1] is None:
                return ZERO, ""
            item, source = match
            loss, origin = self.declared_carding_loss(source, stage.stage_code, factory)  # type: ignore[arg-type]
            return (loss * item.ratio if stage.secondary_method == SecondaryMethod.BINH_QUAN else loss), origin
        if len(yarn.passes_on(stage.stage_code)) != 1:
            return None, ""
        return self.declared_carding_loss(group, stage.stage_code, factory)

    def pass_loss(self, yarn: Yarn, component: YarnComponent, stage: Stage, data: FactoryData) -> Decimal | None:
        """BR-58 (+ BR-64): tiêu hao của lượt chải thô (None = chưa xác định được)."""
        return self.pass_loss_with_source(yarn, component, stage, data)[0]

    # ---- BR-15 / BR-16 -------------------------------------------------------------------------------------------
    def rate_code_for(self, stage: Stage, yarn: Yarn) -> str | None:
        if stage.rate_code_source == RateCodeSource.LOAI_DONG_GOI or stage.is_packaging:
            return yarn.packaging_code
        return stage.stage_code

    def _carding_reasons(self, yarn: Yarn, stage: Stage, data: FactoryData, has_group: bool) -> list[str]:
        reasons: list[str] = []
        code = stage.stage_code
        for number, component in enumerate(yarn.passes_on(code), start=1):
            nsm = component.nsm_value
            if nsm > 0 and code not in data.rates:
                message = f"Chưa có định mức chi phí/phút cho {code}."
                if message not in reasons:
                    reasons.append(message)
            if not has_group:
                continue
            loss = self.pass_loss(yarn, component, stage, data)
            label = f"{code} lượt {number} ({component.material_label})"
            if loss is None:
                message = (
                    f"{code}: nhóm tiêu hao chưa khai báo thành phần nên chưa xác định được tiêu hao từng lượt. "
                    "Vui lòng khai báo thành phần cho nhóm tiêu hao."
                )
                if message not in reasons:
                    reasons.append(message)
            elif nsm > 0 and loss <= 0:
                other = self.equivalent_line(data.factory_code.value, code)
                if other is None:
                    reasons.append(
                        f"{label}: có NSM nhưng nguyên liệu chưa khai báo tiêu hao ở {code}. "
                        "Vui lòng khai báo tiêu hao chải thô của nguyên liệu ở dây chuyền này."
                    )
                else:  # BR-16 / BR-64: neither the running line nor its equivalent has a loss
                    reasons.append(
                        f"{label}: có NSM nhưng nguyên liệu chưa khai báo tiêu hao ở {code} hoặc {other}. "
                        "Vui lòng khai báo tiêu hao chải thô của nguyên liệu."
                    )
            elif nsm <= 0 and loss > 0:
                reasons.append(f"{label}: có tiêu hao nhưng chưa nhập NSM.")
        return reasons

    def missing_materials(self, yarn: Yarn, group: LossGroup, data: FactoryData) -> list[str]:
        """BR-15: mỗi thành phần của nhóm tiêu hao có tiêu hao chải thô phải có dòng thành phần trong sợi."""
        codes = data.carding_codes
        if not group.components:
            if group.carding_lines_with_loss(codes) and not any(c.carding_stage for c in yarn.components):
                return [group.material_label]
            return []
        missing = []
        for component in group.components:
            source = data.loss_groups.get(component.component_group_key)
            if source is None or not source.carding_lines_with_loss(codes):
                continue
            names = [component.component_group_key, source.material_label, source.material_tech_key]
            if not any(same_material(c.material_label, n) for c in yarn.components for n in names):
                missing.append(source.material_label)
        return missing

    def check_match(self, yarn: Yarn, data: FactoryData) -> list[str]:
        """BR-15: có nhóm tiêu hao; công đoạn không phải chải thô, không ghép: (NSM>0 và tiêu hao>0) hoặc (cả hai = 0);
        mỗi lượt chải thô: (NSM chải thô>0 và tiêu hao của lượt>0) hoặc (cả hai = 0); nguyên liệu có tiêu hao chải thô
        phải có dòng thành phần; đủ định mức.

        BR-16: trả về các lý do "Chưa tính được" (danh sách rỗng = đạt).
        """
        reasons: list[str] = []
        group = data.loss_groups.get(yarn.loss_group_key)
        if group is None:
            reasons.append(
                f"Chưa có nhóm tiêu hao '{yarn.loss_group_key}' ở xưởng {data.factory_code.value}. "
                "Vui lòng khai báo tiêu hao."
            )
        for stage in sorted(data.stages, key=lambda s: s.sequence):
            if stage.is_packaging:
                continue
            if stage.is_carding:
                reasons += self._carding_reasons(yarn, stage, data, group is not None)
                continue
            nsm = yarn.nsm_at(stage.stage_code)
            if group is not None and not stage.is_merge_stage:
                loss = group.loss_at(stage.stage_code)
                if nsm > 0 and loss <= 0:
                    reasons.append(f"Công đoạn {stage.stage_code}: có NSM nhưng nhóm tiêu hao không có tiêu hao.")
                elif nsm <= 0 and loss > 0:
                    reasons.append(f"Công đoạn {stage.stage_code}: nhóm tiêu hao có tiêu hao nhưng chưa nhập NSM.")
            if nsm > 0 and stage.stage_code not in data.rates:
                reasons.append(f"Chưa có định mức chi phí/phút cho {stage.stage_code}.")
        if group is not None:
            reasons += [
                f"Nguyên liệu {m} có tiêu hao chải thô nhưng chưa có dòng thành phần trong sợi."
                for m in self.missing_materials(yarn, group, data)
            ]
        if not yarn.packaging_code or yarn.packaging_code not in data.packaging:
            reasons.append("Chưa có loại đóng gói.")
        elif yarn.packaging_code not in data.rates:
            reasons.append(f"Chưa có định mức chi phí/phút cho {yarn.packaging_code}.")
        return reasons

    # ---- BR-17..BR-21 --------------------------------------------------------------------------------------------
    def stage_ratio(self, stage: Stage, yarn: Yarn, component: YarnComponent | None = None) -> Decimal:
        """BR-17: 'Tỷ lệ của lượt' = tỷ lệ của thành phần; 'Tỷ lệ dây chuyền X' = tỷ lệ dây chuyền X; 'Không' = 1."""
        if stage.uses_pass_ratio:
            return component.ratio if component is not None else ONE
        line = stage.ratio_line
        if line is not None:
            return yarn.line_ratio(line)
        return ONE

    def run_minutes(self, stage: Stage, nsm: Decimal, recovery: dict[str, Decimal], ratio: Decimal) -> Decimal:
        """BR-17: 0 nếu NSM = 0; ngược lại 60 ÷ NSM × (1 + hồi phế) × tỷ lệ theo blend_slot."""
        if nsm <= 0:
            return ZERO
        recovery_rate = (
            ZERO if stage.recovery_type == RecoveryType.KHONG else recovery.get(stage.recovery_type.value, ZERO)
        )
        return MINUTES_PER_HOUR / nsm * (ONE + recovery_rate) * ratio

    def packaging_minutes(self, packaging: PackagingType) -> Decimal:
        """BR-18: thời gian đóng gói = phút/kg của loại đóng gói; tiêu hao và tiêu hao lũy kế của F = 0."""
        return packaging.minutes_per_kg

    def cumulative_loss(
        self, stage: Stage, group: LossGroup, minutes: Decimal, own_loss: Decimal | None = None
    ) -> Decimal:
        """BR-19: 0 nếu thời gian = 0; ngược lại tiêu hao của X (lượt chải thô: tiêu hao của lượt, BR-58) + tổng tiêu
        hao của nhóm tại các công đoạn trong cumulative_stages của X."""
        if minutes <= 0:
            return ZERO
        own = group.loss_at(stage.stage_code) if own_loss is None else own_loss
        return own + sum((group.loss_at(code) for code in stage.cumulative_stages), ZERO)

    def stage_cost(self, rate: RateLine, minutes: Decimal, cumulative: Decimal) -> CostBreakdown:
        """BR-20: chi phí khoản K (VND/kg) = định mức K × thời gian ÷ (1 − tiêu hao lũy kế)."""
        factor = minutes / (ONE - cumulative)
        return CostBreakdown(
            labor=rate.labor * factor,
            depreciation=rate.depreciation * factor,
            electricity=rate.electricity * factor,
            materials=rate.materials * factor,
            overhead=rate.overhead * factor,
        )

    def sum_costs(self, costs: Sequence[CostBreakdown]) -> CostBreakdown:
        """BR-21: mỗi khoản = tổng khoản đó qua mọi công đoạn, giữ đủ chữ số thập phân (không làm tròn trung gian)."""
        return CostBreakdown(
            labor=sum((c.labor for c in costs), ZERO),
            depreciation=sum((c.depreciation for c in costs), ZERO),
            electricity=sum((c.electricity for c in costs), ZERO),
            materials=sum((c.materials for c in costs), ZERO),
            overhead=sum((c.overhead for c in costs), ZERO),
        )

    def _detail(
        self,
        stage: Stage,
        rate: RateLine,
        minutes: Decimal,
        loss: Decimal,
        cumulative: Decimal,
        nsm: Decimal | None,
        component: YarnComponent | None = None,
        pass_no: int | None = None,
        loss_source_stage: str = "",
    ) -> StageCostDetail:
        return StageCostDetail(
            sequence=stage.sequence,
            stage_code=stage.stage_code,
            stage_name=stage.stage_name,
            material_label=component.material_label if component is not None else "",
            pass_no=pass_no,
            nsm=nsm,
            run_minutes=minutes,
            loss=loss,
            loss_source_stage=loss_source_stage,
            cumulative_loss=cumulative,
            total_rate=rate.total_rate,
            cost=self.stage_cost(rate, minutes, cumulative),
        )

    def calculate(self, yarn: Yarn, data: FactoryData) -> CostResult:
        """BR-14: chỉ tính khi kiểm tra khớp đạt; BR-17..BR-21 cho mọi công đoạn có thời gian > 0 (kể cả đóng gói),
        dây chuyền chải thô: mỗi lượt một dòng (BR-19, BR-58)."""
        reasons = self.check_match(yarn, data)
        if reasons:
            return CostResult(passed=False, reasons=reasons)
        group = data.loss_groups[yarn.loss_group_key]
        details: list[StageCostDetail] = []
        for stage in sorted(data.stages, key=lambda s: s.sequence):
            if stage.is_packaging:
                packaging = data.packaging[yarn.packaging_code or ""]
                minutes = self.packaging_minutes(packaging)
                if minutes > 0:
                    rate = data.rates[self.rate_code_for(stage, yarn) or ""]
                    details.append(self._detail(stage, rate, minutes, ZERO, ZERO, None))
                continue
            if stage.is_carding:
                for number, component in enumerate(yarn.passes_on(stage.stage_code), start=1):
                    ratio = self.stage_ratio(stage, yarn, component)
                    minutes = self.run_minutes(stage, component.nsm_value, data.recovery, ratio)
                    if minutes <= 0:
                        continue
                    pass_loss, origin = self.pass_loss_with_source(yarn, component, stage, data)
                    loss = pass_loss or ZERO
                    cumulative = self.cumulative_loss(stage, group, minutes, loss)
                    rate = data.rates[stage.stage_code]
                    details.append(
                        self._detail(
                            stage, rate, minutes, loss, cumulative, component.nsm_value, component, number, origin
                        )
                    )
                continue
            nsm = yarn.nsm_at(stage.stage_code)
            minutes = self.run_minutes(stage, nsm, data.recovery, self.stage_ratio(stage, yarn))
            if minutes <= 0:
                continue
            rate = data.rates[self.rate_code_for(stage, yarn) or ""]
            loss = group.loss_at(stage.stage_code)
            details.append(self._detail(stage, rate, minutes, loss, self.cumulative_loss(stage, group, minutes), nsm))
        return CostResult(passed=True, details=details, cost=self.sum_costs([d.cost for d in details]))

    # ---- BR-22 ---------------------------------------------------------------------------------------------------
    def current_exchange_rate(self, rates: Sequence[ExchangeRate], today: date) -> ExchangeRate | None:
        """BR-22 / 4.9: tỷ giá đang dùng = ngày áp dụng lớn nhất ≤ hôm nay (cùng ngày: dòng nhập sau cùng)."""
        valid = [r for r in rates if r.effective_date <= today]
        return max(valid, key=lambda r: (r.effective_date, r.created_at), default=None)

    def usd_per_kg(self, total_vnd: Decimal, rate: ExchangeRate | None) -> Decimal | None:
        """BR-22: USD/kg = Tổng VND/kg ÷ tỷ giá đang dùng (đổi tỷ giá không đổi giá VND)."""
        return total_vnd / rate.rate if rate is not None else None
