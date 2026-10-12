"""DTOs of UC-10..UC-14 (nhóm tiêu hao)."""

from datetime import date, datetime
from decimal import Decimal

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.yarn_costing.dto.common_dto import ActorDTO
from backend.features.yarn_costing.models.enums import FactoryCode, LossGroupLevel, Technology


class ComponentRowDTO(BaseDTO):
    component_group_key: str = ""
    ratio: Decimal | None = None


class LossGroupDTO(BaseDTO):
    factory_code: FactoryCode
    group_key: str
    yarn_group_label: str
    material: str = ""
    technology: Technology
    material_tech_key: str = ""
    level: LossGroupLevel
    losses: dict[str, Decimal] = {}
    components: list[ComponentRowDTO] = []
    is_locked: bool = False
    used_by_codes: list[str] = []
    used_count: int = 0
    locked_codes: list[str] = []
    parent_groups: list[str] = []
    updated_by: str = ""
    updated_at: datetime | None = None


class ListLossGroupsRequest(BaseRequestDTO):
    factory_code: FactoryCode
    level: LossGroupLevel | None = None
    keyword: str = ""
    locked_only: bool = False


class LossGroupListResponse(BaseResponseDTO):
    items: list[LossGroupDTO] = []
    stage_codes: list[str] = []


class CreatePrimaryLossGroupRequest(BaseRequestDTO):
    actor: ActorDTO
    factory_code: FactoryCode
    yarn_group_label: str
    material: str = ""
    technology: Technology
    losses: dict[str, Decimal] = {}


class CreateSecondaryLossGroupRequest(BaseRequestDTO):
    actor: ActorDTO
    factory_code: FactoryCode
    yarn_group_label: str
    material: str = ""
    technology: Technology
    components: list[ComponentRowDTO] = []
    save: bool = False


class UpdateLossGroupRequest(BaseRequestDTO):
    actor: ActorDTO
    factory_code: FactoryCode
    group_key: str
    material: str = ""
    technology: Technology
    losses: dict[str, Decimal] | None = None
    components: list[ComponentRowDTO] | None = None
    reason: str = ""
    effective_date: date | None = None


class DeleteLossGroupRequest(BaseRequestDTO):
    actor: ActorDTO
    factory_code: FactoryCode
    group_key: str


class LossGroupSaveResponse(BaseResponseDTO):
    message: str
    group: LossGroupDTO
    recalculated_count: int = 0
    saved: bool = True
