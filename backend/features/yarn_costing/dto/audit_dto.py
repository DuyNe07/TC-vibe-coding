"""DTOs of UC-02 (nhật ký thay đổi)."""

from datetime import date, datetime

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO


class ListAuditLogRequest(BaseRequestDTO):
    date_from: date | None = None
    date_to: date | None = None
    username: str | None = None
    action: str | None = None
    keyword: str = ""


class AuditLogDTO(BaseDTO):
    at: datetime
    username: str
    display_name: str
    action: str
    object_ref: str = ""
    detail: str = ""
    reason: str = ""


class AuditLogListResponse(BaseResponseDTO):
    items: list[AuditLogDTO] = []
    usernames: list[str] = []  # accounts found in the date range (filter choices)
    actions: list[str] = []  # actions found in the date range (filter choices)
