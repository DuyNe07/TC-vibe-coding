"""4.1 Nhóm người dùng + 4.2 Thành viên nhóm."""

from pydantic import Field

from backend.core.base import BaseEntity, BaseValueObject
from backend.features.yarn_costing.models.enums import FactoryCode, GroupCode


class GroupMember(BaseValueObject):
    name: str = Field(min_length=1, max_length=100)
    active: bool = True


class UserGroup(BaseEntity):
    code: GroupCode
    name: str = Field(min_length=1, max_length=100)
    factory_code: FactoryCode | None = None
    access_code: str = Field(min_length=4, max_length=20)
    active: bool = True
    members: list[GroupMember] = Field(default_factory=list)

    @property
    def active_member_names(self) -> list[str]:
        return [m.name for m in self.members if m.active]
