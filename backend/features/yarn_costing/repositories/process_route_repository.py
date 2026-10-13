"""Table yarn_costing__process_route."""

from backend.features.yarn_costing.models.process_route import ProcessRoute
from backend.features.yarn_costing.repositories.yarn_sql_repository import YarnSqlRepository


class ProcessRouteRepository(YarnSqlRepository[ProcessRoute]):
    legacy_file = "process_routes.json"

    def for_factory(self, factory_code: str) -> list[ProcessRoute]:
        return sorted(
            self.find(lambda r: r.factory_code.value == factory_code), key=lambda r: (r.yarn_group, r.technology.value)
        )
