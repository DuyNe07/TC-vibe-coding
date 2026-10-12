"""Dữ liệu nền: BR-50 cấu hình công đoạn, BR-51 phiên bản định mức, BR-52 loại đóng gói, BR-60 đóng gói mặc định,
BR-62 tính lại khi lưu đóng gói + kiểm tra UC-01..UC-09."""

from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.yarn_costing.constants import MAX_PASSES_LIMIT
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.enums import YarnStatus
from backend.features.yarn_costing.models.master_checks import (
    ConfigIssues,
    DefaultPackagingCheck,
    PackagingCheck,
    RateVersionCheck,
)
from backend.features.yarn_costing.models.packaging_type import PackagingType
from backend.features.yarn_costing.models.rate_version import RateLine, RateVersion
from backend.features.yarn_costing.models.stage import LINE_RATIO_PREFIX, NO_BLEND_SLOT, PASS_RATIO_SLOT, Stage
from backend.features.yarn_costing.models.yarn import Yarn

DATE_REASON_MESSAGE = "Vui lòng chọn ngày hiệu lực và nhập lý do."
PACKAGING_NO_RECALC_TEXT = "Giá các mã không thay đổi."
CLOSED_STATUSES = (YarnStatus.DA_HUY, YarnStatus.TU_CHOI)


class StageConfigRule(BaseBusinessRule[ConfigIssues]):
    code = "BR-50"
    message = "Cấu hình công đoạn không hợp lệ."

    def is_satisfied_by(self, target: ConfigIssues) -> bool:
        return not target.details

    def describe_violation(self, target: ConfigIssues) -> str:
        return f"Cấu hình công đoạn không hợp lệ: {'; '.join(target.details)}"


class RateVersionRule(BaseBusinessRule[RateVersionCheck]):
    code = "BR-51"
    message = "Thiếu định mức."

    def is_satisfied_by(self, target: RateVersionCheck) -> bool:
        return not target.missing_codes and not target.negative and target.has_date_and_reason

    def describe_violation(self, target: RateVersionCheck) -> str:
        if not target.has_date_and_reason:
            return DATE_REASON_MESSAGE
        if target.negative:
            return "Định mức phải là số ≥ 0."
        return f"Thiếu định mức cho: {', '.join(target.missing_codes)}."


class PackagingTypeRule(BaseBusinessRule[PackagingCheck]):
    code = "BR-52"
    message = "Phút/kg phải lớn hơn 0."

    def is_satisfied_by(self, target: PackagingCheck) -> bool:
        return not target.duplicate and target.minutes_ok

    def describe_violation(self, target: PackagingCheck) -> str:
        if target.duplicate:
            return f"Mã đóng gói '{target.code}' đã có ở xưởng {target.factory_code}."
        return self.message


class DefaultPackagingRule(BaseBusinessRule[DefaultPackagingCheck]):
    code = "BR-60"
    message = "Mỗi xưởng chỉ được chọn một loại đóng gói mặc định."

    def is_satisfied_by(self, target: DefaultPackagingCheck) -> bool:
        return target.default_count <= 1 and target.default_active

    def describe_violation(self, target: DefaultPackagingCheck) -> str:
        if target.default_count > 1:
            return self.message
        return "Loại đóng gói mặc định phải là loại đang hoạt động."


