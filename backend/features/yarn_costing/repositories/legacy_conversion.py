"""Conversion of data stored by the previous version (before 2026-09-28) to the current models.

Old data is never deleted: rows are converted in memory when read and written in the new format on the next save.
- stages: S4 C3.1 / C3.2 / C3.3 → one stage C3; blend_slot 'Cotton' / 'PE' / ... → 'Tỷ lệ của lượt' / 'Tỷ lệ dây chuyền X';
  is_carding / max_passes added; sequences renumbered.
- loss groups: S4 losses C3.1 / C3.2 / C3.3 → C3 = lowest non-zero value (BR-59).
- rate versions: S4 version without a 'C3' line gets one copied from its first C3.x line (same rate as before).
- yarns: blend_ratios + carding NSM → components (BR-58 mapping); old stage details C3.k → C3 pass k.
"""

from decimal import Decimal
from typing import Any

from backend.features.yarn_costing.constants import (
    CARDING_STAGES,
    LEGACY_CELLS,
    LEGACY_SLOT_LINES,
    LEGACY_STAGE_COLUMNS,
    SEED_STAGES,
)
from backend.features.yarn_costing.models.legacy_blend import LegacyBlend, LegacyCell
from backend.features.yarn_costing.models.loss_group import LossGroup
from backend.features.yarn_costing.models.stage import LINE_RATIO_PREFIX, NO_BLEND_SLOT, PASS_RATIO_SLOT

Raw = dict[str, Any]


def _seed_row(factory: str, code: str) -> tuple | None:
    return next((row for row in SEED_STAGES.get(factory, ()) if row[1] == code), None)


def needs_stage_conversion(raw: list[Raw]) -> bool:
    return any("is_carding" not in item for item in raw)


def convert_stages(raw: list[Raw]) -> list[Raw]:
    result: list[Raw] = []
    for factory in sorted({item["factory_code"] for item in raw}):
        legacy = LEGACY_STAGE_COLUMNS.get(factory, {})
        carding = CARDING_STAGES.get(factory, ())
        slot_lines = LEGACY_SLOT_LINES.get(factory, {})
        rows = sorted((dict(i) for i in raw if i["factory_code"] == factory), key=lambda r: r.get("sequence", 0))
        codes = {r["stage_code"] for r in rows}
        converted: list[Raw] = []
        for row in rows:
            code = row["stage_code"]
            if code in legacy:
                target = legacy[code]
                if target in codes:
                    continue
                codes.add(target)
                seed = _seed_row(factory, target)
                row |= {"stage_code": target, "stage_group": target}
                if seed is not None:
                    row["stage_name"] = seed[2]
                code = target
            if "is_carding" not in row:
                is_carding = code in carding
                seed = _seed_row(factory, code)
                row["is_carding"] = is_carding
                row["max_passes"] = (seed[10] if seed is not None and seed[10] else 3) if is_carding else None
                slot = row.get("blend_slot") or NO_BLEND_SLOT
                if slot != NO_BLEND_SLOT and not slot.startswith(LINE_RATIO_PREFIX) and slot != PASS_RATIO_SLOT:
                    line = slot_lines.get(slot)
                    slot = PASS_RATIO_SLOT if is_carding else (LINE_RATIO_PREFIX + line if line else NO_BLEND_SLOT)
                row["blend_slot"] = slot
            cumulative = [legacy.get(c, c) for c in row.get("cumulative_stages", [])]
            row["cumulative_stages"] = [c for c in dict.fromkeys(cumulative) if c != code]
            converted.append(row)
        for sequence, row in enumerate(converted, start=1):
            row["sequence"] = sequence
        result += converted
    return result


def merge_legacy_losses(factory: str, losses: dict[str, Any]) -> dict[str, Any]:
    """BR-59: C3 = lowest non-zero value of C3 / C3.1 / C3.2 / C3.3 (no value → 0, not stored)."""
    legacy = LEGACY_STAGE_COLUMNS.get(factory, {})
    if not any(code in losses for code in legacy):
        return losses
    result = {code: value for code, value in losses.items() if code not in legacy}
    for target in dict.fromkeys(legacy.values()):
        values = [Decimal(str(v)) for c, v in losses.items() if (c == target or legacy.get(c) == target)]
        non_zero = [v for v in values if v != 0]
        result.pop(target, None)
        if non_zero:
            result[target] = str(min(non_zero))
    return result


def convert_loss_group(item: Raw) -> Raw:
    losses = item.get("losses") or {}
    merged = merge_legacy_losses(item["factory_code"], losses)
    return item if merged is losses else item | {"losses": merged}


def convert_rate_version(item: Raw) -> Raw:
    legacy = LEGACY_STAGE_COLUMNS.get(item["factory_code"], {})
    lines = list(item.get("lines") or [])
    codes = {line["rate_code"] for line in lines}
    added = []
    for target in dict.fromkeys(legacy.values()):
        source = next(
            (line for line in lines if line["rate_code"] in legacy and legacy[line["rate_code"]] == target), None
        )
        if target not in codes and source is not None:
            added.append(source | {"rate_code": target})
    return item | {"lines": lines + added} if added else item


def needs_yarn_conversion(item: Raw) -> bool:
    factory = item.get("factory_code", "")
    carding = set(CARDING_STAGES.get(factory, ())) | set(LEGACY_STAGE_COLUMNS.get(factory, {}))
    return "blend_ratios" in item or any(code in carding for code in item.get("nsm") or {})


def convert_yarn(item: Raw, groups: dict[str, LossGroup]) -> Raw:
    factory = item["factory_code"]
    carding = set(CARDING_STAGES.get(factory, ())) | set(LEGACY_STAGE_COLUMNS.get(factory, {}))
    nsm = {k: Decimal(str(v)) for k, v in (item.get("nsm") or {}).items()}
    blend = {k: Decimal(str(v)) for k, v in (item.get("blend_ratios") or {}).items()}
    legacy = LegacyBlend(
        cells=[LegacyCell(cell=c, nsm_column=n, carding_stage=s) for c, n, s in LEGACY_CELLS.get(factory, ())],
        blend=blend,
        nsm=nsm,
        group=groups.get(item.get("loss_group_key", "")),
        component_groups=groups,
        carding_codes=list(CARDING_STAGES.get(factory, ())),
    )
    converted = {k: v for k, v in item.items() if k != "blend_ratios"}
    if "components" not in item:
        converted["components"] = [c.model_dump(mode="json") for c in legacy.components()]
    converted["nsm"] = {k: v for k, v in (item.get("nsm") or {}).items() if k not in carding}
    stage_map = LEGACY_STAGE_COLUMNS.get(factory, {})
    details = []
    for detail in item.get("stage_details") or []:
        code = detail.get("stage_code", "")
        if code in stage_map:
            suffix = code.rsplit(".", 1)[-1]
            detail = detail | {"stage_code": stage_map[code], "pass_no": int(suffix) if suffix.isdigit() else None}
        details.append(detail)
    if details:
        converted["stage_details"] = details
    return converted
