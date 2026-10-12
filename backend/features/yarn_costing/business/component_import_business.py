"""Khai báo thành phần sợi pha bằng file (UC-45): BR-66 kiểm tra dòng, BR-67 lưu nhóm, BR-68 đổi tên thành phần của mã,
BR-69 quyền."""

from collections import Counter
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.core.exceptions import AppError
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.business.import_business import technology_of
from backend.features.yarn_costing.business.loss_business import LossBusiness
from backend.features.yarn_costing.business.name_business import group_key_of
from backend.features.yarn_costing.constants import (
    COMP_SHEET,
    MSG_COMP_DUPLICATE,
    MSG_COMP_NEW_TECH,
    MSG_COMP_NOT_FOUND,
    MSG_COMP_PAIR,
    MSG_COMP_RATIO,
    MSG_COMP_TWICE,
    MSG_COMP_UNMATCHED,
)
from backend.features.yarn_costing.models.enums import FactoryCode, LossGroupLevel, YarnStatus
from backend.features.yarn_costing.models.import_rows import (
    ComponentDeclRow,
    ComponentGroupChange,
    ComponentPlan,
    RejectedRow,
    UnmatchedYarn,
)
from backend.features.yarn_costing.models.loss_group import LossComponent, LossGroup
from backend.features.yarn_costing.models.stage import Stage
from backend.features.yarn_costing.models.yarn import Yarn, YarnComponent
from backend.shared.utils import normalize_key

HUNDRED = Decimal(100)
RATIO_TOLERANCE = Decimal("0.0001")


