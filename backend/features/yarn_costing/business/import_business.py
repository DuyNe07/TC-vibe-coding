"""Nhập file: BR-41 file, BR-42 tiêu hao, BR-43 dòng lỗi, BR-44 NSM + bảng giá cũ, BR-45 quyền theo sheet,
BR-58 thành phần nguyên liệu từ file cũ, BR-59 gộp C3.1 / C3.2 / C3.3."""

from collections import Counter
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.core.exceptions import BusinessRuleViolation
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.business.loss_business import LossBusiness
from backend.features.yarn_costing.business.name_business import (
    YarnNameBusiness,
    YarnNameRule,
    collapse_spaces,
    group_key_of,
)
from backend.features.yarn_costing.business.request_business import RequestBusiness
from backend.features.yarn_costing.constants import (
    BLEND_SLOTS,
    CARDING_STAGES,
    FACTORY_SHEETS,
    LEGACY_CELLS,
    LEGACY_STAGE_COLUMNS,
    PACKAGING_STAGE_CODE,
    RECOVERY_LABELS,
    REMARK_SCREEN_ONLY,
    SHEET_LOSSES,
    SHEET_NSM,
    SHEET_PACKAGING,
    SHEET_PRICES,
    SHEET_RATES,
    SHEET_RECOVERY,
    SHEET_ROUTES,
)
from backend.features.yarn_costing.models.enums import FactoryCode, LossGroupLevel, Technology, YarnOrigin, YarnStatus
from backend.features.yarn_costing.models.import_rows import (
    ImportPlan,
    LossRow,
    NsmRow,
    ParsedWorkbook,
    RejectedRow,
    SheetPlan,
)
from backend.features.yarn_costing.models.legacy_blend import LegacyBlend, LegacyCell
from backend.features.yarn_costing.models.loss_group import LossComponent, LossGroup
from backend.features.yarn_costing.models.master_checks import FileCheck, SheetPermissionCheck
from backend.features.yarn_costing.models.packaging_type import PackagingType
from backend.features.yarn_costing.models.process_route import ProcessRoute
from backend.features.yarn_costing.models.rate_version import RateLine
from backend.features.yarn_costing.models.stage import Stage
from backend.features.yarn_costing.models.yarn import Yarn
from backend.shared.utils import normalize_key

ZERO = Decimal(0)
CLOSED = (YarnStatus.DA_HUY, YarnStatus.TU_CHOI)


class UploadFileRule(BaseBusinessRule[FileCheck]):
    code = "BR-41"
    message = "File phải là .xlsx, .xlsm hoặc .xls, không quá 60 MB và mỗi sheet không quá 10.000 dòng."

    def is_satisfied_by(self, target: FileCheck) -> bool:
        return target.extension_ok and target.size_ok and target.rows_ok


class SheetPermissionRule(BaseBusinessRule[SheetPermissionCheck]):
    code = "BR-45"
    message = "Sheet chỉ Phòng SO được cập nhật, đã bỏ qua."

    def is_satisfied_by(self, target: SheetPermissionCheck) -> bool:
        return target.allowed

    def describe_violation(self, target: SheetPermissionCheck) -> str:
        return f"Sheet '{target.sheet}' chỉ Phòng SO được cập nhật, đã bỏ qua."


def technology_of(text: str) -> Technology | None:
    value = (text or "").strip().upper()
    return Technology.MVS if value == "MVS" else Technology.RING if value == "RING" else None


def merged_carding_losses(factory: str, losses: dict[str, Decimal | None]) -> dict[str, Decimal | None]:
    """BR-59: tiêu hao C3 = số khác 0 nhỏ nhất trong các cột C3.1 / C3.2 / C3.3 (và cột C3 nếu có); không có → 0."""
    legacy = LEGACY_STAGE_COLUMNS.get(factory, {})
    if not any(code in losses for code in legacy):
        return losses
    result = {code: value for code, value in losses.items() if code not in legacy}
    for target in dict.fromkeys(legacy.values()):
        values = [v for c, v in losses.items() if v is not None and (c == target or legacy.get(c) == target)]
        non_zero = [v for v in values if v != 0]
        result[target] = min(non_zero) if non_zero else ZERO
    return result