class MasterBusiness(BaseBusiness[Stage]):
    def require(self, condition: bool, message: str) -> None:
        if not condition:
            raise YarnValidationError(message)

    def require_date_and_reason(self, effective_date: date | None, reason: str) -> None:
        self.require(effective_date is not None and bool((reason or "").strip()), DATE_REASON_MESSAGE)

    def stage_issues(
        self, factory_code: str, stages: Sequence[Stage], used_codes: set[str], old_codes: set[str]
    ) -> list[str]:
        """BR-50: mã và thứ tự duy nhất, đúng một công đoạn đóng gói, cumulative_stages hợp lệ, ô tỷ lệ pha hợp lệ,
        không xoá công đoạn đang có NSM hoặc tiêu hao."""
        issues: list[str] = []
        codes = Counter(s.stage_code for s in stages)
        issues += [f"Mã công đoạn '{c}' đã có ở xưởng {factory_code}." for c, n in codes.items() if n > 1]
        sequences = Counter(s.sequence for s in stages)
        issues += [f"Thứ tự {n} bị trùng." for n, count in sequences.items() if count > 1]
        if sum(1 for s in stages if s.is_packaging) != 1:
            issues.append("Cần đúng một công đoạn đóng gói.")
        by_code = {s.stage_code: s for s in stages}
        carding = [s.stage_code for s in stages if s.is_carding]
        slots = (NO_BLEND_SLOT, PASS_RATIO_SLOT, *(LINE_RATIO_PREFIX + code for code in carding))
        for stage in stages:
            for code in stage.cumulative_stages:
                target = by_code.get(code)
                if target is None:
                    issues.append(f"Công đoạn '{code}' không có ở xưởng {factory_code}.")
                elif target.sequence <= stage.sequence:
                    issues.append(f"Công đoạn '{code}' phải đứng sau '{stage.stage_code}'.")
            if stage.blend_slot not in slots:
                issues.append(
                    f"Tỷ lệ '{stage.blend_slot}' không hợp lệ (dây chuyền chải thô không có ở xưởng {factory_code})."
                )
            if stage.is_carding and not (stage.max_passes and 1 <= stage.max_passes <= MAX_PASSES_LIMIT):
                issues.append(f"Dây chuyền chải thô '{stage.stage_code}' cần số lượt tối đa từ 1 đến 3.")
        removed = sorted((old_codes - set(codes)) & used_codes)
        issues += [f"Không xoá được công đoạn '{c}' đang có NSM hoặc tiêu hao." for c in removed]
        return issues

    def ensure_valid_stages(
        self, factory_code: str, stages: Sequence[Stage], used_codes: set[str], old_codes: set[str]
    ) -> None:
        """BR-50."""
        StageConfigRule().check(ConfigIssues(details=self.stage_issues(factory_code, stages, used_codes, old_codes)))

    def ensure_valid_rate_version(
        self,
        lines: Sequence[RateLine],
        required_codes: Sequence[str],
        negative: bool,
        effective_date: date | None,
        reason: str,
    ) -> None:
        """BR-51: đủ 5 khoản ≥ 0 cho mọi công đoạn không phải đóng gói và mọi loại đóng gói đang hoạt động; ngày + lý do."""
        present = {line.rate_code for line in lines}
        RateVersionRule().check(
            RateVersionCheck(
                missing_codes=[c for c in required_codes if c not in present],
                negative=negative,
                has_date_and_reason=effective_date is not None and bool((reason or "").strip()),
            )
        )

    def required_rate_codes(self, stages: Sequence[Stage], packaging: Sequence[PackagingType]) -> list[str]:
        """BR-51: mã bắt buộc có định mức."""
        codes = [s.stage_code for s in sorted(stages, key=lambda s: s.sequence) if not s.is_packaging]
        return codes + [p.code for p in packaging if p.active]

    def ensure_valid_packaging(self, factory_code: str, rows: Sequence[PackagingType]) -> None:
        """BR-52: mã loại đóng gói duy nhất trong xưởng; phút/kg > 0."""
        counts = Counter(p.code for p in rows)
        for row in rows:
            PackagingTypeRule().check(
                PackagingCheck(
                    code=row.code,
                    factory_code=factory_code,
                    duplicate=counts[row.code] > 1,
                    minutes_ok=row.minutes_per_kg > 0,
                )
            )

    def ensure_single_default(self, rows: Sequence[PackagingType]) -> None:
        """BR-60: mỗi xưởng tối đa một loại đóng gói mặc định, phải là loại đang hoạt động."""
        defaults = [p for p in rows if p.is_default]
        DefaultPackagingRule().check(
            DefaultPackagingCheck(default_count=len(defaults), default_active=all(p.active for p in defaults))
        )

    def default_packaging(self, rows: Sequence[PackagingType], version: RateVersion | None) -> str | None:
        """BR-60: loại mặc định được điền sẵn nếu loại đó chọn được (BR-52), ngược lại để trống."""
        chosen = next((p for p in rows if p.is_default), None)
        return chosen.code if chosen is not None and self.is_selectable(chosen, version) else None

    def is_selectable(self, packaging: PackagingType, version: RateVersion | None) -> bool:
        """BR-52: chỉ loại đang hoạt động và đã có định mức mới hiện cho Sales chọn."""
        return packaging.active and version is not None and version.line_for(packaging.code) is not None

    def packaging_in_use(self, factory_code: str, yarns: Sequence[Yarn]) -> set[str]:
        """BR-62: loại đóng gói "đang được dùng" = có bản NSM của xưởng (trừ Đã huỷ, Từ chối) dùng mã loại đó."""
        return {
            y.packaging_code
            for y in yarns
            if y.factory_code.value == factory_code and y.packaging_code and y.status not in CLOSED_STATUSES
        }

    def packaging_recalc_codes(
        self, old: Mapping[str, PackagingType], rows: Sequence[PackagingType], in_use: set[str]
    ) -> list[str]:
        """BR-62: các loại đang được dùng có Phút/kg khác giá trị đang lưu -> phải tính lại toàn bộ xưởng."""
        return [
            p.code
            for p in rows
            if p.code in old and p.code in in_use and old[p.code].minutes_per_kg != p.minutes_per_kg
        ]

    def packaging_confirm_text(
        self, factory_code: str, recalc_codes: Sequence[str], effective_date: date | None
    ) -> str:
        """BR-62: nội dung hộp xác nhận trước khi lưu bảng Đóng gói."""
        if not recalc_codes:
            return PACKAGING_NO_RECALC_TEXT
        when = effective_date.strftime("%d/%m/%Y") if effective_date else ""
        return (
            f"Phút/kg của loại {', '.join(recalc_codes)} (đang có mã sợi dùng) thay đổi. "
            f"App sẽ tính lại toàn bộ giá xưởng {factory_code} từ ngày {when}."
        )

    def ensure_recovery_rate(self, rate: Decimal) -> None:
        """UC-06: 0 ≤ tỷ lệ hồi phế < 100%."""
        self.require(Decimal(0) <= rate < Decimal(1), "Tỷ lệ hồi phế phải từ 0% đến dưới 100%.")

    def ensure_positive(self, value: Decimal | None, message: str) -> None:
        """UC-08 / UC-09: tỷ giá / hệ số thí nghiệm > 0."""
        self.require(value is not None and value > 0, message)

    def ensure_access_code(self, access_code: str) -> None:
        """UC-01: mã nội bộ 4-20 ký tự."""
        self.require(4 <= len(access_code.strip()) <= 20, "Mã nội bộ phải dài từ 4 đến 20 ký tự.")

    def ensure_unique_members(self, names: Sequence[str]) -> None:
        """UC-01: tên thành viên không trùng trong nhóm."""
        counts = Counter(n.strip() for n in names)
        duplicate = next((n for n, c in counts.items() if c > 1), None)
        self.require(duplicate is None, f"Tên '{duplicate}' đã có trong nhóm.")

    def version_code(self, factory_code: str, existing: Sequence[str]) -> str:
        """4.5: mã phiên bản DM-<xưởng>-NNN."""
        prefix = f"DM-{factory_code}-"
        numbers = [int(c[len(prefix) :]) for c in existing if c.startswith(prefix) and c[len(prefix) :].isdigit()]
        return f"{prefix}{max(numbers, default=0) + 1:03d}"
