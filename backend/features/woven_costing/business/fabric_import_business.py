"""UC-01 / UC-02: BR-01 merge Peace / WFX, BR-02 codes, BR-04 yarns, BR-05 ratio check, BR-71 valid codes only."""

from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.woven_costing.business.fabric_business import FabricBusiness
from backend.features.woven_costing.constants import RATIO_TOLERANCE
from backend.features.woven_costing.models.enums import FabricSource, ImportResult
from backend.features.woven_costing.models.fabric import Fabric, FabricYarn
from backend.features.woven_costing.models.fabric_import import (
    FabricFileContent,
    FabricImportOutcome,
    FabricImportRow,
    WeavingRecord,
    YarnRecord,
)

PRIORITY = (FabricSource.PEACE, FabricSource.WFX)


class FabricImportBusiness(BaseBusiness[FabricFileContent]):
    def __init__(self) -> None:
        self.fabric = FabricBusiness()

    def _group(
        self, files: list[FabricFileContent], errors: dict[str, str]
    ) -> tuple[
        dict[FabricSource, dict[str, tuple[WeavingRecord, str]]], dict[FabricSource, dict[str, list[YarnRecord]]]
    ]:
        """BR-02 on every row; rows grouped by system and clean code (invalid codes are reported, BR-71)."""
        specs: dict[FabricSource, dict[str, tuple[WeavingRecord, str]]] = {s: {} for s in PRIORITY}
        yarns: dict[FabricSource, dict[str, list[YarnRecord]]] = {s: {} for s in PRIORITY}
        for content in files:
            rows = content.weaving_rows if content.is_weaving else content.yarn_rows
            for row in rows:
                check = self.fabric.code_check(row.raw_code)
                if not check.ok:
                    errors.setdefault(row.raw_code.strip(), self.fabric.collect_violations(check)[0].message)
                    continue
                code, sy_item = self.fabric.clean_code(row.raw_code)
                if content.is_weaving and isinstance(row, WeavingRecord):
                    specs[content.system].setdefault(code, (row, sy_item))
                elif isinstance(row, YarnRecord):
                    yarns[content.system].setdefault(code, []).append(row)
        return specs, yarns

    def merge(self, files: list[FabricFileContent], stored: dict[str, Fabric], user: str) -> FabricImportOutcome:
        """BR-01: a code in Peace and WFX takes every spec and yarn from Peace; WFX only -> WFX. Stored "Nhập tay" codes
        are overwritten by the files; stored codes missing from the files are kept. Existing warping loss is kept."""
        errors: dict[str, str] = {}
        specs, yarns = self._group(files, errors)
        codes = sorted(set().union(*[set(specs[s]) | set(yarns[s]) for s in PRIORITY]))
        outcome_rows: list[FabricImportRow] = []
        to_save: list[Fabric] = []
        counts = dict.fromkeys(ImportResult, 0)
        for code in codes:
            system = next((s for s in PRIORITY if code in specs[s] or code in yarns[s]), FabricSource.WFX)
            other = PRIORITY[1] if system == PRIORITY[0] else PRIORITY[0]
            spec_pair = specs[system].get(code) or specs[other].get(code)
            yarn_list = self.fabric.normalize_yarns(yarns[system].get(code) or yarns[other].get(code, []))
            old = stored.get(code)
            fabric = self._build(code, system, spec_pair, yarn_list, old, user)
            if fabric is None:
                errors.setdefault(code, f"Mã vải {code} không có thông số (Weaving control) và chưa có trong dữ liệu.")
                continue
            result, reason = self._compare(fabric, old)
            if result != ImportResult.UNCHANGED:
                to_save.append(fabric)
            counts[result] += 1
            if not fabric.yarns:
                counts[ImportResult.MISSING_YARN] += 1
                reason = "; ".join(r for r in (reason, "Có thông số nhưng không có dòng sợi") if r)
            elif abs(fabric.ratio_total - Decimal(1)) > RATIO_TOLERANCE:
                reason = "; ".join(r for r in (reason, f"Tổng tỷ lệ sợi = {fabric.ratio_total * 100:.2f}%") if r)
            outcome_rows.append(FabricImportRow(tcfno=code, fabric_name=fabric.fabric_name, source=system.value,
                                                result=result if fabric.yarns else ImportResult.MISSING_YARN,
                                                reason=reason))  # fmt: skip
        for raw, message in errors.items():
            outcome_rows.append(FabricImportRow(tcfno=raw, result=ImportResult.ERROR, reason=message))
        return FabricImportOutcome(
            to_save=to_save,
            rows=outcome_rows,
            new_count=counts[ImportResult.NEW],
            changed_count=counts[ImportResult.CHANGED],
            unchanged_count=counts[ImportResult.UNCHANGED],
            missing_yarn_count=counts[ImportResult.MISSING_YARN],
            error_count=len(errors),
        )

    def _build(
        self,
        code: str,
        system: FabricSource,
        spec_pair: tuple[WeavingRecord, str] | None,
        yarns: list[FabricYarn],
        old: Fabric | None,
        user: str,
    ) -> Fabric | None:
        if spec_pair is None and old is None:
            return None
        if spec_pair is None and old is not None:
            return old.model_copy(update={"yarns": yarns or old.yarns, "source": system, "updated_by": user})
        record, sy_item = spec_pair  # type: ignore[misc]
        specs = record.specs
        if old is not None:
            specs = specs.model_copy(update={"warping_loss_rate": old.specs.warping_loss_rate})
        values = {
            "tcfno": code, "tcfno_raw": record.raw_code.strip()[:40], "sy_item": sy_item[:30],
            "fabric_name": (record.fabric_name or code)[:300], "structure": record.structure,
            "fabric_kind": record.fabric_kind, "tcfno_status": record.tcfno_status, "created_date": record.created_date,
            "in_charge": record.in_charge, "specs": specs, "source": system, "remark": record.remark[:500],
            "updated_by": user, "yarns": yarns,
        }  # fmt: skip
        if old is not None:
            return old.model_copy(update=values)
        return Fabric(**values)

    def _compare(self, fabric: Fabric, old: Fabric | None) -> tuple[ImportResult, str]:
        if old is None:
            return ImportResult.NEW, ""
        keys = ("fabric_name", "specs", "yarns", "source", "structure", "fabric_kind", "tcfno_status", "remark")
        changed = [k for k in keys if getattr(fabric, k) != getattr(old, k)]
        if not changed:
            return ImportResult.UNCHANGED, ""
        if old.source == FabricSource.MANUAL:
            return ImportResult.CHANGED, "Mã nhập tay được thay bằng dữ liệu file"
        return ImportResult.CHANGED, ""
