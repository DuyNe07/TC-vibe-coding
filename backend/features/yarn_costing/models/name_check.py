"""Tên sợi (bổ sung 2026-11-11): 4.29 từ điển tên chuẩn, 4.30 chữ mới chờ duyệt, 4.31 nhóm sợi / từ khoá của ô ghép tên."""

from datetime import datetime

from pydantic import Field

from backend.core.base import BaseEntity, BaseValueObject, utc_now
from backend.features.yarn_costing.models.enums import (
    FactoryCode,
    NameIssueKind,
    NamePartKind,
    NamePartSource,
    NameWordKind,
    NameWordSource,
    PendingWordStatus,
    YarnStatus,
)


class NameWord(BaseEntity):
    """4.29 one word of the dictionary (standard word or a known misspelling)."""

    word: str
    kind: NameWordKind = NameWordKind.CHUAN
    correct_word: str = ""
    source: NameWordSource = NameWordSource.KHOI_TAO
    created_by: str = ""


class PendingUse(BaseValueObject):
    yarn_code: str
    typed_by: str = ""
    reason: str = ""
    at: datetime = Field(default_factory=utc_now)


class PendingWord(BaseEntity):
    """4.30 an unknown word typed by Sales (BR-104)."""

    word: str
    uses: list[PendingUse] = Field(default_factory=list)
    status: PendingWordStatus = PendingWordStatus.CHO_DUYET
    resolved_word: str = ""
    resolved_by: str = ""
    resolved_at: datetime | None = None

    @property
    def count(self) -> int:
        return len(self.uses)


class NamePart(BaseEntity):
    """4.31 a yarn group or a keyword of the name builder."""

    kind: NamePartKind
    text: str
    fiber_count: int = 1
    sequence: int = 0
    source: NamePartSource = NamePartSource.KHOI_TAO
    reviewed: bool = True


# ---- values computed on the fly ----
class UnknownWord(BaseValueObject):
    word: str
    suggestion: str = ""


class NameCheck(BaseValueObject):
    """BR-100 / BR-101 result for one name."""

    name: str  # upper case, single spaces
    issues: list[NameIssueKind] = Field(default_factory=list)
    unknown: list[UnknownWord] = Field(default_factory=list)
    bad_ratios: list[str] = Field(default_factory=list)  # "60/30" (sum ≠ 100)
    suggested_name: str = ""
    readable: bool = True


class SuspectName(BaseValueObject):
    """UC-65 one row of the "Tên nghi sai" table."""

    factory_code: FactoryCode
    yarn_code: str
    status: YarnStatus
    yarn_name: str
    issues: list[NameIssueKind]
    detail: str = ""
    suggested_name: str = ""


class DuplicateDecision(BaseValueObject):
    """BR-107 one yarn of a duplicate-name group: kept or removed."""

    factory_code: FactoryCode
    upper_name: str
    yarn_code: str
    yarn_name: str
    status: YarnStatus
    keep: bool
    keep_code: str
    accounting_codes: list[str] = Field(default_factory=list)
    reason: str = ""
