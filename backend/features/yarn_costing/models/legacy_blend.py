"""Old Excel layout of blend ratios + carding NSM (5.2 sheet '1. Input NSM') → yarn components (4.12.1, BR-58).

Used by the file import (BR-58) and by the conversion of data stored by the previous version (repositories).
"""

from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseValueObject
from backend.features.yarn_costing.models.loss_group import LossComponent, LossGroup
from backend.features.yarn_costing.models.yarn import YarnComponent
from backend.shared.utils import normalize_key

ZERO = Decimal(0)
ONE = Decimal(1)


class LegacyCell(BaseValueObject):
    cell: str  # blend-ratio cell of the old file, e.g. "Other - C3.3"
    nsm_column: str = ""  # NSM column of the old file, e.g. "C3.3" ("" = no carding NSM)
    carding_stage: str = ""  # carding line of the new model ("" = Không chải thô)


class LegacyBlend(BaseValueObject):
    cells: list[LegacyCell]
    blend: dict[str, Decimal] = Field(default_factory=dict)
    nsm: dict[str, Decimal] = Field(default_factory=dict)
    group: LossGroup | None = None
    component_groups: dict[str, LossGroup] = Field(default_factory=dict)
    carding_codes: list[str] = Field(default_factory=list)

    def _ratio(self, cell: LegacyCell) -> Decimal:
        return min(max(self.blend.get(cell.cell, ZERO), ZERO), ONE)

    def _nsm(self, cell: LegacyCell) -> Decimal:
        return self.nsm.get(cell.nsm_column, ZERO) if cell.nsm_column else ZERO

    def present_cells(self) -> list[LegacyCell]:
        """BR-58: ô tỷ lệ = 0 và NSM = 0 thì không tạo thành phần."""
        return [c for c in self.cells if self._ratio(c) > 0 or self._nsm(c) > 0]

    def _component_for(self, cell: LegacyCell, used: set[str]) -> LossComponent | None:
        group = self.group
        if group is None:
            return None
        free = [c for c in group.components if c.component_group_key not in used]
        exact = next((c for c in free if c.slot and c.slot == cell.cell), None)
        if exact is not None:
            return exact
        free = [c for c in free if not c.slot]

        def runs_here(component: LossComponent) -> bool:
            source = self.component_groups.get(component.component_group_key)
            lines = source.carding_lines_with_loss(self.carding_codes) if source else []
            return cell.carding_stage in lines if cell.carding_stage else not lines

        candidates = [c for c in free if runs_here(c)]
        ratio = self._ratio(cell)
        return next((c for c in candidates if c.ratio == ratio), candidates[0] if candidates else None)

    def _label(self, component: LossComponent) -> str:
        source = self.component_groups.get(component.component_group_key)
        return source.material_label if source else component.component_group_key

    def components(self) -> list[YarnComponent]:
        """BR-58: material = material_tech_key of the loss group component in that cell (secondary group), the material
        of the group (primary group, single carding material), otherwise the cell name."""
        present = self.present_cells()
        carding_count = sum(1 for c in present if c.carding_stage)
        group = self.group
        single_material = (
            group is not None
            and not group.components
            and carding_count == 1
            and len(group.carding_lines_with_loss(self.carding_codes)) <= 1
        )
        used: set[str] = set()
        labels: set[str] = set()
        passes: dict[str, int] = {}
        result: list[YarnComponent] = []
        for cell in present:
            label = cell.cell
            if group is not None and group.components:
                match = self._component_for(cell, used)
                if match is not None:
                    used.add(match.component_group_key)
                    label = self._label(match)
            elif single_material and cell.carding_stage and group is not None:
                label = group.material_label
            if normalize_key(label) in labels:
                label = cell.cell
            labels.add(normalize_key(label))
            pass_no = None
            if cell.carding_stage:
                passes[cell.carding_stage] = passes.get(cell.carding_stage, 0) + 1
                pass_no = passes[cell.carding_stage]
            result.append(
                YarnComponent(
                    material_label=label[:200],
                    ratio=self._ratio(cell),
                    carding_stage=cell.carding_stage,
                    pass_no=pass_no,
                    nsm_carding=self._nsm(cell) if cell.carding_stage else None,
                )
            )
        return result
