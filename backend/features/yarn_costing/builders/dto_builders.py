"""Models → DTOs (no decisions: values computed by business are passed in)."""

from decimal import Decimal

from backend.core.base import BaseBuilder
from backend.features.yarn_costing.constants import FACTORY_NAMES, NO_CARDING_LABEL
from backend.features.yarn_costing.dto.common_dto import RecalcBatchDTO, YarnComponentDTO
from backend.features.yarn_costing.dto.loss_dto import ComponentRowDTO, LossGroupDTO
from backend.features.yarn_costing.dto.master_dto import (
    PackagingRowDTO,
    ProcessRouteRowDTO,
    RateLineRowDTO,
    RecoveryRowDTO,
    StageRowDTO,
)
from backend.features.yarn_costing.dto.pricing_dto import PriceHistoryDTO, PriceLineDTO, StageCostDTO
from backend.features.yarn_costing.dto.reference_dto import ExchangeRateDTO, FactoryDTO, RateVersionDTO
from backend.features.yarn_costing.dto.request_dto import YarnDTO, YarnSummaryDTO
from backend.features.yarn_costing.dto.user_dto import GroupMemberRowDTO, UserGroupDTO
from backend.features.yarn_costing.models.enums import FactoryCode, YarnStatus
from backend.features.yarn_costing.models.exchange_rate import ExchangeRate
from backend.features.yarn_costing.models.loss_group import LossGroup
from backend.features.yarn_costing.models.packaging_type import PackagingType
from backend.features.yarn_costing.models.price_history import PriceHistory
from backend.features.yarn_costing.models.process_route import ProcessRoute
from backend.features.yarn_costing.models.rate_version import RateLine, RateVersion
from backend.features.yarn_costing.models.recalc_batch import RecalcBatch
from backend.features.yarn_costing.models.recovery_rate import RecoveryRate
from backend.features.yarn_costing.models.stage import Stage
from backend.features.yarn_costing.models.user_group import UserGroup
from backend.features.yarn_costing.models.yarn import PriceLine, StageCostDetail, Yarn, YarnComponent


def usd(total: Decimal | None, rate: Decimal | None) -> Decimal | None:
    return total / rate if total is not None and rate else None


def group_dto(group: UserGroup) -> UserGroupDTO:
    return UserGroupDTO(
        code=group.code.value,
        name=group.name,
        factory_code=group.factory_code.value if group.factory_code else None,
        active=group.active,
        members=[GroupMemberRowDTO(name=m.name, active=m.active) for m in group.members],
        active_member_names=group.active_member_names,
        member_count=len(group.members),
    )


def components_from_rows(rows: list[YarnComponentDTO]) -> list[YarnComponent]:
    """Rows of the component table → models (empty rows skipped, 'Không chải thô' = no carding line)."""
    result = []
    for row in rows:
        label = " ".join((row.material_label or "").split())
        if not label:
            continue
        line = (row.carding_stage or "").strip()
        line = "" if line == NO_CARDING_LABEL else line
        result.append(
            YarnComponent(
                material_label=label[:200],
                ratio=row.ratio if row.ratio is not None else Decimal(0),
                carding_stage=line,
                nsm_carding=row.nsm_carding if line else None,
            )
        )
    return result


def factory_dto(code: FactoryCode, carding_stages: list[str], default_packaging_code: str | None = None) -> FactoryDTO:
    return FactoryDTO(
        code=code,
        name=FACTORY_NAMES[code.value],
        carding_stages=carding_stages,
        code_prefix=f"{code.value}-",
        default_packaging_code=default_packaging_code,
    )


def component_dto(component: YarnComponent, reference_nsm: Decimal | None = None) -> YarnComponentDTO:
    return YarnComponentDTO(
        material_label=component.material_label,
        ratio=component.ratio,
        carding_stage=component.carding_stage,
        pass_no=component.pass_no,
        nsm_carding=component.nsm_carding,
        reference_nsm=reference_nsm,
    )