def loss_signature(row: LossRow, factory: str) -> tuple:
    """BR-59: every column of a loss row except the C3 family (loss columns C3 / C3.1 / C3.2 / C3.3 and the
    component columns 'Other - C3.1' / 'Other - C3.2' / 'Other - C3.3' with their ratio columns)."""
    legacy = LEGACY_STAGE_COLUMNS.get(factory, {})
    family = set(legacy) | set(legacy.values())
    merged_lines = set(legacy.values())
    cells = LEGACY_CELLS.get(factory, ())
    fixed, moved = [], []
    for index, (_, _, line) in enumerate(cells):
        name = normalize_key(row.component_names[index]) if index < len(row.component_names) else ""
        ratio = row.component_ratios[index] if index < len(row.component_ratios) else None
        if line in merged_lines:
            if name or ratio is not None:
                moved.append((name, str(ratio)))
        else:
            fixed.append((name, ratio))
    return (
        collapse_spaces(row.material).casefold(),
        normalize_key(row.technology_text),
        tuple(fixed),
        tuple(sorted(moved)),
        tuple(sorted((c, v) for c, v in row.losses.items() if c not in family and v not in (None, ZERO))),
        row.has_formula,
        tuple(row.bad_values),
    )


class ImportBusiness(BaseBusiness[ParsedWorkbook]):
    def __init__(self) -> None:
        self.names = YarnNameBusiness()
        self.requests = RequestBusiness()
        self.losses = LossBusiness()
        self.costing = CostingBusiness()

    def ensure_file_valid(self, check: FileCheck) -> None:
        """BR-41."""
        UploadFileRule().check(check)

    def sheet_skip_message(self, sheet: str, is_so: bool) -> str:
        """BR-45: Xưởng chỉ được sheet NSM và tiêu hao; sheet khác bị bỏ qua với thông báo."""
        violation = SheetPermissionRule().evaluate(
            SheetPermissionCheck(sheet=sheet, allowed=is_so or sheet in FACTORY_SHEETS)
        )
        return violation.message if violation else ""

    # ------------------------------------------------------------------------------------------------------------
    def plan(
        self,
        book: ParsedWorkbook,
        factory: FactoryCode,
        is_so: bool,
        stages: Sequence[Stage],
        packaging: Sequence[PackagingType],
        routes: Sequence[ProcessRoute],
        loss_groups: Sequence[LossGroup],
        yarns: Sequence[Yarn],
        actor: str,
        now: datetime,
    ) -> ImportPlan:
        """BR-42..BR-45 applied to every sheet, in the order of UC-34; nothing is stored here."""
        plan = ImportPlan()
        allowed = {s.sheet: self.sheet_skip_message(s.sheet, is_so) for s in book.sheets}
        sheets: dict[str, SheetPlan] = {}
        rejected: list[RejectedRow] = []
        for read in book.sheets:
            sheets[read.sheet] = SheetPlan(sheet=read.sheet, read=read.read, skipped_message=allowed[read.sheet])

        def active(sheet: str) -> bool:
            return sheet in sheets and not sheets[sheet].skipped_message

        final_packaging = list(packaging)
        if active(SHEET_PACKAGING):
            final_packaging, sheets[SHEET_PACKAGING] = self._packaging(
                book, factory, packaging, sheets[SHEET_PACKAGING], rejected
            )
            plan = plan.model_copy(update={"packaging": [p for p in final_packaging if p.factory_code == factory]})
        if active(SHEET_RATES):
            own_packaging = [p for p in final_packaging if p.factory_code == factory]
            lines, sheets[SHEET_RATES] = self._rates(book, stages, own_packaging, sheets[SHEET_RATES], rejected)
            plan = plan.model_copy(update={"rate_lines": lines})
        if active(SHEET_RECOVERY):
            recovery, sheets[SHEET_RECOVERY] = self._recovery(book, sheets[SHEET_RECOVERY], rejected)
            plan = plan.model_copy(update={"recovery_rates": recovery})
        if active(SHEET_ROUTES):
            new_routes, sheets[SHEET_ROUTES] = self._routes(
                book, factory, stages, routes, sheets[SHEET_ROUTES], rejected
            )
            plan = plan.model_copy(update={"routes": new_routes})
        final_groups = {g.group_key: g for g in loss_groups if g.factory_code == factory}
        if active(SHEET_LOSSES):
            groups, sheets[SHEET_LOSSES] = self._losses(
                book, factory, is_so, stages, loss_groups, yarns, actor, sheets[SHEET_LOSSES], rejected
            )
            plan = plan.model_copy(update={"loss_groups": groups})
            final_groups.update({g.group_key: g for g in groups})
        changed: dict[str, Yarn] = {}
        nsm_codes: set[str] = set()
        if active(SHEET_NSM):
            sheets[SHEET_NSM], nsm_codes = self._nsm(
                book, factory, stages, final_groups, yarns, actor, now, changed, sheets[SHEET_NSM], rejected
            )
        if active(SHEET_PRICES):
            sheets[SHEET_PRICES], prices, codes = self._prices(
                book, factory, yarns, nsm_codes, actor, now, changed, sheets[SHEET_PRICES], rejected
            )
            plan = plan.model_copy(update={"legacy_prices": prices, "legacy_codes": codes})
        return plan.model_copy(
            update={
                "sheets": [sheets[s.sheet] for s in book.sheets],
                "rejected_rows": rejected,
                "yarns": list(changed.values()),
            }
        )

    # ---- master sheets -----------------------------------------------------------------------------------------
    def _reject(self, rejected: list[RejectedRow], sheet: str, row: int, key: str, reason: str) -> None:
        """BR-43: sheet, dòng Excel, mã / nhóm, lý do."""
        rejected.append(RejectedRow(sheet=sheet, excel_row=row, key=key, reason=reason))

    def _packaging(
        self,
        book: ParsedWorkbook,
        factory: FactoryCode,
        existing: Sequence[PackagingType],
        sheet: SheetPlan,
        rejected: list,
    ) -> tuple[list[PackagingType], SheetPlan]:
        by_code = {p.code: p for p in existing if p.factory_code == factory}
        counts = Counter(r.code for r in book.packaging_rows)
        created = updated = bad = 0
        for row in book.packaging_rows:
            if counts[row.code] > 1:
                self._reject(
                    rejected, SHEET_PACKAGING, row.excel_row, row.code, f"Mã đóng gói '{row.code}' bị trùng trong file."
                )
            elif row.minutes_per_kg is None or row.minutes_per_kg <= 0:
                self._reject(rejected, SHEET_PACKAGING, row.excel_row, row.code, "Phút/kg phải lớn hơn 0.")
            else:
                values = {
                    "name": (row.name or row.code)[:200],
                    "weight_kg": row.weight_kg,
                    "man_days": row.man_days,
                    "minutes_per_kg": row.minutes_per_kg,
                    "active": True,
                }
                if row.code in by_code:
                    by_code[row.code] = by_code[row.code].model_copy(update=values)
                    updated += 1
                else:
                    by_code[row.code] = PackagingType(factory_code=factory, code=row.code, **values)
                    created += 1
                continue
            bad += 1
        others = [p for p in existing if p.factory_code != factory]
        return others + list(by_code.values()), sheet.model_copy(
            update={"created": created, "updated": updated, "rejected": bad}
        )

    def rate_code(self, stage_value: str, group_value: str) -> str:
        """5.2: mã định mức = cột 'Công đoạn'; nếu đó là công đoạn đóng gói F thì = cột 'Nhóm công đoạn'."""
        return group_value if stage_value == PACKAGING_STAGE_CODE else stage_value

    def _rates(
        self,
        book: ParsedWorkbook,
        stages: Sequence[Stage],
        packaging: Sequence[PackagingType],
        sheet: SheetPlan,
        rejected: list,
    ) -> tuple[list[RateLine] | None, SheetPlan]:
        lines: dict[str, RateLine] = {}
        bad = 0
        for row in book.rate_rows:
            code = self.rate_code(row.stage_value, row.group_value)
            values = (row.labor, row.depreciation, row.electricity, row.materials, row.overhead)
            if not code or any(v is None or v < 0 for v in values):
                self._reject(rejected, SHEET_RATES, row.excel_row, code, "Định mức phải là số ≥ 0.")
                bad += 1
                continue
            lines[code] = RateLine(
                rate_code=code[:20],
                labor=row.labor,  # type: ignore[arg-type]
                depreciation=row.depreciation,  # type: ignore[arg-type]
                electricity=row.electricity,  # type: ignore[arg-type]
                materials=row.materials,  # type: ignore[arg-type]
                overhead=row.overhead,  # type: ignore[arg-type]
                note=row.note[:200],
            )
        required = [s.stage_code for s in stages if not s.is_packaging] + [p.code for p in packaging if p.active]
        missing = [c for c in required if c not in lines]
        if missing:
            message = f"Thiếu định mức cho: {', '.join(missing)}."
            return None, sheet.model_copy(update={"rejected": bad, "skipped_message": message})
        return list(lines.values()), sheet.model_copy(update={"created": len(lines), "rejected": bad})

    def _recovery(self, book: ParsedWorkbook, sheet: SheetPlan, rejected: list) -> tuple[dict[str, Decimal], SheetPlan]:
        result: dict[str, Decimal] = {}
        bad = 0
        for row in book.recovery_rows:
            kind = RECOVERY_LABELS.get(normalize_key(row.label))
            if kind is None:
                continue
            if row.rate is None or not ZERO <= row.rate < Decimal(1):
                self._reject(
                    rejected, SHEET_RECOVERY, row.excel_row, row.label, "Tỷ lệ hồi phế phải từ 0% đến dưới 100%."
                )
                bad += 1
                continue
            result[kind] = row.rate
        return result, sheet.model_copy(update={"updated": len(result), "rejected": bad})

    def _routes(
        self,
        book: ParsedWorkbook,
        factory: FactoryCode,
        stages: Sequence[Stage],
        existing: Sequence[ProcessRoute],
        sheet: SheetPlan,
        rejected: list,
    ) -> tuple[list[ProcessRoute], SheetPlan]:
        by_key = {(r.yarn_group, r.technology): r for r in existing if r.factory_code == factory}
        keys = Counter((group_key_of(r.yarn_group), technology_of(r.technology_text)) for r in book.route_rows)
        created = updated = bad = 0
        result: list[ProcessRoute] = []
        for row in book.route_rows:
            tech = technology_of(row.technology_text)
            key = (group_key_of(row.yarn_group), tech)
            label = f"{key[0]} - {row.technology_text}"
            count = int(row.component_count) if row.component_count is not None else None
            if tech is None:
                reason = "Phân loại phải là Ring hoặc MVS."
            elif keys[key] > 1:
                reason = f"Quy trình cho nhóm '{key[0]}' - {tech.value} bị trùng trong file."
            elif count is not None and not 1 <= count <= 5:
                reason = "Số thành phần phải từ 1 đến 5."
            else:
                values = {
                    "component_count": count,
                    "route_text": collapse_spaces(row.route_text)[:500],
                    "route_stages": self.costing.route_stage_codes(row.route_text, stages),
                }
                old = by_key.get((key[0], tech))
                if old is not None:
                    result.append(old.model_copy(update=values))
                    updated += 1
                else:
                    result.append(
                        ProcessRoute(factory_code=factory, yarn_group=key[0][:100], technology=tech, **values)
                    )
                    created += 1
                continue
            self._reject(rejected, SHEET_ROUTES, row.excel_row, label, reason)
            bad += 1
        return result, sheet.model_copy(update={"created": created, "updated": updated, "rejected": bad})

    # ---- BR-42 -------------------------------------------------------------------------------------------------
    def _losses(
        self,
        book: ParsedWorkbook,
        factory: FactoryCode,
        is_so: bool,
        stages: Sequence[Stage],
        existing: Sequence[LossGroup],
        yarns: Sequence[Yarn],
        actor: str,
        sheet: SheetPlan,
        rejected: list,
    ) -> tuple[list[LossGroup], SheetPlan]:
        """BR-42: trùng trong file → loại; S4 có tên thành phần → Thứ cấp; S1 có công thức → Nhập từ file; còn lại Sơ cấp;
        nhóm đã có → cập nhật theo quyền BR-24."""
        factory_groups = [g for g in existing if g.factory_code == factory]
        groups = {g.group_key: g for g in factory_groups}
        stage_codes = [s.stage_code for s in stages if not s.is_packaging]
        loss_rows = self.merge_duplicate_rows(book.loss_rows, factory)
        counts = Counter(group_key_of(r.yarn_group_label) for r in loss_rows)
        touched: dict[str, str] = {}
        secondary_rows = []
        bad = 0

        def reject(row_no: int, key: str, reason: str) -> None:
            nonlocal bad
            self._reject(rejected, SHEET_LOSSES, row_no, key, reason)
            bad += 1

        def can_edit(key: str) -> str:
            if key not in groups or is_so:
                return ""
            codes = self.losses.locked_codes(self.losses.affected_groups(key, factory_groups), factory.value, yarns)
            try:
                self.losses.ensure_can_edit(key, codes, is_so)
            except BusinessRuleViolation as exc:
                return exc.message
            return ""

        for row in loss_rows:
            key = group_key_of(row.yarn_group_label)
            tech = technology_of(row.technology_text)
            if counts[key] > 1:
                reject(row.excel_row, key, f"Nhóm '{key}' bị trùng trong file.")
                continue
            if tech is None:
                reject(row.excel_row, key, "Công nghệ phải là Ring hoặc MVS.")
                continue
            losses = {c: v for c, v in row.losses.items() if v is not None and c in stage_codes}
            if row.bad_values or not self.losses.losses_valid(losses):
                reject(row.excel_row, key, "Tiêu hao phải từ 0% đến dưới 100%.")
                continue
            if message := can_edit(key):
                reject(row.excel_row, key, message)
                continue
            is_secondary = factory == FactoryCode.S4 and any(n.strip() for n in row.component_names)
            level = (
                LossGroupLevel.THU_CAP
                if is_secondary
                else LossGroupLevel.NHAP_TU_FILE
                if row.has_formula
                else LossGroupLevel.SO_CAP
            )
            values = {
                "yarn_group_label": collapse_spaces(row.yarn_group_label)[:200],
                "material": collapse_spaces(row.material)[:200],
                "technology": tech,
                "level": level,
                "losses": {} if is_secondary else self.losses.manual_losses(losses, stage_codes),
                "components": [],
                "updated_by": actor,
            }
            old = groups.get(key)
            groups[key] = (
                old.model_copy(update=values) if old else LossGroup(factory_code=factory, group_key=key, **values)
            )
            touched[key] = "updated" if old else "created"
            if is_secondary:
                secondary_rows.append(row)
        primaries = {
            normalize_key(g.material_tech_key): g
            for g in reversed(list(groups.values()))
            if g.level != LossGroupLevel.THU_CAP
        }
        for row in secondary_rows:
            key = group_key_of(row.yarn_group_label)
            components: list[LossComponent] = []
            error = ""
            slots = BLEND_SLOTS.get(factory.value, ())
            for index, (name, ratio) in enumerate(zip(row.component_names, row.component_ratios, strict=False)):
                if not name.strip():
                    continue
                match = primaries.get(normalize_key(name))
                if match is None:
                    error = f"Không tìm thấy thành phần '{name.strip()}'."
                    break
                if ratio is None or not ZERO < ratio <= Decimal(1):
                    error = "Nhóm sợi pha cần từ 1 đến 5 thành phần, tổng tỷ lệ bằng 100% và không được dùng chính nó làm thành phần."
                    break
                slot = slots[index] if index < len(slots) else ""
                components.append(LossComponent(component_group_key=match.group_key, ratio=ratio, slot=slot))
            if not error:
                try:
                    self.losses.ensure_valid_components(key, components, list(groups.values()))
                except BusinessRuleViolation as exc:
                    error = exc.message
            if error:
                reject(row.excel_row, key, error)
                old = next((g for g in factory_groups if g.group_key == key), None)
                if old is not None:
                    groups[key] = old
                else:
                    groups.pop(key, None)
                touched.pop(key, None)
                continue
            groups[key] = groups[key].model_copy(update={"components": components})
        recomputed = {g.group_key: g for g in self.losses.recompute_secondaries(list(groups.values()), stages)}
        groups.update(recomputed)
        keys = set(touched) | set(recomputed)
        created = sum(1 for v in touched.values() if v == "created")
        updated = sum(1 for v in touched.values() if v == "updated")
        return [groups[k] for k in keys], sheet.model_copy(
            update={"created": created, "updated": updated, "rejected": bad}
        )

    def merge_duplicate_rows(self, rows: Sequence[LossRow], factory: FactoryCode) -> list[LossRow]:
        """BR-59: C3 của mỗi dòng = số khác 0 nhỏ nhất của C3.1 / C3.2 / C3.3; các dòng cùng group_key chỉ khác các cột
        C3.x → gộp thành một (C3 = số khác 0 nhỏ nhất của các dòng); các dòng trùng khác vẫn bị loại theo BR-42."""
        merged = [r.model_copy(update={"losses": merged_carding_losses(factory.value, r.losses)}) for r in rows]
        legacy = LEGACY_STAGE_COLUMNS.get(factory.value, {})
        if not legacy:
            return merged
        by_key: dict[str, list[int]] = {}
        for index, row in enumerate(rows):
            by_key.setdefault(group_key_of(row.yarn_group_label), []).append(index)
        drop: set[int] = set()
        targets = list(dict.fromkeys(legacy.values()))
        for indexes in by_key.values():
            if len(indexes) < 2 or len({loss_signature(rows[i], factory.value) for i in indexes}) != 1:
                continue
            losses = dict(merged[indexes[0]].losses)
            for target in targets:
                non_zero = [v for i in indexes if (v := merged[i].losses.get(target)) is not None and v != 0]
                losses[target] = min(non_zero) if non_zero else ZERO
            merged[indexes[0]] = merged[indexes[0]].model_copy(update={"losses": losses})
            drop.update(indexes[1:])
        return [r for i, r in enumerate(merged) if i not in drop]

    def row_components(
        self, row: NsmRow, factory: FactoryCode, group: LossGroup | None, groups: dict[str, LossGroup]
    ) -> list:
        """BR-58: S4 ô Cotton + C1 → C1; ô PE + C2 → C2 lượt 1; ô Other - C3.k + C3.k → C3; S1 ô PE + C1 → C1, ô
        Viscose/other + C2 → C2, ô Cotton → Không chải thô; tên nguyên liệu theo nhóm tiêu hao (xem LegacyBlend)."""
        return LegacyBlend(
            cells=[LegacyCell(cell=c, nsm_column=n, carding_stage=s) for c, n, s in LEGACY_CELLS[factory.value]],
            blend=row.blend_ratios,
            nsm=row.nsm,
            group=group,
            component_groups=groups,
            carding_codes=list(CARDING_STAGES[factory.value]),
        ).components()

    def keep_known_labels(self, components: list, old: Yarn, factory: FactoryCode) -> list:
        """A material named after its file cell ('PE', 'Other - C3.1'...) keeps the name already stored for the same
        carding line and pass (a template round trip does not rename materials)."""
        cells = {normalize_key(c) for c, _, _ in LEGACY_CELLS[factory.value]}
        by_pass = {(c.carding_stage, c.pass_no): c.material_label for c in old.components}
        taken = {normalize_key(c.material_label) for c in components}
        result = []
        for component in components:
            known = by_pass.get((component.carding_stage, component.pass_no))
            if known and normalize_key(component.material_label) in cells and normalize_key(known) not in taken:
                taken.add(normalize_key(known))
                component = component.model_copy(update={"material_label": known})
            result.append(component)
        return result

    # ---- BR-44 -------------------------------------------------------------------------------------------------
    def _nsm(
        self,
        book: ParsedWorkbook,
        factory: FactoryCode,
        stages: Sequence[Stage],
        groups: dict[str, LossGroup],
        yarns: Sequence[Yarn],
        actor: str,
        now: datetime,
        changed: dict[str, Yarn],
        sheet: SheetPlan,
        rejected: list,
    ) -> tuple[SheetPlan, set[str]]:
        """BR-44: chuẩn hoá mã, ĐCNSM trỏ về mã gốc, mã trống → cấp mã mới, mã đã có → cập nhật nếu chưa khoá."""
        by_code = {y.yarn_code: y for y in yarns}
        nsm_codes = {s.stage_code for s in stages if not s.is_packaging and not s.is_carding}
        remark = normalize_key(REMARK_SCREEN_ONLY)
        normalized = [
            self.requests.normalize_import_code(r.raw_code) if r.raw_code else ("", "", 0) for r in book.nsm_rows
        ]
        counts = Counter(code for code, _, _ in normalized if code)
        created = updated = bad = 0
        pending_new = []
        codes_in_file: set[str] = set()
        for row, (code, base, number) in zip(book.nsm_rows, normalized, strict=True):
            parsed = self.names.analyze(row.yarn_name)
            key = code or row.yarn_name
            reason = ""
            if code and counts[code] > 1:
                reason = f"Mã '{code}' bị trùng trong file."
            elif not parsed.valid:
                reason = YarnNameRule.message
            elif row.bad_values:
                reason = "NSM phải là số ≥ 0 và cần nhập ít nhất một công đoạn."
            old = by_code.get(code) if code else None
            if not reason and old is not None:
                if old.factory_code != factory:
                    reason = f"Mã '{code}' đã có ở xưởng {old.factory_code.value}."
                elif old.is_locked:
                    reason = f"Mã {code} đã có mã kế toán nên không sửa được. Muốn điều chỉnh NSM, hãy tạo bản ĐCNSM."
                elif old.status in CLOSED:
                    reason = f"Mã {code} đang ở trạng thái '{old.status.value}', không cập nhật được."
            if reason:
                self._reject(rejected, SHEET_NSM, row.excel_row, key, reason)
                bad += 1
                continue
            name = collapse_spaces(row.yarn_name)
            values = {
                "yarn_name": name,
                "yarn_group": parsed.yarn_group,
                "count": parsed.count,
                "loss_group_key": parsed.loss_group_key,
                "technology": self.names.technology(name),
                "is_compact": parsed.is_compact,
                "packaging_code": row.packaging_code or None,
                "components": self.row_components(row, factory, groups.get(parsed.loss_group_key), groups),
                "nsm": {k: v for k, v in row.nsm.items() if v > 0 and k in nsm_codes},
                "handled_by": actor,
                "handled_at": now,
            }
            if old is not None and normalize_key(row.remark) == remark:
                values["components"] = old.components  # BR-58: REMARK → thành phần giữ nguyên
            elif old is not None:
                values["components"] = self.keep_known_labels(values["components"], old, factory)  # type: ignore[arg-type]
            if old is not None:
                status = YarnStatus.CHUA_TINH_DUOC if old.status == YarnStatus.CHO_XUONG_XEM else old.status
                changed[code] = old.model_copy(update={**values, "status": status})
                updated += 1
                codes_in_file.add(code)
                continue
            fields = {**values, "origin": YarnOrigin.NHAP_TU_FILE, "status": YarnStatus.CHUA_TINH_DUOC}
            if code:
                yarn = Yarn(
                    factory_code=factory,
                    yarn_code=code,
                    base_code=base,
                    revision_no=number,
                    requested_by=actor,
                    **fields,
                )
                changed[code] = yarn
                codes_in_file.add(code)
                created += 1
            else:
                pending_new.append(fields)
        known = list(yarns) + list(changed.values())
        for fields in pending_new:
            new_code = self.requests.next_base_code(factory, known)
            yarn = Yarn(factory_code=factory, yarn_code=new_code, base_code=new_code, requested_by=actor, **fields)
            changed[new_code] = yarn
            known.append(yarn)
            codes_in_file.add(new_code)
            created += 1
        return sheet.model_copy(update={"created": created, "updated": updated, "rejected": bad}), codes_in_file

    def _prices(
        self,
        book: ParsedWorkbook,
        factory: FactoryCode,
        yarns: Sequence[Yarn],
        nsm_codes: set[str],
        actor: str,
        now: datetime,
        changed: dict[str, Yarn],
        sheet: SheetPlan,
        rejected: list,
    ) -> tuple[SheetPlan, list, list[str]]:
        """BR-44 (sheet bảng giá): mã kế toán → dòng Thường (bản bị khoá); mã không dạng '<xưởng>-N' có ở sheet NSM
        → giữ làm mã tính giá và điền mã kế toán; không có dữ liệu NSM → loại dòng; 'Ngày tính giá' → first_priced_at."""
        by_code = {y.yarn_code: y for y in yarns if y.factory_code == factory}
        seen: set[str] = set()
        prices, codes = [], []
        created = bad = 0
        for row in book.price_rows:
            code, _, _ = self.requests.normalize_import_code(row.raw_code)
            yarn = changed.get(code) or by_code.get(code)
            if code in seen:
                reason = f"Mã '{code}' bị trùng trong file."
            elif yarn is None:
                reason = f"Không có dữ liệu NSM cho mã '{code}'."
            else:
                reason = ""
            if reason:
                self._reject(rejected, SHEET_PRICES, row.excel_row, code, reason)
                bad += 1
                continue
            assert yarn is not None
            seen.add(code)
            accounting = row.accounting_code.strip()
            if (
                not accounting
                and code in nsm_codes
                and self.requests.base_number(factory.value, yarn.base_code) is None
            ):
                accounting = code
            update: dict[str, object] = {}
            if row.priced_date is not None:
                update["first_priced_at"] = row.priced_date
            if accounting:
                regular = yarn.regular_line
                if regular is None:
                    update["pending_accounting_code"] = accounting[:100]
                elif not regular.has_accounting_code:
                    line = regular.model_copy(
                        update={
                            "accounting_code": accounting[:100],
                            "accounting_code_by": actor,
                            "accounting_code_at": now,
                        }
                    )
                    update["lines"] = [line if x.line_code == regular.line_code else x for x in yarn.lines]
            if update:
                changed[code] = yarn.model_copy(update=update)
            prices.append(row)
            codes.append(code)
            created += 1
        return sheet.model_copy(update={"created": created, "rejected": bad}), prices, codes
