"""UC-07 Khai báo quy trình công nghệ (không tính lại giá)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.name_business import group_key_of
from backend.features.yarn_costing.dto.common_dto import SaveCountResponse
from backend.features.yarn_costing.dto.master_dto import SaveProcessRoutesRequest
from backend.features.yarn_costing.models.process_route import ProcessRoute
from backend.features.yarn_costing.repositories.process_route_repository import ProcessRouteRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.stage_repository import StageRepository
from backend.features.yarn_costing.repositories.user_group_repository import UserGroupRepository


class SaveProcessRoutesService(BaseService[SaveProcessRoutesRequest, SaveCountResponse]):
    def __init__(self, repository: ProcessRouteRepository | None = None) -> None:
        self.repository = repository or ProcessRouteRepository()
        self.access = AccessBusiness()
        self.master = MasterBusiness()
        self.costing = CostingBusiness()

    def execute(self, request: SaveProcessRoutesRequest) -> SaveCountResponse:
        a, factory = request.actor, request.factory_code
        group = self.access.verify(
            a.group_code, a.access_code, a.person_name, UserGroupRepository().list_all(), "UC-07", factory.value
        )
        stages = StageRepository().for_factory(factory.value)
        old = {(r.yarn_group, r.technology): r for r in self.repository.for_factory(factory.value)}
        seen: set = set()
        items = []
        for r in request.rows:
            key = group_key_of(r.yarn_group)
            if not key:
                continue
            self.master.require(r.technology is not None, f"Vui lòng chọn công nghệ cho nhóm '{key}'.")
            self.master.require(
                (key, r.technology) not in seen, f"Quy trình cho nhóm '{key}' - {r.technology.value} đã có."
            )  # type: ignore[union-attr]
            self.master.require(
                r.component_count is None or 1 <= r.component_count <= 5, "Số thành phần phải từ 1 đến 5."
            )
            seen.add((key, r.technology))
            item = ProcessRoute(
                factory_code=factory,
                yarn_group=key,
                technology=r.technology,  # type: ignore[arg-type]
                component_count=r.component_count,
                route_text=" ".join(r.route_text.split()),
                route_stages=self.costing.route_stage_codes(r.route_text, stages),
            )
            if (key, r.technology) in old:
                item = item.model_copy(
                    update={"id": old[(key, r.technology)].id, "created_at": old[(key, r.technology)].created_at}
                )
            items.append(item)
        for key, route in old.items():
            if key not in seen:
                self.repository.delete(route.id)
        self.repository.save_many(items)
        names = [f"{i.yarn_group} - {i.technology.value}" for i in items]
        AuditLogRepository().add(
            self.access.audit_entry(group, a.person_name, "UC-07", factory.value, f"{len(items)} quy trình")
        )
        self.logger.info("Process routes %s saved: %s", factory, len(items))
        message = (
            f"Đã lưu quy trình {names[0]}."
            if len(names) == 1
            else f"Đã lưu {len(names)} quy trình công nghệ của xưởng {factory.value}."
        )
        return SaveCountResponse(message=message, saved_count=len(items))
