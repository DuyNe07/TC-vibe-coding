"""Stored in data/yarn_costing/process_routes.json."""

from backend.features.yarn_costing.models.process_route import ProcessRoute
from backend.features.yarn_costing.repositories.safe_json_repository import SafeJsonRepository


class ProcessRouteRepository(SafeJsonRepository[ProcessRoute]):
    storage_file = "process_routes.json"

    def for_factory(self, factory_code: str) -> list[ProcessRoute]:
        return sorted(
            self.find(lambda r: r.factory_code.value == factory_code), key=lambda r: (r.yarn_group, r.technology.value)
        )