def stage_row(stage: Stage) -> StageRowDTO:
    return StageRowDTO(**stage.model_dump(exclude={"id", "created_at", "updated_at"}))


def rate_row(line: RateLine, factory_code: FactoryCode | None = None) -> RateLineRowDTO:
    return RateLineRowDTO(
        factory_code=factory_code,
        rate_code=line.rate_code,
        labor=line.labor,
        depreciation=line.depreciation,
        electricity=line.electricity,
        materials=line.materials,
        overhead=line.overhead,
        note=line.note,
        total_rate=line.total_rate,
    )


def rate_version_dto(version: RateVersion) -> RateVersionDTO:
    return RateVersionDTO(
        version_code=version.version_code,
        factory_code=version.factory_code,
        effective_date=version.effective_date,
        reason=version.reason,
        created_by=version.created_by,
        created_at=version.created_at,
        lines=[rate_row(line, version.factory_code) for line in version.lines],
    )


def packaging_row(packaging: PackagingType, has_rate: bool, selectable: bool) -> PackagingRowDTO:
    return PackagingRowDTO(
        factory_code=packaging.factory_code,
        code=packaging.code,
        name=packaging.name,
        weight_kg=packaging.weight_kg,
        man_days=packaging.man_days,
        minutes_per_kg=packaging.minutes_per_kg,
        active=packaging.active,
        is_default=packaging.is_default,
        has_rate=has_rate,
        selectable=selectable,
    )


def recovery_row(rate: RecoveryRate) -> RecoveryRowDTO:
    return RecoveryRowDTO(factory_code=rate.factory_code, recovery_type=rate.recovery_type, rate=rate.rate)


def route_row(route: ProcessRoute) -> ProcessRouteRowDTO:
    return ProcessRouteRowDTO(
        factory_code=route.factory_code,
        yarn_group=route.yarn_group,
        technology=route.technology,
        component_count=route.component_count,
        route_text=route.route_text,
        route_stages=route.route_stages,
    )


def exchange_rate_dto(rate: ExchangeRate) -> ExchangeRateDTO:
    return ExchangeRateDTO(
        effective_date=rate.effective_date,
        rate=rate.rate,
        note=rate.note,
        created_by=rate.created_by,
        created_at=rate.created_at,
    )


def batch_dto(batch: RecalcBatch) -> RecalcBatchDTO:
    return RecalcBatchDTO(
        batch_id=batch.batch_code,
        factory_code=batch.factory_code,
        trigger=batch.trigger,
        effective_date=batch.effective_date,
        reason=batch.reason,
        run_by=batch.run_by,
        run_at=batch.run_at,
        yarn_count=batch.yarn_count,
        changed_line_count=batch.changed_line_count,
        failed_yarn_count=batch.failed_yarn_count,
    )


def line_dto(yarn: Yarn, line: PriceLine, rate: Decimal | None) -> PriceLineDTO:
    c = line.cost
    return PriceLineDTO(
        yarn_code=yarn.yarn_code,
        line_code=line.line_code,
        line_type=line.line_type,
        adjustment_percent=line.adjustment_percent,
        adjustment_reason=line.adjustment_reason,
        order_ref=line.order_ref,
        labor=c.labor,
        depreciation=c.depreciation,
        electricity=c.electricity,
        materials=c.materials,
        overhead=c.overhead,
        total_vnd=c.total,
        usd_per_kg=usd(c.total, rate),
        accounting_code=line.accounting_code,
        accounting_code_by=line.accounting_code_by,
        accounting_code_at=line.accounting_code_at,
        created_by=line.created_by,
        created_at=line.created_at,
    )


def stage_cost_dto(detail: StageCostDetail) -> StageCostDTO:
    c = detail.cost
    return StageCostDTO(
        sequence=detail.sequence,
        stage_code=detail.stage_code,
        stage_name=detail.stage_name,
        material_label=detail.material_label,
        pass_no=detail.pass_no,
        nsm=detail.nsm,
        run_minutes=detail.run_minutes,
        loss=detail.loss,
        loss_note=detail.loss_note,
        cumulative_loss=detail.cumulative_loss,
        total_rate=detail.total_rate,
        cost_per_kg=c.total,
        labor=c.labor,
        depreciation=c.depreciation,
        electricity=c.electricity,
        materials=c.materials,
        overhead=c.overhead,
    )


