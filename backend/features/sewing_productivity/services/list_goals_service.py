"""UC-16: the level applied today for each factory, and every saved level."""

from datetime import date

from backend.core.base import BaseService, EmptyRequest
from backend.features.sewing_productivity.builders.settings_builders import GoalListBuilder
from backend.features.sewing_productivity.business.access_rules import AccessBusiness
from backend.features.sewing_productivity.business.productivity_business import ProductivityBusiness
from backend.features.sewing_productivity.constants import ALL_FACTORIES
from backend.features.sewing_productivity.dto.goal_dto import GoalListResponse
from backend.features.sewing_productivity.repositories.settings_repositories import FactoryGoalRepository


class ListGoalsService(BaseService[EmptyRequest, GoalListResponse]):
    def __init__(self, repository: FactoryGoalRepository | None = None) -> None:
        self.repository = repository or FactoryGoalRepository()
        self.access = AccessBusiness()
        self.calc = ProductivityBusiness()

    def execute(self, request: EmptyRequest) -> GoalListResponse:
        self.access.ensure_valid(self.current_user)
        goals = self.repository.list_seeded()
        today = date.today()
        current = [
            goal
            for factory in ALL_FACTORIES
            if (goal := self.calc.goal_on([item for item in goals if item.factory == factory], today)) is not None
        ]
        self.logger.info("Listed %s goals, %s applied today", len(goals), len(current))
        return GoalListBuilder(current, goals).build()
