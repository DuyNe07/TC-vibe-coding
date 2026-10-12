"""DTOs of UC-01 (nhóm người dùng) and UC-39 (xác thực người thao tác)."""

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.yarn_costing.dto.common_dto import ActorDTO


class GroupMemberRowDTO(BaseDTO):
    name: str = ""
    active: bool = True


class UserGroupDTO(BaseDTO):
    """Không có mã nội bộ (chỉ nhập lại khi đổi)."""

    code: str
    name: str
    factory_code: str | None = None
    active: bool = True
    members: list[GroupMemberRowDTO] = []
    active_member_names: list[str] = []
    member_count: int = 0


class SaveUserGroupRequest(BaseRequestDTO):
    actor: ActorDTO
    group_code: str
    name: str
    new_access_code: str | None = None
    active: bool = True
    members: list[GroupMemberRowDTO] = []


class UserGroupResponse(BaseResponseDTO):
    message: str = ""
    group: UserGroupDTO


class VerifyActorRequest(BaseRequestDTO):
    actor: ActorDTO


class ActorResponse(BaseResponseDTO):
    message: str
    group_code: str
    group_name: str
    person_name: str
    factory_code: str | None = None
