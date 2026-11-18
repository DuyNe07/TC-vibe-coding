"""UC-18: the weekly changeover numbers entered, newest first."""

from backend.core.base import BaseService, EmptyRequest
from backend.features.sewing_productivity.builders.settings_builders import WeeklyChangeoverListBuilder
from backend.features.sewing_productivity.business.access_rules import AccessBusiness
from backend.features.sewing_productivity.dto.weekly_changeover_dto import WeeklyChangeoverListResponse
from backend.features.sewing_productivity.repositories.settings_repositories import WeeklyChangeoverRepository


class ListWeeklyChangeoversService(BaseService[EmptyRequest, WeeklyChangeoverListResponse]):
    def __init__(self, repository: WeeklyChangeoverRepository | None = None) -> None:
        self.repository = repository or WeeklyChangeoverRepository()
        self.access = AccessBusiness()

    def execute(self, request: EmptyRequest) -> WeeklyChangeoverListResponse:
        self.access.ensure_valid(self.current_user)
        items = self.repository.list_all()
        self.logger.info("Listed %s weekly changeovers", len(items))
        return WeeklyChangeoverListBuilder(items).build()
