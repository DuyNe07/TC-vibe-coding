"""Targets of the master data rules BR-41 (file), BR-45 (sheet permission), BR-50, BR-51, BR-52, BR-60."""

from pydantic import Field

from backend.core.base import BaseValueObject


class ConfigIssues(BaseValueObject):
    details: list[str] = Field(default_factory=list)


class RateVersionCheck(BaseValueObject):
    missing_codes: list[str] = Field(default_factory=list)
    negative: bool = False
    has_date_and_reason: bool = True


class PackagingCheck(BaseValueObject):
    code: str
    factory_code: str
    duplicate: bool = False
    minutes_ok: bool = True


class DefaultPackagingCheck(BaseValueObject):
    default_count: int = 0
    default_active: bool = True


class FileCheck(BaseValueObject):
    extension_ok: bool
    size_ok: bool
    rows_ok: bool = True


class SheetPermissionCheck(BaseValueObject):
    sheet: str
    allowed: bool
