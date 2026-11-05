"""UC-19: save the weekly numbers; the same factory and period replaces the old one."""

from backend.core.base import BaseService
from backend.features.sewing_productivity.business.access_rules import AccessBusiness
from backend.features.sewing_productivity.business.settings_business import SettingsBusiness
from backend.features.sewing_productivity.dto.weekly_changeover_dto import (
    SaveWeeklyChangeoversRequest,
    SaveWeeklyChangeoversResponse,
)
from backend.features.sewing_productivity.models.input_values import WeeklyChangeoverInput
from backend.features.sewing_productivity.repositories.settings_repositories import WeeklyChangeoverRepository


class SaveWeeklyChangeoversService(BaseService[SaveWeeklyChangeoversRequest, SaveWeeklyChangeoversResponse]):
    def __init__(self, repository: WeeklyChangeoverRepository | None = None) -> None:
        self.repository = repository or WeeklyChangeoverRepository()
        self.access = AccessBusiness()
        self.settings = SettingsBusiness()

    def execute(self, request: SaveWeeklyChangeoversRequest) -> SaveWeeklyChangeoversResponse:
        user = self.current_user
        self.access.ensure_valid(user)
        values = WeeklyChangeoverInput(from_date=request.from_date, to_date=request.to_date, counts=request.counts)
        self.settings.ensure_weekly(values)
        entries = self.settings.to_weekly(values, self.access.saved_by(user))
        self.repository.save_many(entries)
        self.logger.info("Saved %s weekly changeovers %s..%s", len(entries), request.from_date, request.to_date)
        return SaveWeeklyChangeoversResponse(
            message=f"Đã lưu số đổi mã hàng từ {request.from_date:%d/%m/%Y} đến {request.to_date:%d/%m/%Y}."
        )
