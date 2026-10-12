"""Kiểm tra đầu vào NSM: BR-09 tỷ lệ pha, BR-10 NSM, BR-11 compact, BR-12 đóng gói, BR-32 khoá, BR-33, BR-38,
BR-56 lượt chải thô, BR-57 nguyên liệu của nhóm tiêu hao."""

from collections import Counter
from collections.abc import Sequence
from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.yarn_costing.business.display_business import format_percent
from backend.features.yarn_costing.constants import PACKAGING_STAGE_CODE, RATIO_TOLERANCE
from backend.features.yarn_costing.models.costing import NsmInput
from backend.features.yarn_costing.models.yarn import YarnComponent
from backend.shared.utils import normalize_key

COMPACT_STAGE = "S Compact"
NORMAL_SPIN_STAGE = "S"


class BlendRatioRule(BaseBusinessRule[NsmInput]):
    code = "BR-09"
    message = "Tổng tỷ lệ pha phải bằng 100%."
    field = "components"

    def total(self, target: NsmInput) -> Decimal:
        return sum((c.ratio for c in target.components), Decimal(0))

    def is_satisfied_by(self, target: NsmInput) -> bool:
        each_ok = all(Decimal(0) <= c.ratio <= Decimal(1) for c in target.components)
        return each_ok and abs(self.total(target) - Decimal(1)) <= RATIO_TOLERANCE

    def describe_violation(self, target: NsmInput) -> str:
        return f"Tổng tỷ lệ pha phải bằng 100% (hiện là {format_percent(self.total(target))}%)."


class NsmValuesRule(BaseBusinessRule[NsmInput]):
    code = "BR-10"
    message = "NSM phải là số ≥ 0 và cần nhập ít nhất một công đoạn."
    field = "nsm"

    def is_satisfied_by(self, target: NsmInput) -> bool:
        values_ok = all(v >= 0 for v in target.nsm.values()) and all(c.nsm_value >= 0 for c in target.components)
        carding = any(c.carding_stage and c.nsm_value > 0 for c in target.components)
        return values_ok and (carding or any(v > 0 for code, v in target.nsm.items() if code != PACKAGING_STAGE_CODE))


class CompactStageRule(BaseBusinessRule[NsmInput]):
    code = "BR-11"
    message = "Sợi compact phải nhập NSM ở công đoạn 'S Compact' (sợi thường nhập ở 'S')."
    field = "nsm"

    def is_satisfied_by(self, target: NsmInput) -> bool:
        if not target.has_compact_stage:
            return True
        wrong_stage = NORMAL_SPIN_STAGE if target.is_compact else COMPACT_STAGE
        return target.nsm.get(wrong_stage, Decimal(0)) == 0


class PackagingRule(BaseBusinessRule[NsmInput]):
    code = "BR-12"
    message = "Mã chưa có loại đóng gói hợp lệ. Vui lòng chọn loại đóng gói."
    field = "packaging_code"

    def is_satisfied_by(self, target: NsmInput) -> bool:
        return target.packaging_valid

    def describe_violation(self, target: NsmInput) -> str:
        return f"Mã {target.yarn_code} chưa có loại đóng gói hợp lệ. Vui lòng chọn loại đóng gói."


class LockedYarnRule(BaseBusinessRule[NsmInput]):
    code = "BR-32"
    message = "Mã đã có mã kế toán nên không sửa được. Muốn điều chỉnh NSM, hãy tạo bản ĐCNSM."

    def is_satisfied_by(self, target: NsmInput) -> bool:
        return not target.is_locked

    def describe_violation(self, target: NsmInput) -> str:
        return f"Mã {target.yarn_code} đã có mã kế toán nên không sửa được. Muốn điều chỉnh NSM, hãy tạo bản ĐCNSM."


class AdjustReasonRule(BaseBusinessRule[NsmInput]):
    code = "BR-33"
    message = "Vui lòng nhập lý do điều chỉnh."
    field = "adjust_reason"

    def is_satisfied_by(self, target: NsmInput) -> bool:
        return bool(target.adjust_reason.strip())


