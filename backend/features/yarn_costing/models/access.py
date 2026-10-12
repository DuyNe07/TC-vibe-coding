"""Targets of the access rules BR-46 (actor), BR-47 (group permission), BR-48 (factory scope)."""

from backend.core.base import BaseValueObject


class ActorCheck(BaseValueObject):
    group_found: bool
    group_active: bool
    access_code_ok: bool
    member_ok: bool

    @property
    def is_authenticated(self) -> bool:
        return self.group_found and self.group_active and self.access_code_ok and self.member_ok


class PermissionCheck(BaseValueObject):
    group_code: str
    group_name: str
    use_case: str
    allowed: bool


class FactoryScopeCheck(BaseValueObject):
    group_factory: str | None
    target_factory: str | None

    @property
    def in_scope(self) -> bool:
        return self.group_factory is None or self.target_factory is None or self.group_factory == self.target_factory
