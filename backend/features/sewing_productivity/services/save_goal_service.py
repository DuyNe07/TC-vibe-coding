"""UC-17: save a level; the same factory and effective date replaces the old one."""

from backend.core.base import BaseService
from backend.features.sewing_productivity.business.access_rules import AccessBusiness
from backend.features.sewing_productivity.business.settings_business import SettingsBusiness
from backend.features.sewing_productivity.dto.goal_dto import SaveGoalRequest, SaveGoalResponse
from backend.features.sewing_productivity.models.input_values import GoalInput
from backend.features.sewing_productivity.repositories.settings_repositories import FactoryGoalRepository


class SaveGoalService(BaseService[SaveGoalRequest, SaveGoalResponse]):
    def __init__(self, repository: FactoryGoalRepository | None = None) -> None:
        self.repository = repository or FactoryGoalRepository()
        self.access = AccessBusiness()
        self.settings = SettingsBusiness()

    def execute(self, request: SaveGoalRequest) -> SaveGoalResponse:
        user = self.current_user
        self.access.ensure_valid(user)
        values = GoalInput(**request.model_dump())
        self.settings.ensure_valid(values)
        self.repository.list_seeded()
        goal = self.settings.to_goal(values, self.access.saved_by(user))
        self.repository.save(goal)
        self.logger.info("Saved goal of %s from %s", goal.factory, goal.effective_from)
        return SaveGoalResponse(
            message=f"Đã lưu mục tiêu của {goal.factory.value}, hiệu lực từ {goal.effective_from:%d/%m/%Y}."
        )
