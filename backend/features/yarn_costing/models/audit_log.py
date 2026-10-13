"""4.19 Nhật ký thay đổi (Audit log)."""

from datetime import datetime

from pydantic import Field

from backend.core.base import BaseEntity, utc_now


class AuditLog(BaseEntity):
    at: datetime = Field(default_factory=utc_now)
    username: str
    display_name: str
    action: str
    object_ref: str = ""
    detail: str = ""
    reason: str = ""
