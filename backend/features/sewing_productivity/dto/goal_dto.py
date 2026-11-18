"""UC-16, UC-17: goals and thresholds."""

from datetime import date
from decimal import Decimal

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.sewing_productivity.models.enums import Factory

__all__ = ["Factory", "GoalDTO", "GoalListResponse", "SaveGoalRequest", "SaveGoalResponse"]


class GoalDTO(BaseDTO):
    factory: str
    effective_from: date
    efficiency_target: float
    mo8h_target: float
    efficiency_threshold: float
    mo8h_threshold: float
    updated_by: str


class GoalListResponse(BaseResponseDTO):
    current: list[GoalDTO]
    history: list[GoalDTO]


class SaveGoalRequest(BaseRequestDTO):
    """Every field accepts None, so an empty cell reaches BR-45 and shows its message."""

    factory: Factory | None = None
    effective_from: date | None = None
    efficiency_target: Decimal | None = None
    mo8h_target: Decimal | None = None
    efficiency_threshold: Decimal | None = None
    mo8h_threshold: Decimal | None = None


class SaveGoalResponse(BaseResponseDTO):
    message: str
