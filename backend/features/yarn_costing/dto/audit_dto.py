"""DTOs of UC-02 (nhật ký thay đổi)."""

from datetime import date, datetime

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO


class ListAuditLogRequest(BaseRequestDTO):
    date_from: date | None = None
    date_to: date | None = None
    group_code: str | None = None
    keyword: str = ""


class AuditLogDTO(BaseDTO):
    at: datetime
    group_code: str
    person_name: str
    action: str
    object_ref: str = ""
    detail: str = ""
    reason: str = ""


class AuditLogListResponse(BaseResponseDTO):
    items: list[AuditLogDTO] = []
