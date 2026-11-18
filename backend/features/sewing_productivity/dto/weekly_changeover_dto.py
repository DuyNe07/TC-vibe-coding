"""UC-18, UC-19, UC-20: weekly changeover numbers given by the factories."""

from datetime import date

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO


class WeeklyChangeoverDTO(BaseDTO):
    id: str
    factory: str
    from_date: date
    to_date: date
    changeover_count: int
    updated_by: str


class WeeklyChangeoverListResponse(BaseResponseDTO):
    items: list[WeeklyChangeoverDTO]


class SaveWeeklyChangeoversRequest(BaseRequestDTO):
    """Missing dates and negative or broken counts pass here on purpose: BR-39 shows the message."""

    from_date: date | None = None
    to_date: date | None = None
    counts: dict[str, int | float | None] = {}


class SaveWeeklyChangeoversResponse(BaseResponseDTO):
    message: str


class DeleteWeeklyChangeoverRequest(BaseRequestDTO):
    id: str


class DeleteWeeklyChangeoverResponse(BaseResponseDTO):
    message: str