class NsmWarningReasonRule(BaseBusinessRule[NsmInput]):
    code = "BR-38"
    message = "NSM khác sợi cùng nhóm. Vui lòng nhập lý do trước khi lưu."
    field = "nsm_warning_reason"

    def is_satisfied_by(self, target: NsmInput) -> bool:
        return not target.warning_stages or bool(target.warning_reason.strip())

    def describe_violation(self, target: NsmInput) -> str:
        return (
            f"NSM khác sợi cùng nhóm ({target.reference_yarn_code}) ở công đoạn: {', '.join(target.warning_stages)}. "
            "Vui lòng nhập lý do trước khi lưu."
        )


class CardingPassRule(BaseBusinessRule[NsmInput]):
    code = "BR-56"
    message = "Dây chuyền chỉ chạy tối đa số nguyên liệu cho phép trong một sợi."
    field = "components"

    def over_limit(self, target: NsmInput) -> tuple[str, int] | None:
        counts = Counter(c.carding_stage for c in target.components if c.carding_stage)
        for line, limit in target.max_passes.items():
            if counts.get(line, 0) > limit:
                return line, limit
        return None

    def duplicate(self, target: NsmInput) -> str | None:
        counts = Counter(normalize_key(c.material_label) for c in target.components)
        return next((c.material_label for c in target.components if counts[normalize_key(c.material_label)] > 1), None)

    def is_satisfied_by(self, target: NsmInput) -> bool:
        return self.over_limit(target) is None and self.duplicate(target) is None

    def describe_violation(self, target: NsmInput) -> str:
        over = self.over_limit(target)
        if over is not None:
            return f"{over[0]} chỉ chạy tối đa {over[1]} nguyên liệu trong một sợi."
        return f"Nguyên liệu '{self.duplicate(target)}' bị nhập 2 lần."


class GroupMaterialRule(BaseBusinessRule[NsmInput]):
    code = "BR-57"
    message = "Nguyên liệu không có trong nhóm tiêu hao. Vui lòng chọn nguyên liệu của nhóm."
    field = "components"

    def wrong(self, target: NsmInput) -> str | None:
        if not target.material_options:
            return None
        allowed = {normalize_key(m) for m in target.material_options}
        return next(
            (
                c.material_label
                for c in target.components
                if c.carding_stage and normalize_key(c.material_label) not in allowed
            ),
            None,
        )

    def is_satisfied_by(self, target: NsmInput) -> bool:
        return self.wrong(target) is None

    def describe_violation(self, target: NsmInput) -> str:
        return (
            f"Nguyên liệu '{self.wrong(target)}' không có trong nhóm tiêu hao '{target.group_key}'. "
            "Vui lòng chọn nguyên liệu của nhóm."
        )


def number_passes(components: Sequence[YarnComponent]) -> list[YarnComponent]:
    """BR-56: lượt = thứ tự của thành phần trong các thành phần cùng dây chuyền (1, 2, 3)."""
    counters: Counter[str] = Counter()
    result = []
    for component in components:
        if component.carding_stage:
            counters[component.carding_stage] += 1
            result.append(component.model_copy(update={"pass_no": counters[component.carding_stage]}))
        else:
            result.append(component.model_copy(update={"pass_no": None, "nsm_carding": None}))
    return result


class NsmInputBusiness(BaseBusiness[NsmInput]):
    def rules(self) -> Sequence[BaseBusinessRule[NsmInput]]:
        return (
            BlendRatioRule(),
            CardingPassRule(),
            GroupMaterialRule(),
            NsmValuesRule(),
            CompactStageRule(),
            PackagingRule(),
        )

    def number_passes(self, components: Sequence[YarnComponent]) -> list[YarnComponent]:
        """BR-56: app tự đánh lượt."""
        return number_passes(components)

    def ensure_editable(self, target: NsmInput) -> None:
        """BR-32: bản khoá không sửa tên, đóng gói, tỷ lệ pha, NSM."""
        LockedYarnRule().check(target)

    def ensure_adjust_reason(self, target: NsmInput) -> None:
        """BR-33: ĐCNSM bắt buộc lý do."""
        AdjustReasonRule().check(target)

    def ensure_warning_reason(self, target: NsmInput) -> None:
        """BR-38: NSM khác sợi so sánh → bắt buộc lý do."""
        NsmWarningReasonRule().check(target)
