"""UC-33 file mẫu (5.3): 7 sheet đúng tên bảng 5.2 với dữ liệu hiện tại của xưởng (sheet bảng giá chỉ có tiêu đề)."""

from decimal import Decimal

from backend.core.base import BaseBuilder, FileDownloadDTO, MimeType
from backend.features.yarn_costing.constants import (
    BLEND_SLOTS,
    COL_ACCOUNTING,
    COL_ACCOUNTING_2,
    COL_COMPONENT_COUNT,
    COL_DEPRECIATION,
    COL_ELECTRICITY,
    COL_LABOR,
    COL_MAN_DAYS,
    COL_MATERIAL,
    COL_MATERIALS,
    COL_MINUTES,
    COL_NOTE,
    COL_OVERHEAD,
    COL_PACKAGING_CODE,
    COL_PACKAGING_NAME,
    COL_PRICED_DATE,
    COL_REMARK,
    COL_ROUTE,
    COL_ROUTE_TECH,
    COL_SO_CHECK,
    COL_STAGE,
    COL_STAGE_GROUP,
    COL_STAGE_NAME,
    COL_STT,
    COL_TECHNOLOGY,
    COL_TOTAL,
    COL_WEIGHT,
    COL_YARN_CODE,
    COL_YARN_GROUP,
    COL_YARN_NAME,
    LEGACY_CELLS,
    LEGACY_STAGE_COLUMNS,
    RATIO_SUFFIX,
    RECOVERY_COLUMN,
    RECOVERY_LABEL_TEXT,
    REMARK_SCREEN_ONLY,
    SHEET_LOSSES,
    SHEET_NSM,
    SHEET_PACKAGING,
    SHEET_PRICES,
    SHEET_RATES,
    SHEET_RECOVERY,
    SHEET_ROUTES,
)
from backend.features.yarn_costing.models.enums import FactoryCode
from backend.features.yarn_costing.models.loss_group import LossGroup
from backend.features.yarn_costing.models.packaging_type import PackagingType
from backend.features.yarn_costing.models.process_route import ProcessRoute
from backend.features.yarn_costing.models.rate_version import RateVersion
from backend.features.yarn_costing.models.recovery_rate import RecoveryRate
from backend.features.yarn_costing.models.stage import Stage
from backend.features.yarn_costing.models.yarn import Yarn
from backend.shared.file_io import ExcelWriter


def num(value: object) -> float | None:
    return float(value) if value is not None else None  # type: ignore[arg-type]


def with_header(rows: list[dict], headers: list[str]) -> list[dict]:
    """ExcelWriter takes headers from the first row: keep them even without data."""
    return rows or [dict.fromkeys(headers)]


