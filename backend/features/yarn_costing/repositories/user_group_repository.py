"""Stored in data/yarn_costing/user_groups.json. Seeds the 5 fixed groups on first read (section 10)."""

from backend.features.yarn_costing.constants import SEED_GROUPS
from backend.features.yarn_costing.models.enums import FactoryCode, GroupCode
from backend.features.yarn_costing.models.user_group import GroupMember, UserGroup
from backend.features.yarn_costing.repositories.safe_json_repository import SafeJsonRepository


def _seed() -> list[UserGroup]:
    return [
        UserGroup(
            code=GroupCode(code),
            name=name,
            factory_code=FactoryCode(factory) if factory else None,
            access_code=access,
            members=[GroupMember(name=m) for m in members],
        )
        for code, name, factory, access, members in SEED_GROUPS
    ]


class UserGroupRepository(SafeJsonRepository[UserGroup]):
    storage_file = "user_groups.json"

    def _read(self) -> dict[str, UserGroup]:
        if not self.file_path.exists():
            with self._lock:
                if not self.file_path.exists():
                    self._save({g.id: g for g in _seed()})
        return super()._read()

    def get_by_code(self, code: str) -> UserGroup | None:
        return self.find_one(lambda g: g.code.value == code)

    def list_ordered(self) -> list[UserGroup]:
        order = [code for code, *_ in SEED_GROUPS]
        return sorted(self.list_all(), key=lambda g: order.index(g.code.value))