def history_dto(entry: PriceHistory) -> PriceHistoryDTO:
    old, new = entry.old, entry.new
    return PriceHistoryDTO(
        line_code=entry.line_code,
        changed_at=entry.changed_at,
        changed_by=entry.changed_by,
        event=entry.event,
        batch_id=entry.batch_id,
        effective_date=entry.effective_date,
        old_labor=old.labor if old else None,
        old_depreciation=old.depreciation if old else None,
        old_electricity=old.electricity if old else None,
        old_materials=old.materials if old else None,
        old_overhead=old.overhead if old else None,
        old_total=old.total if old else None,
        new_labor=new.labor,
        new_depreciation=new.depreciation,
        new_electricity=new.electricity,
        new_materials=new.materials,
        new_overhead=new.overhead,
        new_total=new.total,
        reason=entry.reason,
    )


def yarn_dto(yarn: Yarn, rate: Decimal | None = None, packaging_name: str = "") -> YarnDTO:
    regular = yarn.regular_line
    total = regular.total_vnd if regular else None
    data = yarn.model_dump(
        exclude={
            "created_at",
            "updated_at",
            "lines",
            "stage_details",
            "max_ck_no",
            "max_pp_no",
            "pending_accounting_code",
        }
    )
    return YarnDTO(
        **data, packaging_name=packaging_name, is_locked=yarn.is_locked, total_vnd=total, usd_per_kg=usd(total, rate)
    )


def summary_dto(yarn: Yarn, rate: Decimal | None = None) -> YarnSummaryDTO:
    regular = yarn.regular_line
    total = regular.total_vnd if regular else None
    reason = yarn.reject_reason if yarn.status == YarnStatus.TU_CHOI else "; ".join(yarn.status_reasons)
    return YarnSummaryDTO(
        yarn_code=yarn.yarn_code,
        factory_code=yarn.factory_code,
        base_code=yarn.base_code,
        revision_no=yarn.revision_no,
        yarn_name=yarn.yarn_name,
        packaging_code=yarn.packaging_code,
        status=yarn.status,
        origin=yarn.origin,
        requested_by=yarn.requested_by,
        requested_at=yarn.requested_at,
        handled_by=yarn.handled_by,
        handled_at=yarn.handled_at,
        reason=reason,
        total_vnd=total,
        usd_per_kg=usd(total, rate),
        is_locked=yarn.is_locked,
        first_priced_at=yarn.first_priced_at,
        loss_group_key=yarn.loss_group_key,
    )


def loss_group_dto(group: LossGroup, used_by: list[str], locked_codes: list[str], parents: list[str]) -> LossGroupDTO:
    return LossGroupDTO(
        factory_code=group.factory_code,
        group_key=group.group_key,
        yarn_group_label=group.yarn_group_label,
        material=group.material,
        technology=group.technology,
        material_tech_key=group.material_tech_key,
        level=group.level,
        losses=group.losses,
        components=[
            ComponentRowDTO(component_group_key=c.component_group_key, ratio=c.ratio) for c in group.components
        ],
        is_locked=bool(locked_codes),
        used_by_codes=used_by,
        used_count=len(used_by),
        locked_codes=locked_codes,
        parent_groups=parents,
        updated_by=group.updated_by,
        updated_at=group.updated_at,
    )


class YarnDtoBuilder(BaseBuilder[YarnDTO]):
    """Convenience wrapper so services can build the main yarn DTO in one call."""

    def __init__(self, yarn: Yarn, rate: Decimal | None = None, packaging_name: str = "") -> None:
        self.yarn, self.rate, self.packaging_name = yarn, rate, packaging_name

    def build(self) -> YarnDTO:
        return yarn_dto(self.yarn, self.rate, self.packaging_name)