class TemplateFileBuilder(BaseBuilder[FileDownloadDTO]):
    def __init__(
        self,
        factory: FactoryCode,
        stages: list[Stage],
        version: RateVersion | None,
        packaging: list[PackagingType],
        recovery: list[RecoveryRate],
        routes: list[ProcessRoute],
        groups: list[LossGroup],
        yarns: list[Yarn],
    ) -> None:
        self.factory, self.stages, self.version = factory, sorted(stages, key=lambda s: s.sequence), version
        self.packaging, self.recovery, self.routes, self.groups, self.yarns = packaging, recovery, routes, groups, yarns

    def build(self) -> FileDownloadDTO:
        slots = list(BLEND_SLOTS[self.factory.value])
        nsm_codes = [s.stage_code for s in self.stages if not s.is_packaging]
        sheets = {
            SHEET_RATES: self._rates(),
            SHEET_RECOVERY: with_header(
                [
                    {
                        COL_STT: i,
                        COL_STAGE_NAME: RECOVERY_LABEL_TEXT[r.recovery_type.value],
                        RECOVERY_COLUMN[self.factory.value]: num(r.rate),
                    }
                    for i, r in enumerate(self.recovery, 1)
                    if r.recovery_type.value in RECOVERY_LABEL_TEXT
                ],
                [COL_STT, COL_STAGE_NAME, RECOVERY_COLUMN[self.factory.value]],
            ),
            SHEET_PACKAGING: with_header(
                [
                    {
                        COL_STT: i,
                        COL_PACKAGING_NAME: p.name,
                        COL_PACKAGING_CODE: p.code,
                        COL_WEIGHT: num(p.weight_kg),
                        COL_MAN_DAYS: num(p.man_days),
                        COL_MINUTES: num(p.minutes_per_kg),
                    }
                    for i, p in enumerate(self.packaging, 1)
                ],
                [COL_STT, COL_PACKAGING_NAME, COL_PACKAGING_CODE, COL_WEIGHT, COL_MAN_DAYS, COL_MINUTES],
            ),
            SHEET_ROUTES: with_header(
                [
                    {
                        COL_STT: i,
                        COL_YARN_GROUP: r.yarn_group,
                        COL_ROUTE_TECH: r.technology.value,
                        COL_COMPONENT_COUNT: r.component_count,
                        COL_ROUTE: r.route_text,
                    }
                    for i, r in enumerate(self.routes, 1)
                ],
                [COL_STT, COL_YARN_GROUP, COL_ROUTE_TECH, COL_COMPONENT_COUNT, COL_ROUTE],
            ),
            SHEET_LOSSES: self._losses(slots, nsm_codes),
            SHEET_NSM: self._nsm(slots, nsm_codes),
            SHEET_PRICES: [
                dict.fromkeys(
                    [
                        COL_STT,
                        COL_ACCOUNTING,
                        COL_YARN_NAME,
                        COL_LABOR,
                        COL_DEPRECIATION,
                        COL_ELECTRICITY,
                        COL_MATERIALS,
                        COL_OVERHEAD,
                        COL_TOTAL,
                        COL_PRICED_DATE,
                        COL_SO_CHECK,
                        COL_ACCOUNTING_2,
                    ]
                )
            ],
        }
        content = ExcelWriter().write(sheets)
        return FileDownloadDTO(
            filename=f"mau-du-lieu-tinh-gia-{self.factory.value}.xlsx", content=content, mime_type=MimeType.XLSX
        )

    def _rates(self) -> list[dict]:
        names = {s.stage_code: (s.stage_name, s.stage_group) for s in self.stages}
        names |= {p.code: ("Hoàn tất, đóng gói", p.code) for p in self.packaging}
        headers = [
            COL_STT,
            COL_STAGE,
            COL_STAGE_NAME,
            COL_STAGE_GROUP,
            COL_LABOR,
            COL_DEPRECIATION,
            COL_ELECTRICITY,
            COL_MATERIALS,
            COL_OVERHEAD,
            COL_NOTE,
        ]
        if self.version is not None:
            source = [(line.rate_code, line) for line in self.version.lines]
        else:
            codes = [s.stage_code for s in self.stages if not s.is_packaging] + [p.code for p in self.packaging]
            source = [(code, None) for code in codes]
        rows = []
        for i, (code, line) in enumerate(source, 1):
            name, group = names.get(code, ("", code))
            rows.append(
                {
                    COL_STT: i,
                    COL_STAGE: code,
                    COL_STAGE_NAME: name,
                    COL_STAGE_GROUP: group,
                    COL_LABOR: num(line.labor) if line else None,
                    COL_DEPRECIATION: num(line.depreciation) if line else None,
                    COL_ELECTRICITY: num(line.electricity) if line else None,
                    COL_MATERIALS: num(line.materials) if line else None,
                    COL_OVERHEAD: num(line.overhead) if line else None,
                    COL_NOTE: line.note if line else "",
                }
            )
        return with_header(rows, headers)

    def _losses(self, slots: list[str], nsm_codes: list[str]) -> list[dict]:
        """5.3: one loss column per stage of the factory in sequence order (S4: a single 'C3' column)."""
        by_key = {g.group_key: g for g in self.groups}
        with_components = self.factory == FactoryCode.S4
        headers = [COL_STT, COL_YARN_GROUP, COL_MATERIAL, COL_TECHNOLOGY]
        if with_components:
            headers += slots + [s + RATIO_SUFFIX for s in slots]
        headers += nsm_codes
        rows = []
        for i, g in enumerate(self.groups, 1):
            row: dict = dict.fromkeys(headers)
            row.update(
                {
                    COL_STT: i,
                    COL_YARN_GROUP: g.yarn_group_label,
                    COL_MATERIAL: g.material,
                    COL_TECHNOLOGY: g.technology.value,
                }
            )
            if with_components:
                free = [s for s in slots if s not in {c.slot for c in g.components}]
                for component in g.components:
                    slot = component.slot if component.slot in slots else (free.pop(0) if free else None)
                    if slot is None:
                        continue
                    source = by_key.get(component.component_group_key)
                    row[slot] = source.material_tech_key if source else component.component_group_key
                    row[slot + RATIO_SUFFIX] = num(component.ratio)
            if not (with_components and g.components):
                row.update({code: num(g.losses[code]) for code in nsm_codes if code in g.losses})
            rows.append(row)
        return with_header(rows, headers)

    def _nsm_columns(self) -> list[str]:
        """5.3: the NSM columns of the current file layout (S4: C3 → C3.1 / C3.2 / C3.3)."""
        legacy = LEGACY_STAGE_COLUMNS.get(self.factory.value, {})
        columns: list[str] = []
        for stage in self.stages:
            if stage.is_packaging:
                continue
            olds = [old for old, new in legacy.items() if new == stage.stage_code]
            columns += olds or [stage.stage_code]
        return columns

    def _cells_of(self, yarn: Yarn) -> dict[str, tuple[Decimal, Decimal | None, str]] | None:
        """5.3: component → (ratio cell, NSM column); None when a component does not fit the file layout."""
        cells = LEGACY_CELLS.get(self.factory.value, ())
        by_line: dict[str, list[tuple[str, str]]] = {}
        for cell, column, line in cells:
            by_line.setdefault(line, []).append((cell, column))
        used: dict[str, int] = {}
        result: dict[str, tuple[Decimal, Decimal | None, str]] = {}
        for component in yarn.components:
            line = component.carding_stage
            index = used.get(line, 0)
            slots = by_line.get(line, [])
            if index >= len(slots):
                return None
            used[line] = index + 1
            cell, column = slots[index]
            result[cell] = (component.ratio, component.nsm_carding if line else None, column)
        return result

    def _nsm(self, slots: list[str], nsm_codes: list[str]) -> list[dict]:
        columns = self._nsm_columns()
        headers = [COL_STT, COL_YARN_CODE, COL_YARN_NAME, *slots, *columns, COL_PACKAGING_NAME, COL_REMARK]
        carding = {s.stage_code for s in self.stages if s.is_carding}
        rows = []
        for i, y in enumerate(self.yarns, 1):
            row: dict = dict.fromkeys(headers)
            row.update(
                {
                    COL_STT: i,
                    COL_YARN_CODE: y.yarn_code,
                    COL_YARN_NAME: y.yarn_name,
                    COL_PACKAGING_NAME: y.packaging_code,
                }
            )
            row.update({code: num(y.nsm[code]) for code in nsm_codes if code in y.nsm and code not in carding})
            cells = self._cells_of(y)
            if cells is None:
                row[COL_REMARK] = REMARK_SCREEN_ONLY
            else:
                for cell, (ratio, nsm, column) in cells.items():
                    row[cell] = num(ratio)
                    if column and nsm is not None:
                        row[column] = num(nsm)
            rows.append(row)
        return with_header(rows, headers)
