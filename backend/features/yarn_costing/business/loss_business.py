"""Tiêu hao: BR-24 ảnh hưởng + khoá, BR-25 nhập tay, BR-26 tiêu hao thứ cấp, BR-27, BR-28, BR-29."""

from collections.abc import Iterable, Sequence
from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.yarn_costing.business.display_business import format_percent
from backend.features.yarn_costing.constants import MAX_LOCKED_CODES_SHOWN, RATIO_TOLERANCE
from backend.features.yarn_costing.models.enums import LossGroupLevel, SecondaryMethod, YarnStatus
from backend.features.yarn_costing.models.loss_checks import ComponentCheck, DeleteCheck, LockCheck, LossGroupCheck
from backend.features.yarn_costing.models.loss_group import LossComponent, LossGroup
from backend.features.yarn_costing.models.stage import Stage
from backend.features.yarn_costing.models.yarn import Yarn

ZERO = Decimal(0)
MAX_COMPONENTS = 5
AFFECTED_STATUSES = (YarnStatus.DA_TINH_GIA, YarnStatus.CO_MA_KE_TOAN, YarnStatus.CHUA_TINH_DUOC)


class LockedGroupRule(BaseBusinessRule[LockCheck]):
    code = "BR-24"
    message = "Nhóm tiêu hao đang được dùng cho sợi đã có mã kế toán. Chỉ Phòng SO được sửa."

    def is_satisfied_by(self, target: LockCheck) -> bool:
        return target.is_so or not target.locked_codes

    def describe_violation(self, target: LockCheck) -> str:
        codes = ", ".join(target.locked_codes[:MAX_LOCKED_CODES_SHOWN])
        return (
            f"Nhóm tiêu hao '{target.group_key}' đang được dùng cho sợi đã có mã kế toán ({codes}). "
            "Chỉ Phòng SO được sửa."
        )


class ComponentsRule(BaseBusinessRule[ComponentCheck]):
    code = "BR-27"
    message = "Nhóm sợi pha cần từ 1 đến 5 thành phần, tổng tỷ lệ bằng 100% và không được dùng chính nó làm thành phần."
    field = "components"

    def is_satisfied_by(self, target: ComponentCheck) -> bool:
        return (
            1 <= target.count <= MAX_COMPONENTS
            and target.ratios_positive
            and abs(target.ratio_total - Decimal(1)) <= RATIO_TOLERANCE
            and target.all_exist
            and not target.self_or_cycle
        )

    def describe_violation(self, target: ComponentCheck) -> str:
        if not 1 <= target.count <= MAX_COMPONENTS:
            return "Nhóm sợi pha cần từ 1 đến 5 thành phần."
        if target.self_or_cycle:
            return "Một nhóm không thể là thành phần của chính nó."
        if target.ratios_positive and abs(target.ratio_total - Decimal(1)) > RATIO_TOLERANCE:
            return f"Tổng tỷ lệ thành phần phải bằng 100% (hiện là {format_percent(target.ratio_total)}%)."
        return self.message


class LossGroupValuesRule(BaseBusinessRule[LossGroupCheck]):
    code = "BR-28"
    message = "Tiêu hao phải từ 0% đến dưới 100%."

    def is_satisfied_by(self, target: LossGroupCheck) -> bool:
        return not target.duplicate and target.losses_ok

    def describe_violation(self, target: LossGroupCheck) -> str:
        if target.duplicate:
            return f"Nhóm tiêu hao '{target.group_key}' đã có ở xưởng {target.factory_code}."
        return self.message


class DeleteGroupRule(BaseBusinessRule[DeleteCheck]):
    code = "BR-29"
    message = "Không xoá được: nhóm đang được dùng."

    def is_satisfied_by(self, target: DeleteCheck) -> bool:
        return target.yarn_count == 0 and target.parent_count == 0

    def describe_violation(self, target: DeleteCheck) -> str:
        return (
            f"Không xoá được: nhóm đang được dùng bởi {target.yarn_count} mã sợi / {target.parent_count} nhóm sợi pha."
        )


