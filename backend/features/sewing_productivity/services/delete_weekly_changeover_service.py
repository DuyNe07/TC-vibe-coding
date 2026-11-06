"""UC-20: remove a weekly number from the list (the row stays, flagged)."""

from backend.core.base import BaseService
from backend.features.sewing_productivity.business.access_rules import AccessBusiness
from backend.features.sewing_productivity.dto.weekly_changeover_dto import (
    DeleteWeeklyChangeoverRequest,
    DeleteWeeklyChangeoverResponse,
)
from backend.features.sewing_productivity.repositories.settings_repositories import WeeklyChangeoverRepository


class DeleteWeeklyChangeoverService(BaseService[DeleteWeeklyChangeoverRequest, DeleteWeeklyChangeoverResponse]):
    def __init__(self, repository: WeeklyChangeoverRepository | None = None) -> None:
        self.repository = repository or WeeklyChangeoverRepository()
        self.access = AccessBusiness()

    def execute(self, request: DeleteWeeklyChangeoverRequest) -> DeleteWeeklyChangeoverResponse:
        self.access.ensure_valid(self.current_user)
        self.repository.delete(request.id)
        self.logger.info("Flagged weekly changeover %s as deleted", request.id)
        return DeleteWeeklyChangeoverResponse(message="Đã xoá.")
