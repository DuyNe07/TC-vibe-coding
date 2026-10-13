"""Roles of the app (= the groups of section 4.1) and the targets of the access rules BR-47, BR-48."""

from typing import Final

from backend.core.base import BaseValueObject
from backend.features.yarn_costing.models.enums import GroupCode

# Role code -> label shown on /admin (the manifest takes its roles from here: one source of truth).
ROLE_LABELS: Final = {
    GroupCode.SALES: "Sales",
    GroupCode.XS1: "Xưởng S1",
    GroupCode.XS4: "Xưởng S4",
    GroupCode.KT: "Kế toán",
    GroupCode.SO: "Phòng SO",
}
# BR-48: factory of a factory role; the other roles work on both factories.
ROLE_FACTORY: Final = {GroupCode.XS1.value: "S1", GroupCode.XS4.value: "S4"}
_FACTORY_ROLES: Final = (GroupCode.XS1.value, GroupCode.XS4.value)
_SO: Final = GroupCode.SO.value
_SALES: Final = GroupCode.SALES.value
_KT: Final = GroupCode.KT.value
INITIAL_IMPORT_USE_CASE: Final = "UC-34-BAN-DAU"  # BR-45: "Chuyển dữ liệu ban đầu" is Phòng SO only
# BR-47: roles allowed per use case besides Phòng SO (SO may run every use case). Unlisted use case = SO only.
USE_CASE_PERMISSIONS: Final = {
    "UC-03": (_SO,),
    "UC-04": (_SO,),
    "UC-05": (_SO,),
    "UC-06": (_SO,),
    "UC-07": (_SO,),
    "UC-08": (_SO,),
    "UC-09": (_SO,),
    "UC-43": (_SO,),
    "UC-45": (_SO, *_FACTORY_ROLES),
    "UC-11": (_SO, *_FACTORY_ROLES),
    "UC-12": (_SO, *_FACTORY_ROLES),
    "UC-13": (_SO, *_FACTORY_ROLES),
    "UC-14": (_SO, *_FACTORY_ROLES),
    "UC-15": (_SO, _SALES),
    "UC-16": (_SO, _SALES),
    "UC-17": (_SO, _SALES),
    "UC-18": (_SO, *_FACTORY_ROLES),
    "UC-20": (_SO, *_FACTORY_ROLES),
    "UC-21": (_SO, *_FACTORY_ROLES),
    "UC-23": (_SO, *_FACTORY_ROLES),
    "UC-24": (_SO, *_FACTORY_ROLES),
    "UC-25": (_SO, *_FACTORY_ROLES),
    "UC-26": (_SO, *_FACTORY_ROLES),
    "UC-28": (_SO, _KT, *_FACTORY_ROLES),
    "UC-34": (_SO, *_FACTORY_ROLES),
    INITIAL_IMPORT_USE_CASE: (_SO,),
}


class PermissionCheck(BaseValueObject):
    use_case: str
    action: str
    allowed: bool


class FactoryScopeCheck(BaseValueObject):
    role_factories: tuple[str | None, ...]  # factory of each role that permits the use case (None = both factories)
    target_factory: str | None

    @property
    def factories_text(self) -> str:
        return ", ".join(sorted({f for f in self.role_factories if f}))

    @property
    def in_scope(self) -> bool:
        return self.target_factory is None or None in self.role_factories or self.target_factory in self.role_factories