class LossBusiness(BaseBusiness[LossGroup]):
    # ---- BR-24 ---------------------------------------------------------------------------------------------------
    def parents_of(self, group_key: str, groups: Iterable[LossGroup]) -> list[LossGroup]:
        return [g for g in groups if any(c.component_group_key == group_key for c in g.components)]

    def affected_groups(self, group_key: str, groups: Sequence[LossGroup]) -> set[str]:
        """BR-24: G và mọi nhóm thứ cấp dùng G làm thành phần (trực tiếp hoặc gián tiếp)."""
        affected, stack = {group_key}, [group_key]
        while stack:
            current = stack.pop()
            for parent in self.parents_of(current, groups):
                if parent.group_key not in affected:
                    affected.add(parent.group_key)
                    stack.append(parent.group_key)
        return affected

    def parent_index(self, groups: Sequence[LossGroup]) -> dict[str, list[str]]:
        """component key → keys of the secondary groups using it (for listing thousands of groups quickly)."""
        index: dict[str, list[str]] = {}
        for group in groups:
            for component in group.components:
                index.setdefault(component.component_group_key, []).append(group.group_key)
        return index

    def affected_from_index(self, group_key: str, index: dict[str, list[str]]) -> set[str]:
        """BR-24 using a prepared parent index."""
        affected, stack = {group_key}, [group_key]
        while stack:
            for parent in index.get(stack.pop(), []):
                if parent not in affected:
                    affected.add(parent)
                    stack.append(parent)
        return affected

    def check_component_rows(
        self, group_key: str, rows: Sequence[tuple[str, Decimal | None]], groups: Sequence[LossGroup]
    ) -> list[LossComponent]:
        """BR-27 on rows typed in a table (empty key rows ignored); returns the components when valid."""
        filled = [(key.strip(), ratio) for key, ratio in rows if key and key.strip()]
        ratios_ok = all(r is not None and ZERO < r <= Decimal(1) for _, r in filled)
        if not ratios_ok:
            keys = {g.group_key for g in groups}
            ComponentsRule().check(
                ComponentCheck(
                    count=len(filled),
                    ratio_total=sum((r or ZERO for _, r in filled), ZERO),
                    ratios_positive=False,
                    all_exist=all(k in keys for k, _ in filled),
                    self_or_cycle=any(k == group_key for k, _ in filled),
                )
            )
        components = [LossComponent(component_group_key=k, ratio=r) for k, r in filled]  # type: ignore[arg-type]
        self.ensure_valid_components(group_key, components, groups)
        return components

    def affected_yarns(self, keys: set[str], factory_code: str, yarns: Sequence[Yarn]) -> list[Yarn]:
        """BR-24: bản NSM (Đã tính giá, Có mã kế toán, Chưa tính được) có nhóm tiêu hao thuộc các nhóm bị ảnh hưởng."""
        return [
            y
            for y in yarns
            if y.factory_code == factory_code and y.status in AFFECTED_STATUSES and y.loss_group_key in keys
        ]

    def locked_codes(self, keys: set[str], factory_code: str, yarns: Sequence[Yarn]) -> list[str]:
        """BR-24: G đang khoá nếu ít nhất một bản NSM bị ảnh hưởng đang khoá."""
        return sorted(y.yarn_code for y in self.affected_yarns(keys, factory_code, yarns) if y.is_locked)

    def ensure_can_edit(self, group_key: str, locked_codes: list[str], is_so: bool) -> None:
        """BR-24: nhóm đang khoá chỉ Phòng SO được sửa."""
        LockedGroupRule().check(LockCheck(group_key=group_key, locked_codes=locked_codes, is_so=is_so))

    # ---- BR-25 / BR-28 -------------------------------------------------------------------------------------------
    def manual_losses(self, losses: dict[str, Decimal], stage_codes: Sequence[str]) -> dict[str, Decimal]:
        """BR-25: nhóm sơ cấp / nhập từ file: tiêu hao nhập tay từng công đoạn (chỉ giữ công đoạn của xưởng, ≠ 0)."""
        return {code: value for code, value in losses.items() if code in stage_codes and value != 0}

    def losses_valid(self, losses: dict[str, Decimal]) -> bool:
        return all(ZERO <= value < Decimal(1) for value in losses.values())

    def ensure_valid_group(
        self, group_key: str, factory_code: str, duplicate: bool, losses: dict[str, Decimal]
    ) -> None:
        """BR-28: group_key duy nhất trong xưởng; mỗi tiêu hao 0 ≤ x < 100%."""
        LossGroupValuesRule().check(
            LossGroupCheck(
                group_key=group_key, factory_code=factory_code, duplicate=duplicate, losses_ok=self.losses_valid(losses)
            )
        )

    # ---- BR-26 / BR-27 -------------------------------------------------------------------------------------------
    def creates_cycle(self, group_key: str, components: Sequence[LossComponent], groups: Sequence[LossGroup]) -> bool:
        """BR-27: thành phần khác chính nó và không tạo vòng (A dùng B, B dùng A)."""
        by_key = {g.group_key: g for g in groups}
        stack = [c.component_group_key for c in components]
        seen: set[str] = set()
        while stack:
            key = stack.pop()
            if key == group_key:
                return True
            if key in seen:
                continue
            seen.add(key)
            group = by_key.get(key)
            if group is not None:
                stack.extend(c.component_group_key for c in group.components)
        return False

    def ensure_valid_components(
        self, group_key: str, components: Sequence[LossComponent], groups: Sequence[LossGroup]
    ) -> None:
        """BR-27: 1-5 thành phần có sẵn của cùng xưởng, tỷ lệ > 0, tổng = 100%, không vòng."""
        keys = {g.group_key for g in groups}
        ComponentsRule().check(
            ComponentCheck(
                count=len(components),
                ratio_total=sum((c.ratio for c in components), ZERO),
                ratios_positive=all(c.ratio > 0 for c in components),
                all_exist=all(c.component_group_key in keys for c in components),
                self_or_cycle=self.creates_cycle(group_key, components, groups),
            )
        )

    def secondary_losses(
        self, components: Sequence[LossComponent], groups: dict[str, LossGroup], stages: Sequence[Stage]
    ) -> dict[str, Decimal]:
        """BR-26: tại công đoạn s: Bình quân = Σ tiêu hao_i × tỷ lệ_i; Cộng thẳng = Σ tiêu hao_i."""
        result: dict[str, Decimal] = {}
        for stage in stages:
            if stage.is_packaging:
                continue
            total = ZERO
            for component in components:
                group = groups.get(component.component_group_key)
                if group is None:
                    continue
                loss = group.loss_at(stage.stage_code)
                total += loss * component.ratio if stage.secondary_method == SecondaryMethod.BINH_QUAN else loss
            if total != 0:
                result[stage.stage_code] = total
        return result

    def recompute_secondaries(self, groups: Sequence[LossGroup], stages: Sequence[Stage]) -> list[LossGroup]:
        """BR-26: tính lại tự động mọi nhóm thứ cấp (thành phần trước, nhóm dùng nó sau). Trả về các nhóm đã đổi."""
        by_key = {g.group_key: g for g in groups}
        changed: dict[str, LossGroup] = {}
        done: set[str] = set()

        def visit(key: str, path: set[str]) -> None:
            group = by_key.get(key)
            if group is None or key in done or key in path:
                return
            for component in group.components:
                visit(component.component_group_key, path | {key})
            if group.level == LossGroupLevel.THU_CAP and group.components:
                losses = self.secondary_losses(group.components, by_key, stages)
                if losses != group.losses:
                    by_key[key] = group.model_copy(update={"losses": losses})
                    changed[key] = by_key[key]
            done.add(key)

        for key in list(by_key):
            visit(key, set())
        return list(changed.values())

    def ensure_deletable(self, yarn_count: int, parent_count: int) -> None:
        """BR-29: chỉ xoá nhóm không có mã sợi dùng và không là thành phần của nhóm khác."""
        DeleteGroupRule().check(DeleteCheck(yarn_count=yarn_count, parent_count=parent_count))