class ComponentImportBusiness(BaseBusiness[LossGroup]):
    def __init__(self) -> None:
        self.loss = LossBusiness()
        self.costing = CostingBusiness()

    # ---- BR-66 ---------------------------------------------------------------------------------------------------
    def resolve_component(self, name: str, groups: Sequence[LossGroup]) -> str | None:
        """BR-66: tên thành phần khớp `group_key` hoặc `material_tech_key` của một nhóm của xưởng."""
        key = group_key_of(name)
        for group in groups:
            if group.group_key == key:
                return group.group_key
        wanted = normalize_key(name)
        for group in groups:
            if normalize_key(group.material_tech_key) == wanted and group.material.strip():
                return group.group_key
        return None

    def check_row(
        self, row: ComponentDeclRow, factory_code: str, groups: Sequence[LossGroup], existing: set[str]
    ) -> tuple[list[LossComponent], str | None]:
        """BR-66: thành phần của một dòng (tỷ lệ % → phân số) hoặc lý do loại dòng."""
        components: list[LossComponent] = []
        seen: set[str] = set()
        for k, (name, ratio) in enumerate(zip(row.names, row.ratios, strict=False), start=1):
            if k in row.bad_ratios:
                return [], MSG_COMP_RATIO.format(k=k)
            if not name and ratio is None:
                continue
            if not name or ratio is None:
                return [], MSG_COMP_PAIR.format(k=k)
            if ratio <= 0 or ratio > HUNDRED:
                return [], MSG_COMP_RATIO.format(k=k)
            key = self.resolve_component(name, groups)
            if key is None:
                return [], MSG_COMP_NOT_FOUND.format(name=name, factory=factory_code)
            if key in seen:
                return [], MSG_COMP_TWICE.format(name=name)
            seen.add(key)
            components.append(LossComponent(component_group_key=key, ratio=ratio / HUNDRED))
        group_key = group_key_of(row.group_label)
        if group_key not in existing and technology_of(row.technology_text) is None:
            return [], MSG_COMP_NEW_TECH.format(group=row.group_label)
        return components, None

    # ---- BR-67 ---------------------------------------------------------------------------------------------------
    def declared_group(
        self,
        row: ComponentDeclRow,
        components: list[LossComponent],
        current: LossGroup | None,
        factory: FactoryCode,
        label: str,
        now: datetime,
    ) -> LossGroup:
        """BR-67: nhóm đã có → Thứ cấp, thay thành phần (tiêu hao tính sau theo BR-26); nhóm chưa có → tạo nhóm Thứ cấp."""
        if current is not None:
            return current.model_copy(
                update={
                    "level": LossGroupLevel.THU_CAP,
                    "components": components,
                    "updated_by": label,
                    "updated_at": now,
                }
            )
        return LossGroup(
            factory_code=factory,
            group_key=group_key_of(row.group_label),
            yarn_group_label=row.group_label.strip(),
            material="",
            technology=technology_of(row.technology_text),  # type: ignore[arg-type]  # checked by BR-66
            level=LossGroupLevel.THU_CAP,
            components=components,
            losses={},
            updated_by=label,
        )

    # ---- BR-68 ---------------------------------------------------------------------------------------------------
    def relabel_yarn(
        self, yarn: Yarn, group: LossGroup, groups: dict[str, LossGroup], factory_code: str
    ) -> tuple[Yarn, list[UnmatchedYarn]]:
        """BR-68: đổi `material_label` của các thành phần có dây chuyền chải thô theo thành phần của nhóm (cùng dây chuyền
        hoặc dây chuyền tương đương; nhiều ứng viên → cùng tỷ lệ). Không đổi tỷ lệ, dây chuyền, NSM, lượt."""
        new_components: list[YarnComponent] = []
        unmatched: list[UnmatchedYarn] = []
        used: set[str] = set()
        for component in yarn.components:
            line = component.carding_stage
            if not line:
                new_components.append(component)
                continue
            current = self.costing.group_component(group, component.material_label, groups)
            if current is not None and current[1] is not None:
                used.add(current[1].group_key)
                new_components.append(component)
                continue
            other = self.costing.equivalent_line(factory_code, line)
            candidates = []
            for item in group.components:
                source = groups.get(item.component_group_key)
                if source is None or source.group_key in used:
                    continue
                if source.loss_at(line) > 0 or (other is not None and source.loss_at(other) > 0):
                    candidates.append((item, source))
            if len(candidates) > 1:
                candidates = [(i, s) for i, s in candidates if abs(i.ratio - component.ratio) <= RATIO_TOLERANCE]
            if len(candidates) != 1:
                unmatched.append(
                    UnmatchedYarn(
                        yarn_code=yarn.yarn_code,
                        yarn_name=yarn.yarn_name,
                        material_label=component.material_label,
                        carding_stage=line,
                        group_key=group.group_key,
                    )
                )
                new_components.append(component)
                continue
            source = candidates[0][1]
            used.add(source.group_key)
            new_components.append(component.model_copy(update={"material_label": source.material_label}))
        if new_components != list(yarn.components):
            yarn = yarn.model_copy(update={"components": new_components})
        return yarn, unmatched

    def unmatched_message(self, item: UnmatchedYarn) -> str:
        """BR-68: lý do 'Chưa tính được' của mã có thành phần không ghép được."""
        return MSG_COMP_UNMATCHED.format(material=item.material_label, line=item.carding_stage, group=item.group_key)

    # ---- UC-45 plan (BR-66..BR-69) ---------------------------------------------------------------------------------
    def plan(
        self,
        rows: Sequence[ComponentDeclRow],
        factory: FactoryCode,
        groups: dict[str, LossGroup],
        stages: Sequence[Stage],
        yarns: Sequence[Yarn],
        is_so: bool,
        label: str,
        now: datetime,
    ) -> ComponentPlan:
        """UC-45: kiểm tra mọi dòng (BR-66, BR-69), nhóm sau khai báo (BR-67, BR-26, BR-27), mã bị ảnh hưởng, đổi tên
        thành phần của mã (BR-68). Không lưu gì."""
        factory_code = factory.value
        rejected: list[RejectedRow] = []

        def reject(row: ComponentDeclRow, reason: str) -> None:
            rejected.append(RejectedRow(sheet=COMP_SHEET, excel_row=row.excel_row, key=row.group_label, reason=reason))

        filled = [r for r in rows if r.group_label and any(r.names)]
        counts = Counter(group_key_of(r.group_label) for r in filled)
        existing = set(groups)
        all_groups = list(groups.values())
        candidates: dict[str, tuple[ComponentDeclRow, list[LossComponent]]] = {}
        for row in filled:
            key = group_key_of(row.group_label)
            if counts[key] > 1:
                reject(row, MSG_COMP_DUPLICATE.format(group=row.group_label))
                continue
            components, reason = self.check_row(row, factory_code, all_groups, existing)
            if reason is not None:
                reject(row, reason)
                continue
            if key in existing:  # BR-69: nhóm đang khoá chỉ Phòng SO được đổi
                affected = self.loss.affected_groups(key, all_groups)
                locked = self.loss.locked_codes(affected, factory_code, yarns)
                try:
                    self.loss.ensure_can_edit(key, locked, is_so)
                except AppError as exc:
                    reject(row, exc.message)
                    continue
            candidates[key] = (row, components)
        # BR-67 + BR-27 on the groups after the declaration (cycles between rows of the same file included)
        while True:
            working = dict(groups)
            for key, (row, components) in candidates.items():
                working[key] = self.declared_group(row, components, groups.get(key), factory, label, now)
            invalid: dict[str, str] = {}
            for key, (_row, components) in candidates.items():
                try:
                    self.loss.ensure_valid_components(key, components, list(working.values()))
                except AppError as exc:
                    invalid[key] = exc.message
            if not invalid:
                break
            for key, message in invalid.items():
                reject(candidates.pop(key)[0], message)
        working_list = list(working.values())
        affected_keys: set[str] = set()
        for key in candidates:
            affected_keys |= self.loss.affected_groups(key, working_list)
        # BR-26: only the declared groups and the secondary groups using them are recomputed (others unchanged)
        recomputed = {
            g.group_key: g
            for g in self.loss.recompute_secondaries(working_list, stages)
            if g.group_key in affected_keys
        }
        final = {**working, **recomputed}
        for key in candidates:
            if key not in recomputed:
                final[key] = final[key].model_copy(
                    update={"losses": self.loss.secondary_losses(final[key].components, final, stages)}
                )
        changes: list[ComponentGroupChange] = []
        for key, (row, _components) in candidates.items():
            old = groups.get(key)
            keys = self.loss.affected_groups(key, working_list)
            changes.append(
                ComponentGroupChange(
                    excel_row=row.excel_row,
                    group=final[key],
                    created=old is None,
                    old_level=old.level.value if old is not None else "",
                    old_losses=dict(old.losses) if old is not None else {},
                    affected_count=len(self.loss.affected_yarns(keys, factory_code, yarns)),
                )
            )
        declared = {c.group.group_key for c in changes}
        dependents = [g for k, g in final.items() if k in recomputed and k not in declared]
        relabeled: list[Yarn] = []
        unmatched: list[UnmatchedYarn] = []
        for yarn in yarns:
            if yarn.factory_code != factory or yarn.loss_group_key not in declared or yarn.status == YarnStatus.DA_HUY:
                continue
            new_yarn, missing = self.relabel_yarn(yarn, final[yarn.loss_group_key], final, factory_code)
            if new_yarn is not yarn:
                relabeled.append(new_yarn)
            unmatched.extend(missing)
        return ComponentPlan(
            changes=sorted(changes, key=lambda c: c.excel_row),
            recomputed=dependents,
            rejected_rows=sorted(rejected, key=lambda r: r.excel_row),
            relabeled_yarns=relabeled,
            unmatched=unmatched,
            affected_keys=sorted(affected_keys),
            affected_yarn_count=len(self.loss.affected_yarns(affected_keys, factory_code, yarns)),
        )
